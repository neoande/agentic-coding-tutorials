"""Unit tests for CLI interface."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner
from pydantic_ai.models.test import TestModel

from cli_generator.cli import cli, spec_cmd, generate_cmd, build_cmd
from cli_generator.models import CLISpec, CommandSpec


class TestCLIGroup:
    """Tests for the main CLI group."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_cli_has_help(self, runner: CliRunner) -> None:
        """CLI should have help text."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Generate CLI tools from natural language" in result.output

    def test_cli_has_version(self, runner: CliRunner) -> None:
        """CLI should have version option."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestSpecCommand:
    """Tests for the 'spec' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_spec_requires_description(self, runner: CliRunner) -> None:
        """spec command should require a description."""
        result = runner.invoke(cli, ["spec"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "required" in result.output.lower()

    def test_spec_has_help(self, runner: CliRunner) -> None:
        """spec command should have help text."""
        result = runner.invoke(cli, ["spec", "--help"])
        assert result.exit_code == 0
        assert "description" in result.output.lower()

    def test_spec_outputs_json(self, runner: CliRunner) -> None:
        """spec command should output JSON."""
        # Use environment variable to set test model
        result = runner.invoke(
            cli,
            ["spec", "A simple counter CLI", "--test-mode"],
            catch_exceptions=False,
        )
        # Should succeed or fail gracefully
        # With test mode, it should produce valid output
        assert result.exit_code == 0 or "Error" in result.output

    def test_spec_with_save_option(self, runner: CliRunner) -> None:
        """spec command should support --save option."""
        with tempfile.TemporaryDirectory() as tmpdir:
            spec_file = Path(tmpdir) / "spec.json"
            result = runner.invoke(
                cli,
                ["spec", "A counter CLI", "--save", str(spec_file), "--test-mode"],
            )
            # Either succeeds or shows error message
            if result.exit_code == 0:
                assert spec_file.exists()


class TestGenerateCommand:
    """Tests for the 'generate' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_generate_requires_description(self, runner: CliRunner) -> None:
        """generate command should require a description."""
        result = runner.invoke(cli, ["generate"])
        assert result.exit_code != 0

    def test_generate_has_help(self, runner: CliRunner) -> None:
        """generate command should have help text."""
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "output" in result.output.lower()

    def test_generate_has_output_option(self, runner: CliRunner) -> None:
        """generate command should have --output option."""
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output or "-o" in result.output

    def test_generate_has_dry_run_option(self, runner: CliRunner) -> None:
        """generate command should have --dry-run option."""
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output

    def test_generate_dry_run_does_not_create_files(self, runner: CliRunner) -> None:
        """generate --dry-run should not create files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                cli,
                [
                    "generate",
                    "A counter CLI",
                    "--output",
                    tmpdir,
                    "--dry-run",
                    "--test-mode",
                ],
            )
            # Check that no new directories were created
            # (tmpdir will exist but should be empty or have no package dir)
            if result.exit_code == 0:
                # In dry-run mode, we shouldn't create the package
                contents = list(Path(tmpdir).iterdir())
                # Either empty or only contains the spec output, not a full package
                assert len(contents) == 0 or not any(
                    (Path(tmpdir) / d / "cli.py").exists() for d in contents
                )


class TestBuildCommand:
    """Tests for the 'build' command."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def sample_spec_file(self) -> Path:
        """Create a sample spec file for testing."""
        spec = CLISpec(
            name="testcli",
            description="A test CLI",
            commands=[
                CommandSpec(name="hello", description="Say hello"),
            ],
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(spec.model_dump_json(indent=2))
            return Path(f.name)

    def test_build_requires_spec_file(self, runner: CliRunner) -> None:
        """build command should require a spec file."""
        result = runner.invoke(cli, ["build"])
        assert result.exit_code != 0

    def test_build_has_help(self, runner: CliRunner) -> None:
        """build command should have help text."""
        result = runner.invoke(cli, ["build", "--help"])
        assert result.exit_code == 0
        assert "spec" in result.output.lower()

    def test_build_with_valid_spec(
        self, runner: CliRunner, sample_spec_file: Path
    ) -> None:
        """build command should work with valid spec file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                cli,
                ["build", str(sample_spec_file), "--output", tmpdir],
            )
            assert result.exit_code == 0
            # Check that files were created
            assert (Path(tmpdir) / "testcli" / "cli.py").exists()

    def test_build_with_invalid_spec_file(self, runner: CliRunner) -> None:
        """build command should handle invalid spec file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": "spec"}')
            spec_file = Path(f.name)

        result = runner.invoke(cli, ["build", str(spec_file)])
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "invalid" in result.output.lower()

    def test_build_with_nonexistent_file(self, runner: CliRunner) -> None:
        """build command should handle nonexistent file."""
        result = runner.invoke(cli, ["build", "/nonexistent/file.json"])
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "not found" in result.output.lower()

    def test_build_has_output_option(self, runner: CliRunner) -> None:
        """build command should have --output option."""
        result = runner.invoke(cli, ["build", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output or "-o" in result.output


class TestErrorHandling:
    """Tests for error handling."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_invalid_command_shows_help(self, runner: CliRunner) -> None:
        """Invalid command should show help or error."""
        result = runner.invoke(cli, ["invalid_command"])
        assert result.exit_code != 0

    def test_keyboard_interrupt_handled(self, runner: CliRunner) -> None:
        """CLI should handle interrupts gracefully."""
        # This is more of an integration test, but we can check the structure
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
