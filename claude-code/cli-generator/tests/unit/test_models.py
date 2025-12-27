"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from cli_generator.models import ArgumentSpec, CLISpec, CommandSpec, OptionSpec


class TestArgumentSpec:
    """Tests for ArgumentSpec model."""

    def test_create_minimal_argument(self) -> None:
        """Create argument with only required fields."""
        arg = ArgumentSpec(name="filename")
        assert arg.name == "filename"
        assert arg.type == "str"
        assert arg.required is True
        assert arg.help == ""

    def test_create_full_argument(self) -> None:
        """Create argument with all fields."""
        arg = ArgumentSpec(
            name="count",
            type="int",
            required=False,
            help="Number of items to process",
        )
        assert arg.name == "count"
        assert arg.type == "int"
        assert arg.required is False
        assert arg.help == "Number of items to process"

    def test_argument_name_required(self) -> None:
        """Argument must have a name."""
        with pytest.raises(ValidationError):
            ArgumentSpec()  # type: ignore[call-arg]


class TestOptionSpec:
    """Tests for OptionSpec model."""

    def test_create_minimal_option(self) -> None:
        """Create option with only required fields."""
        opt = OptionSpec(name="output")
        assert opt.name == "output"
        assert opt.short is None
        assert opt.type == "str"
        assert opt.required is False
        assert opt.default is None
        assert opt.help == ""
        assert opt.choices is None

    def test_create_full_option(self) -> None:
        """Create option with all fields."""
        opt = OptionSpec(
            name="format",
            short="f",
            type="choice",
            required=True,
            default="json",
            help="Output format",
            choices=["json", "yaml", "xml"],
        )
        assert opt.name == "format"
        assert opt.short == "f"
        assert opt.type == "choice"
        assert opt.required is True
        assert opt.default == "json"
        assert opt.help == "Output format"
        assert opt.choices == ["json", "yaml", "xml"]

    def test_short_option_single_character(self) -> None:
        """Short option must be single character."""
        # Valid single character
        opt = OptionSpec(name="output", short="o")
        assert opt.short == "o"

    def test_short_option_multiple_characters_fails(self) -> None:
        """Short option with multiple characters should fail validation."""
        with pytest.raises(ValidationError) as exc_info:
            OptionSpec(name="output", short="out")
        assert "single character" in str(exc_info.value).lower()

    def test_short_option_empty_string_becomes_none(self) -> None:
        """Short option as empty string should be converted to None."""
        opt = OptionSpec(name="output", short="")
        assert opt.short is None

    def test_short_option_none_is_valid(self) -> None:
        """Short option can be None (no short form)."""
        opt = OptionSpec(name="verbose", short=None)
        assert opt.short is None

    def test_option_name_strips_dashes(self) -> None:
        """Option name should have leading dashes stripped."""
        opt = OptionSpec(name="--output", short="-o")
        assert opt.name == "output"
        assert opt.short == "o"

    def test_option_name_strips_double_dashes(self) -> None:
        """Option name should have double dashes stripped."""
        opt = OptionSpec(name="--output-dir")
        assert opt.name == "output-dir"

    def test_choice_type_requires_choices_list(self) -> None:
        """Option with type='choice' must have choices list."""
        with pytest.raises(ValidationError) as exc_info:
            OptionSpec(name="format", type="choice")
        assert "choice" in str(exc_info.value).lower()

    def test_choice_type_with_none_choices_fails(self) -> None:
        """Option with type='choice' and choices=None should fail."""
        with pytest.raises(ValidationError) as exc_info:
            OptionSpec(name="format", type="choice", choices=None)
        assert "choice" in str(exc_info.value).lower()

    def test_choice_type_with_empty_choices_fails(self) -> None:
        """Option with type='choice' and empty choices should fail."""
        with pytest.raises(ValidationError) as exc_info:
            OptionSpec(name="format", type="choice", choices=[])
        assert "choice" in str(exc_info.value).lower()

    def test_choice_type_with_choices_is_valid(self) -> None:
        """Option with type='choice' and valid choices should work."""
        opt = OptionSpec(name="format", type="choice", choices=["json", "yaml", "xml"])
        assert opt.type == "choice"
        assert opt.choices == ["json", "yaml", "xml"]

    def test_non_choice_type_with_choices_is_valid(self) -> None:
        """Non-choice type can have choices list (ignored but allowed)."""
        opt = OptionSpec(name="output", type="str", choices=["a", "b"])
        assert opt.type == "str"
        assert opt.choices == ["a", "b"]


class TestCommandSpec:
    """Tests for CommandSpec model."""

    def test_create_minimal_command(self) -> None:
        """Create command with only required fields."""
        cmd = CommandSpec(name="build", description="Build the project")
        assert cmd.name == "build"
        assert cmd.description == "Build the project"
        assert cmd.arguments == []
        assert cmd.options == []
        assert cmd.examples == []

    def test_create_full_command(self) -> None:
        """Create command with all fields."""
        cmd = CommandSpec(
            name="convert",
            description="Convert files",
            arguments=[ArgumentSpec(name="input")],
            options=[OptionSpec(name="output", short="o")],
            examples=["convert file.txt -o output.txt"],
        )
        assert cmd.name == "convert"
        assert len(cmd.arguments) == 1
        assert len(cmd.options) == 1
        assert len(cmd.examples) == 1

    def test_no_duplicate_option_names(self) -> None:
        """Command cannot have duplicate option names."""
        with pytest.raises(ValidationError) as exc_info:
            CommandSpec(
                name="test",
                description="Test command",
                options=[
                    OptionSpec(name="output", short="o"),
                    OptionSpec(name="output", short="u"),  # Duplicate name
                ],
            )
        assert "duplicate" in str(exc_info.value).lower()

    def test_no_duplicate_option_short_names(self) -> None:
        """Command cannot have duplicate short option names."""
        with pytest.raises(ValidationError) as exc_info:
            CommandSpec(
                name="test",
                description="Test command",
                options=[
                    OptionSpec(name="output", short="o"),
                    OptionSpec(name="outfile", short="o"),  # Duplicate short
                ],
            )
        assert "duplicate" in str(exc_info.value).lower()

    def test_no_duplicate_argument_names(self) -> None:
        """Command cannot have duplicate argument names."""
        with pytest.raises(ValidationError) as exc_info:
            CommandSpec(
                name="test",
                description="Test command",
                arguments=[
                    ArgumentSpec(name="input"),
                    ArgumentSpec(name="input"),  # Duplicate
                ],
            )
        assert "duplicate" in str(exc_info.value).lower()

    def test_unique_options_are_valid(self) -> None:
        """Command with unique options should be valid."""
        cmd = CommandSpec(
            name="test",
            description="Test command",
            options=[
                OptionSpec(name="output", short="o"),
                OptionSpec(name="verbose", short="v"),
                OptionSpec(name="quiet"),  # No short form
            ],
        )
        assert len(cmd.options) == 3


class TestCLISpec:
    """Tests for CLISpec model."""

    def test_create_minimal_cli(self) -> None:
        """Create CLI with only required fields."""
        cli = CLISpec(name="mytool", description="My awesome tool")
        assert cli.name == "mytool"
        assert cli.description == "My awesome tool"
        assert cli.commands == []
        assert cli.global_options == []
        assert cli.python_version == "3.11"
        assert cli.dependencies == []

    def test_create_full_cli(self) -> None:
        """Create CLI with all fields."""
        cli = CLISpec(
            name="imgconvert",
            description="Image converter",
            commands=[
                CommandSpec(name="convert", description="Convert images"),
                CommandSpec(name="resize", description="Resize images"),
            ],
            global_options=[OptionSpec(name="verbose", short="v")],
            python_version="3.12",
            dependencies=["pillow", "click"],
        )
        assert cli.name == "imgconvert"
        assert len(cli.commands) == 2
        assert len(cli.global_options) == 1

    def test_valid_python_package_name(self) -> None:
        """CLI name must be valid Python package name."""
        # Valid names
        CLISpec(name="mytool", description="Test")
        CLISpec(name="my_tool", description="Test")
        CLISpec(name="mytool123", description="Test")
        CLISpec(name="_private", description="Test")

    def test_invalid_package_name_with_hyphen(self) -> None:
        """CLI name with hyphen is invalid for Python package."""
        with pytest.raises(ValidationError) as exc_info:
            CLISpec(name="my-tool", description="Test")
        assert "valid python package name" in str(exc_info.value).lower()

    def test_invalid_package_name_starts_with_number(self) -> None:
        """CLI name starting with number is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            CLISpec(name="123tool", description="Test")
        assert "valid python package name" in str(exc_info.value).lower()

    def test_invalid_package_name_with_spaces(self) -> None:
        """CLI name with spaces is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            CLISpec(name="my tool", description="Test")
        assert "valid python package name" in str(exc_info.value).lower()

    def test_invalid_package_name_with_special_chars(self) -> None:
        """CLI name with special characters is invalid."""
        with pytest.raises(ValidationError) as exc_info:
            CLISpec(name="my@tool", description="Test")
        assert "valid python package name" in str(exc_info.value).lower()

    def test_invalid_package_name_empty(self) -> None:
        """CLI name cannot be empty."""
        with pytest.raises(ValidationError):
            CLISpec(name="", description="Test")

    def test_invalid_package_name_python_keyword(self) -> None:
        """CLI name cannot be a Python keyword."""
        with pytest.raises(ValidationError) as exc_info:
            CLISpec(name="import", description="Test")
        assert "valid python package name" in str(exc_info.value).lower()

    def test_no_duplicate_command_names(self) -> None:
        """CLI cannot have duplicate command names."""
        with pytest.raises(ValidationError) as exc_info:
            CLISpec(
                name="mytool",
                description="Test",
                commands=[
                    CommandSpec(name="build", description="Build"),
                    CommandSpec(name="build", description="Also build"),  # Duplicate
                ],
            )
        assert "duplicate" in str(exc_info.value).lower()

    def test_unique_commands_are_valid(self) -> None:
        """CLI with unique command names should be valid."""
        cli = CLISpec(
            name="mytool",
            description="Test",
            commands=[
                CommandSpec(name="build", description="Build"),
                CommandSpec(name="test", description="Test"),
                CommandSpec(name="deploy", description="Deploy"),
            ],
        )
        assert len(cli.commands) == 3

    def test_no_duplicate_global_option_names(self) -> None:
        """CLI cannot have duplicate global option names."""
        with pytest.raises(ValidationError) as exc_info:
            CLISpec(
                name="mytool",
                description="Test",
                global_options=[
                    OptionSpec(name="verbose", short="v"),
                    OptionSpec(name="verbose", short="V"),  # Duplicate
                ],
            )
        assert "duplicate" in str(exc_info.value).lower()
