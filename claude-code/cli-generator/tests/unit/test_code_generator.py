"""Unit tests for CodeGenerator."""

import ast
import tempfile
from pathlib import Path

import pytest

from cli_generator.generators.code_generator import CodeGenerator
from cli_generator.models import (
    ArgumentSpec,
    CLISpec,
    CommandSpec,
    OptionSpec,
)


class TestCodeGeneratorInit:
    """Tests for CodeGenerator initialization."""

    def test_creates_instance(self) -> None:
        """CodeGenerator should create successfully."""
        gen = CodeGenerator()
        assert gen is not None


class TestCodeGeneratorGenerate:
    """Tests for CodeGenerator.generate() method."""

    @pytest.fixture
    def generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    @pytest.fixture
    def simple_spec(self) -> CLISpec:
        """Create a simple CLISpec for testing."""
        return CLISpec(
            name="mytool",
            description="A simple test tool",
            commands=[
                CommandSpec(
                    name="greet",
                    description="Greet someone",
                    arguments=[ArgumentSpec(name="name", help="Name to greet")],
                    options=[
                        OptionSpec(
                            name="loud",
                            short="l",
                            type="bool",
                            help="Greet loudly",
                        )
                    ],
                )
            ],
        )

    @pytest.fixture
    def complex_spec(self) -> CLISpec:
        """Create a complex CLISpec with multiple commands and option types."""
        return CLISpec(
            name="fileutil",
            description="File utility tool",
            commands=[
                CommandSpec(
                    name="convert",
                    description="Convert files between formats",
                    arguments=[
                        ArgumentSpec(name="input_file", type="path", help="Input file"),
                    ],
                    options=[
                        OptionSpec(
                            name="output",
                            short="o",
                            type="path",
                            help="Output file",
                        ),
                        OptionSpec(
                            name="format",
                            short="f",
                            type="choice",
                            choices=["json", "yaml", "xml"],
                            default="json",
                            help="Output format",
                        ),
                        OptionSpec(
                            name="indent",
                            short="i",
                            type="int",
                            default=2,
                            help="Indentation level",
                        ),
                    ],
                ),
                CommandSpec(
                    name="validate",
                    description="Validate a file",
                    arguments=[
                        ArgumentSpec(name="file", type="path", help="File to validate"),
                    ],
                    options=[
                        OptionSpec(
                            name="strict",
                            type="bool",
                            help="Enable strict validation",
                        ),
                    ],
                ),
            ],
            global_options=[
                OptionSpec(name="verbose", short="v", type="bool", help="Verbose output"),
            ],
        )

    def test_generate_returns_dict(
        self, generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """generate() should return a dict of file paths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(simple_spec, Path(tmpdir))

        assert isinstance(result, dict)
        assert "cli" in result
        assert "init" in result
        assert "pyproject" in result
        assert "readme" in result

    def test_generate_creates_files(
        self, generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """generate() should create actual files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(simple_spec, Path(tmpdir))

            for path in result.values():
                assert path.exists(), f"{path} should exist"

    def test_generated_cli_is_valid_python(
        self, generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """Generated cli.py should be valid Python syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(simple_spec, Path(tmpdir))
            cli_path = result["cli"]

            # Read and parse the generated code
            code = cli_path.read_text()

            # Should not raise SyntaxError
            ast.parse(code)

    def test_generated_cli_has_click_imports(
        self, generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """Generated cli.py should import click."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(simple_spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "import click" in code

    def test_generated_cli_has_all_commands(
        self, generator: CodeGenerator, complex_spec: CLISpec
    ) -> None:
        """Generated cli.py should have all commands from spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(complex_spec, Path(tmpdir))
            code = result["cli"].read_text()

            # Check that all commands are defined
            assert "def convert(" in code
            assert "def validate(" in code

    def test_generated_cli_has_command_decorators(
        self, generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """Generated cli.py should have @cli.command() decorators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(simple_spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "@cli.command()" in code or '@cli.command("' in code

    def test_generated_cli_has_arguments(
        self, generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """Generated cli.py should have @click.argument decorators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(simple_spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "@click.argument" in code

    def test_generated_cli_has_options(
        self, generator: CodeGenerator, simple_spec: CLISpec
    ) -> None:
        """Generated cli.py should have @click.option decorators."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(simple_spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "@click.option" in code


class TestCodeGeneratorOptionTypes:
    """Tests for correct option type handling."""

    @pytest.fixture
    def generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    def test_string_option_type(self, generator: CodeGenerator) -> None:
        """String options should use str type."""
        spec = CLISpec(
            name="test",
            description="Test",
            commands=[
                CommandSpec(
                    name="cmd",
                    description="Command",
                    options=[OptionSpec(name="name", type="str", help="Name")],
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            code = result["cli"].read_text()

            # String is default, so might not be explicit
            assert "@click.option" in code

    def test_int_option_type(self, generator: CodeGenerator) -> None:
        """Int options should use int type."""
        spec = CLISpec(
            name="test",
            description="Test",
            commands=[
                CommandSpec(
                    name="cmd",
                    description="Command",
                    options=[OptionSpec(name="count", type="int", help="Count")],
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "type=int" in code

    def test_float_option_type(self, generator: CodeGenerator) -> None:
        """Float options should use float type."""
        spec = CLISpec(
            name="test",
            description="Test",
            commands=[
                CommandSpec(
                    name="cmd",
                    description="Command",
                    options=[OptionSpec(name="rate", type="float", help="Rate")],
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "type=float" in code

    def test_bool_option_type(self, generator: CodeGenerator) -> None:
        """Bool options should use is_flag=True."""
        spec = CLISpec(
            name="test",
            description="Test",
            commands=[
                CommandSpec(
                    name="cmd",
                    description="Command",
                    options=[OptionSpec(name="verbose", type="bool", help="Verbose")],
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "is_flag=True" in code

    def test_path_option_type(self, generator: CodeGenerator) -> None:
        """Path options should use click.Path type."""
        spec = CLISpec(
            name="test",
            description="Test",
            commands=[
                CommandSpec(
                    name="cmd",
                    description="Command",
                    options=[OptionSpec(name="file", type="path", help="File path")],
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "click.Path" in code

    def test_choice_option_type(self, generator: CodeGenerator) -> None:
        """Choice options should use click.Choice type."""
        spec = CLISpec(
            name="test",
            description="Test",
            commands=[
                CommandSpec(
                    name="cmd",
                    description="Command",
                    options=[
                        OptionSpec(
                            name="format",
                            type="choice",
                            choices=["json", "yaml"],
                            help="Format",
                        )
                    ],
                )
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            code = result["cli"].read_text()

            assert "click.Choice" in code
            assert "json" in code
            assert "yaml" in code


class TestCodeGeneratorPyproject:
    """Tests for pyproject.toml generation."""

    @pytest.fixture
    def generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    def test_pyproject_has_name(self, generator: CodeGenerator) -> None:
        """Generated pyproject.toml should have correct name."""
        spec = CLISpec(name="mytool", description="My tool")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            content = result["pyproject"].read_text()

            assert 'name = "mytool"' in content

    def test_pyproject_has_description(self, generator: CodeGenerator) -> None:
        """Generated pyproject.toml should have description."""
        spec = CLISpec(name="mytool", description="My awesome tool")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            content = result["pyproject"].read_text()

            assert "My awesome tool" in content

    def test_pyproject_has_click_dependency(self, generator: CodeGenerator) -> None:
        """Generated pyproject.toml should include click dependency."""
        spec = CLISpec(name="mytool", description="My tool")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            content = result["pyproject"].read_text()

            assert "click" in content

    def test_pyproject_has_entry_point(self, generator: CodeGenerator) -> None:
        """Generated pyproject.toml should have console script entry point."""
        spec = CLISpec(name="mytool", description="My tool")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            content = result["pyproject"].read_text()

            assert "[project.scripts]" in content
            assert "mytool" in content


class TestCodeGeneratorReadme:
    """Tests for README.md generation."""

    @pytest.fixture
    def generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    def test_readme_has_name(self, generator: CodeGenerator) -> None:
        """Generated README.md should have CLI name."""
        spec = CLISpec(name="mytool", description="My tool")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            content = result["readme"].read_text()

            assert "mytool" in content

    def test_readme_has_description(self, generator: CodeGenerator) -> None:
        """Generated README.md should have description."""
        spec = CLISpec(name="mytool", description="My awesome tool")

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            content = result["readme"].read_text()

            assert "My awesome tool" in content

    def test_readme_has_commands(self, generator: CodeGenerator) -> None:
        """Generated README.md should document commands."""
        spec = CLISpec(
            name="mytool",
            description="My tool",
            commands=[
                CommandSpec(name="convert", description="Convert files"),
                CommandSpec(name="validate", description="Validate files"),
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            content = result["readme"].read_text()

            assert "convert" in content
            assert "validate" in content


class TestCodeGeneratorNoCommands:
    """Tests for CLISpec with no commands (single-command CLI)."""

    @pytest.fixture
    def generator(self) -> CodeGenerator:
        """Create a CodeGenerator instance."""
        return CodeGenerator()

    def test_cli_with_no_commands_is_valid(self, generator: CodeGenerator) -> None:
        """CLI with no commands should still generate valid Python."""
        spec = CLISpec(
            name="simple",
            description="A simple tool with no subcommands",
            global_options=[
                OptionSpec(name="verbose", short="v", type="bool", help="Verbose")
            ],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            result = generator.generate(spec, Path(tmpdir))
            code = result["cli"].read_text()

            # Should be valid Python
            ast.parse(code)
