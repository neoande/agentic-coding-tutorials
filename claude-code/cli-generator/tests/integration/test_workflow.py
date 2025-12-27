"""Integration tests for the complete CLI generator workflow.

These tests verify the full pipeline:
1. Generate a spec from natural language description
2. Generate code from the spec
3. Verify generated code compiles
4. Optionally install and test --help (slow tests)
"""

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from pydantic_ai.models.test import TestModel

from cli_generator.generators.code_generator import CodeGenerator
from cli_generator.generators.spec_generator import SpecGenerator
from cli_generator.models import (
    ArgumentSpec,
    CLISpec,
    CommandSpec,
    OptionSpec,
)


class TestWorkflowWithMockedLLM:
    """Integration tests using mocked LLM responses for fast execution."""

    @pytest.fixture
    def spec_generator(self) -> SpecGenerator:
        """Create a SpecGenerator instance."""
        return SpecGenerator()

    @pytest.fixture
    def code_generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    async def test_full_workflow_mocked(
        self, spec_generator: SpecGenerator, code_generator: CodeGenerator
    ) -> None:
        """Test complete workflow: description -> spec -> code -> compile check."""
        # Step 1: Generate spec from description (using mocked LLM)
        with spec_generator.agent.override(model=TestModel()):
            spec = await spec_generator.generate(
                "A CLI tool that converts images between formats like PNG, JPEG, and WebP"
            )

        assert isinstance(spec, CLISpec)
        assert spec.name
        assert spec.description

        # Step 2: Generate code from spec
        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(spec, Path(tmpdir))

            # Step 3: Verify all expected files were created
            assert "cli" in result
            assert "init" in result
            assert "pyproject" in result
            assert "readme" in result

            for file_path in result.values():
                assert file_path.exists(), f"{file_path} should exist"

            # Step 4: Verify generated Python code compiles
            cli_code = result["cli"].read_text()
            ast.parse(cli_code)  # Raises SyntaxError if invalid

            # Verify init.py compiles
            init_code = result["init"].read_text()
            ast.parse(init_code)

    async def test_workflow_with_complex_cli(
        self, spec_generator: SpecGenerator, code_generator: CodeGenerator
    ) -> None:
        """Test workflow with a more complex CLI description."""
        with spec_generator.agent.override(model=TestModel()):
            spec = await spec_generator.generate(
                "A file manager CLI with commands to list, copy, move, and delete files. "
                "It should support recursive operations and have verbose output mode."
            )

        assert isinstance(spec, CLISpec)

        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(spec, Path(tmpdir))

            # Verify code compiles
            cli_code = result["cli"].read_text()
            ast.parse(cli_code)

    async def test_workflow_add_command_to_existing(
        self, spec_generator: SpecGenerator, code_generator: CodeGenerator
    ) -> None:
        """Test adding a command to an existing spec and regenerating code."""
        # Start with a basic spec
        base_spec = CLISpec(
            name="mytool",
            description="A utility tool",
            commands=[
                CommandSpec(name="info", description="Show information"),
            ],
        )

        # Add a new command using LLM
        with spec_generator.command_agent.override(model=TestModel()):
            updated_spec = await spec_generator.add_command(
                base_spec, "Add a command to export data to JSON or CSV format"
            )

        # Should have 2 commands now
        assert len(updated_spec.commands) == 2

        # Generate code from updated spec
        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(updated_spec, Path(tmpdir))

            cli_code = result["cli"].read_text()
            ast.parse(cli_code)


class TestWorkflowWithFixedSpec:
    """Integration tests using a pre-defined spec to test code generation reliability."""

    @pytest.fixture
    def code_generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    @pytest.fixture
    def realistic_spec(self) -> CLISpec:
        """Create a realistic CLISpec for thorough testing."""
        return CLISpec(
            name="imgconvert",
            description="Convert images between formats",
            commands=[
                CommandSpec(
                    name="convert",
                    description="Convert an image to a different format",
                    arguments=[
                        ArgumentSpec(
                            name="input_file",
                            type="path",
                            required=True,
                            help="Input image file to convert",
                        ),
                    ],
                    options=[
                        OptionSpec(
                            name="output",
                            short="o",
                            type="path",
                            required=False,
                            help="Output file path",
                        ),
                        OptionSpec(
                            name="format",
                            short="f",
                            type="choice",
                            choices=["png", "jpeg", "webp", "gif"],
                            default="png",
                            help="Output format",
                        ),
                        OptionSpec(
                            name="quality",
                            short="q",
                            type="int",
                            default=85,
                            help="Output quality (1-100)",
                        ),
                    ],
                    examples=[
                        "imgconvert convert photo.jpg -f png",
                        "imgconvert convert photo.jpg -o output.png -q 90",
                    ],
                ),
                CommandSpec(
                    name="info",
                    description="Display information about an image",
                    arguments=[
                        ArgumentSpec(
                            name="file",
                            type="path",
                            required=True,
                            help="Image file to inspect",
                        ),
                    ],
                    options=[
                        OptionSpec(
                            name="verbose",
                            short="v",
                            type="bool",
                            help="Show detailed information",
                        ),
                    ],
                ),
            ],
            global_options=[
                OptionSpec(
                    name="quiet",
                    short="q",
                    type="bool",
                    help="Suppress output",
                ),
            ],
            python_version="3.11",
            dependencies=["pillow>=10.0"],
        )

    def test_generate_and_compile_realistic_spec(
        self, code_generator: CodeGenerator, realistic_spec: CLISpec
    ) -> None:
        """Test that a realistic spec generates valid, compilable code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(realistic_spec, Path(tmpdir))

            # Verify cli.py compiles and has expected content
            cli_code = result["cli"].read_text()
            ast.parse(cli_code)

            # Verify expected commands are present
            assert "def convert(" in cli_code
            assert "def info(" in cli_code

            # Verify Click decorators
            assert "@click.option" in cli_code
            assert "@click.argument" in cli_code
            assert "click.Choice" in cli_code  # For format option

            # Verify pyproject has dependencies
            pyproject = result["pyproject"].read_text()
            assert "pillow" in pyproject
            assert "click" in pyproject

    def test_generate_creates_complete_package_structure(
        self, code_generator: CodeGenerator, realistic_spec: CLISpec
    ) -> None:
        """Test that generated code creates a complete, installable package."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(realistic_spec, Path(tmpdir))

            output_dir = Path(tmpdir)
            package_dir = output_dir / realistic_spec.name

            # Check package structure
            assert package_dir.exists()
            assert (package_dir / "cli.py").exists()
            assert (package_dir / "__init__.py").exists()
            assert (output_dir / "pyproject.toml").exists()
            assert (output_dir / "README.md").exists()


@pytest.mark.slow
class TestWorkflowWithRealLLM:
    """Integration tests using real LLM - marked slow, requires API key."""

    @pytest.fixture
    def spec_generator(self) -> SpecGenerator:
        """Create a SpecGenerator with real model."""
        return SpecGenerator(model="openai:gpt-4o-mini")

    @pytest.fixture
    def code_generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    )
    async def test_real_llm_generates_valid_spec(
        self, spec_generator: SpecGenerator, code_generator: CodeGenerator
    ) -> None:
        """Test that real LLM generates a valid, usable spec."""
        spec = await spec_generator.generate(
            "A simple CLI that counts words in text files. "
            "It should have a count command that takes a filename as argument "
            "and options for verbose output and counting lines instead of words."
        )

        # Verify spec is valid
        assert isinstance(spec, CLISpec)
        assert spec.name
        assert spec.description
        assert len(spec.commands) >= 1

        # Generate code and verify it compiles
        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(spec, Path(tmpdir))

            cli_code = result["cli"].read_text()
            ast.parse(cli_code)

    @pytest.mark.skipif(
        not os.environ.get("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set",
    )
    async def test_real_llm_complex_cli(
        self, spec_generator: SpecGenerator, code_generator: CodeGenerator
    ) -> None:
        """Test real LLM with a more complex CLI request."""
        spec = await spec_generator.generate(
            "A JSON utility CLI with commands to: "
            "1. validate - check if a file is valid JSON "
            "2. format - pretty print JSON with configurable indentation "
            "3. query - extract values using JSONPath expressions"
        )

        assert isinstance(spec, CLISpec)
        assert len(spec.commands) >= 1

        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(spec, Path(tmpdir))

            cli_code = result["cli"].read_text()
            ast.parse(cli_code)


@pytest.mark.slow
class TestWorkflowInstallAndRun:
    """Integration tests that actually install and run the generated CLI."""

    @pytest.fixture
    def code_generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    @pytest.fixture
    def simple_spec(self) -> CLISpec:
        """Create a simple, minimal spec for installation testing."""
        return CLISpec(
            name="testcli",
            description="A simple test CLI",
            commands=[
                CommandSpec(
                    name="hello",
                    description="Print a greeting",
                    arguments=[
                        ArgumentSpec(name="name", type="str", help="Name to greet"),
                    ],
                    options=[
                        OptionSpec(
                            name="loud",
                            short="l",
                            type="bool",
                            help="Greet loudly",
                        ),
                    ],
                ),
            ],
        )

    def test_generated_cli_installs_and_shows_help(
        self, code_generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """Test that generated CLI can be installed and shows --help."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(simple_spec, Path(tmpdir))

            # Create a virtual environment and install
            venv_dir = Path(tmpdir) / ".venv"
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
            )

            # Get the pip path in the venv
            if sys.platform == "win32":
                pip_path = venv_dir / "Scripts" / "pip"
                python_path = venv_dir / "Scripts" / "python"
            else:
                pip_path = venv_dir / "bin" / "pip"
                python_path = venv_dir / "bin" / "python"

            # Install the generated package
            install_result = subprocess.run(
                [str(pip_path), "install", "-e", str(tmpdir)],
                capture_output=True,
                text=True,
            )

            if install_result.returncode != 0:
                pytest.fail(
                    f"Failed to install generated CLI: {install_result.stderr}"
                )

            # Test --help on main CLI
            help_result = subprocess.run(
                [str(python_path), "-m", simple_spec.name + ".cli", "--help"],
                capture_output=True,
                text=True,
            )

            assert help_result.returncode == 0
            assert simple_spec.description in help_result.stdout or "--help" in help_result.stdout

            # Test --help on subcommand
            cmd_help_result = subprocess.run(
                [str(python_path), "-m", simple_spec.name + ".cli", "hello", "--help"],
                capture_output=True,
                text=True,
            )

            assert cmd_help_result.returncode == 0
            assert "name" in cmd_help_result.stdout.lower() or "NAME" in cmd_help_result.stdout

    def test_generated_cli_version_flag(
        self, code_generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """Test that generated CLI has working --version flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(simple_spec, Path(tmpdir))

            venv_dir = Path(tmpdir) / ".venv"
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                check=True,
                capture_output=True,
            )

            if sys.platform == "win32":
                pip_path = venv_dir / "Scripts" / "pip"
                python_path = venv_dir / "Scripts" / "python"
            else:
                pip_path = venv_dir / "bin" / "pip"
                python_path = venv_dir / "bin" / "python"

            subprocess.run(
                [str(pip_path), "install", "-e", str(tmpdir)],
                capture_output=True,
                text=True,
                check=True,
            )

            # Test --version
            version_result = subprocess.run(
                [str(python_path), "-m", simple_spec.name + ".cli", "--version"],
                capture_output=True,
                text=True,
            )

            assert version_result.returncode == 0
            assert "0.1.0" in version_result.stdout


class TestWorkflowErrorHandling:
    """Tests for error handling in the workflow."""

    @pytest.fixture
    def spec_generator(self) -> SpecGenerator:
        """Create a SpecGenerator instance."""
        return SpecGenerator()

    @pytest.fixture
    def code_generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    async def test_empty_description_raises_error(
        self, spec_generator: SpecGenerator
    ) -> None:
        """Test that empty description raises ValueError."""
        with pytest.raises(ValueError, match="description"):
            await spec_generator.generate("")

    async def test_whitespace_description_raises_error(
        self, spec_generator: SpecGenerator
    ) -> None:
        """Test that whitespace-only description raises ValueError."""
        with pytest.raises(ValueError, match="description"):
            await spec_generator.generate("   \n\t  ")

    def test_invalid_output_directory(
        self, code_generator: CodeGenerator
    ) -> None:
        """Test handling of invalid output directory."""
        spec = CLISpec(name="test", description="Test")

        # Non-existent parent directory should be created
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = Path(tmpdir) / "deep" / "nested" / "path"
            result = code_generator.generate(spec, nested_path)

            assert nested_path.exists()
            assert result["cli"].exists()


class TestWorkflowEdgeCases:
    """Tests for edge cases in the workflow."""

    @pytest.fixture
    def code_generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    def test_spec_with_no_commands(self, code_generator: CodeGenerator) -> None:
        """Test generating CLI with no subcommands (single-purpose CLI)."""
        spec = CLISpec(
            name="simple",
            description="A simple single-purpose tool",
            global_options=[
                OptionSpec(name="verbose", short="v", type="bool", help="Verbose"),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(spec, Path(tmpdir))

            cli_code = result["cli"].read_text()
            ast.parse(cli_code)

    def test_spec_with_special_characters_in_description(
        self, code_generator: CodeGenerator
    ) -> None:
        """Test that special characters in description are handled."""
        spec = CLISpec(
            name="quotetool",
            description='A tool for handling "quoted" strings & special <chars>',
            commands=[
                CommandSpec(
                    name="process",
                    description='Process "quoted" input with <special> chars & symbols',
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(spec, Path(tmpdir))

            cli_code = result["cli"].read_text()
            ast.parse(cli_code)

    def test_spec_with_many_commands(self, code_generator: CodeGenerator) -> None:
        """Test generating CLI with many commands."""
        commands = [
            CommandSpec(name=f"cmd{i}", description=f"Command number {i}")
            for i in range(10)
        ]

        spec = CLISpec(
            name="manycmds",
            description="A tool with many commands",
            commands=commands,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(spec, Path(tmpdir))

            cli_code = result["cli"].read_text()
            ast.parse(cli_code)

            # All commands should be in the code
            for i in range(10):
                assert f"def cmd{i}(" in cli_code

    def test_spec_with_all_option_types(self, code_generator: CodeGenerator) -> None:
        """Test generating CLI with all supported option types."""
        spec = CLISpec(
            name="alltypes",
            description="CLI with all option types",
            commands=[
                CommandSpec(
                    name="demo",
                    description="Demonstrate all types",
                    options=[
                        OptionSpec(name="text", type="str", help="String option"),
                        OptionSpec(name="number", type="int", help="Integer option"),
                        OptionSpec(name="rate", type="float", help="Float option"),
                        OptionSpec(name="flag", type="bool", help="Boolean flag"),
                        OptionSpec(name="file", type="path", help="Path option"),
                        OptionSpec(
                            name="choice",
                            type="choice",
                            choices=["a", "b", "c"],
                            help="Choice option",
                        ),
                    ],
                ),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = code_generator.generate(spec, Path(tmpdir))

            cli_code = result["cli"].read_text()
            ast.parse(cli_code)

            # Verify type handling
            assert "type=int" in cli_code
            assert "type=float" in cli_code
            assert "is_flag=True" in cli_code
            assert "click.Path" in cli_code
            assert "click.Choice" in cli_code
