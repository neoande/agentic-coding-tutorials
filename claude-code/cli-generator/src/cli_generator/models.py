"""Pydantic models for CLI specification."""

import keyword
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def sanitize_name(name: str) -> str:
    """Remove leading dashes and clean up option/argument names."""
    # Strip leading dashes (e.g., "--output" -> "output", "-o" -> "o")
    cleaned = name.lstrip("-")
    # Replace remaining dashes with underscores for Python compatibility
    # but keep single dashes in multi-word options like "output-dir"
    return cleaned


class ArgumentSpec(BaseModel):
    """A positional argument for a CLI command."""

    name: str = Field(..., description="Argument name (e.g., 'filename')")
    type: str = Field(default="str", description="Type: str, int, float, path")
    required: bool = Field(default=True, description="Whether argument is required")
    help: str = Field(default="", description="Help text for the argument")

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Clean up argument name by removing any leading dashes."""
        if isinstance(v, str):
            return sanitize_name(v)
        return v


class OptionSpec(BaseModel):
    """A command-line option (flag)."""

    name: str = Field(..., description="Long option name (e.g., 'output')")
    short: str | None = Field(default=None, description="Short name (e.g., 'o')")
    type: str = Field(
        default="str", description="Type: str, int, float, bool, path, choice"
    )
    required: bool = Field(default=False, description="Whether option is required")
    default: Any = Field(default=None, description="Default value")
    help: str = Field(default="", description="Help text for the option")
    choices: list[str] | None = Field(
        default=None, description="Valid choices (for choice type)"
    )

    @field_validator("name", mode="before")
    @classmethod
    def clean_name(cls, v: str) -> str:
        """Clean up option name by removing any leading dashes."""
        if isinstance(v, str):
            return sanitize_name(v)
        return v

    @field_validator("short", mode="before")
    @classmethod
    def clean_short(cls, v: str | None) -> str | None:
        """Clean up short option by removing any leading dash."""
        if isinstance(v, str):
            cleaned = v.lstrip("-")
            return cleaned if cleaned else None
        return v

    @model_validator(mode="after")
    def validate_short_option(self) -> "OptionSpec":
        """Validate that short option is a single character."""
        if self.short is not None and len(self.short) != 1:
            raise ValueError(
                f"Short option must be a single character, got '{self.short}'"
            )
        return self

    @model_validator(mode="after")
    def validate_choice_type_has_choices(self) -> "OptionSpec":
        """Validate that choice type options have a non-empty choices list."""
        if self.type == "choice":
            if self.choices is None or len(self.choices) == 0:
                raise ValueError(
                    "Option with type='choice' must have a non-empty choices list"
                )
        return self


class CommandSpec(BaseModel):
    """A single command in the CLI."""

    name: str = Field(..., description="Command name (e.g., 'convert')")
    description: str = Field(..., description="Help text shown to users")
    arguments: list[ArgumentSpec] = Field(
        default_factory=list, description="Positional arguments"
    )
    options: list[OptionSpec] = Field(
        default_factory=list, description="Command options"
    )
    examples: list[str] = Field(
        default_factory=list, description="Usage examples for help text"
    )

    @model_validator(mode="after")
    def validate_no_duplicates(self) -> "CommandSpec":
        """Validate no duplicate option names, short names, or argument names."""
        # Check for duplicate option names
        option_names = [opt.name for opt in self.options]
        if len(option_names) != len(set(option_names)):
            seen = set()
            duplicates = [n for n in option_names if n in seen or seen.add(n)]  # type: ignore[func-returns-value]
            raise ValueError(f"Duplicate option names: {duplicates}")

        # Check for duplicate short option names (excluding None)
        short_names = [opt.short for opt in self.options if opt.short is not None]
        if len(short_names) != len(set(short_names)):
            seen = set()
            duplicates = [n for n in short_names if n in seen or seen.add(n)]  # type: ignore[func-returns-value]
            raise ValueError(f"Duplicate short option names: {duplicates}")

        # Check for duplicate argument names
        arg_names = [arg.name for arg in self.arguments]
        if len(arg_names) != len(set(arg_names)):
            seen = set()
            duplicates = [n for n in arg_names if n in seen or seen.add(n)]  # type: ignore[func-returns-value]
            raise ValueError(f"Duplicate argument names: {duplicates}")

        return self


# Pattern for valid Python identifiers (package names)
PYTHON_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class CLISpec(BaseModel):
    """The complete specification for a CLI to generate."""

    name: str = Field(..., description="CLI name (e.g., 'imgconvert')")
    description: str = Field(..., description="What the CLI does")
    commands: list[CommandSpec] = Field(
        default_factory=list, description="Commands to generate"
    )
    global_options: list[OptionSpec] = Field(
        default_factory=list, description="Options available to all commands"
    )
    python_version: str = Field(default="3.11", description="Target Python version")
    dependencies: list[str] = Field(
        default_factory=list, description="Required pip packages"
    )

    @model_validator(mode="after")
    def validate_cli_spec(self) -> "CLISpec":
        """Validate CLI name is valid package name and no duplicate commands."""
        # Validate CLI name is a valid Python package name
        if not self.name:
            raise ValueError("CLI name cannot be empty")

        if not PYTHON_IDENTIFIER_PATTERN.match(self.name):
            raise ValueError(
                f"'{self.name}' is not a valid Python package name. "
                "Must start with a letter or underscore, contain only "
                "letters, numbers, and underscores."
            )

        if keyword.iskeyword(self.name):
            raise ValueError(
                f"'{self.name}' is not a valid Python package name. "
                "Cannot use Python keywords."
            )

        # Check for duplicate command names
        command_names = [cmd.name for cmd in self.commands]
        if len(command_names) != len(set(command_names)):
            seen = set()
            duplicates = [n for n in command_names if n in seen or seen.add(n)]  # type: ignore[func-returns-value]
            raise ValueError(f"Duplicate command names: {duplicates}")

        # Check for duplicate global option names
        option_names = [opt.name for opt in self.global_options]
        if len(option_names) != len(set(option_names)):
            seen = set()
            duplicates = [n for n in option_names if n in seen or seen.add(n)]  # type: ignore[func-returns-value]
            raise ValueError(f"Duplicate global option names: {duplicates}")

        # Check for duplicate global short option names
        short_names = [opt.short for opt in self.global_options if opt.short is not None]
        if len(short_names) != len(set(short_names)):
            seen = set()
            duplicates = [n for n in short_names if n in seen or seen.add(n)]  # type: ignore[func-returns-value]
            raise ValueError(f"Duplicate global short option names: {duplicates}")

        return self
