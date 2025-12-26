"""Pydantic models for CLI specification."""

from typing import Any

from pydantic import BaseModel, Field


class ArgumentSpec(BaseModel):
    """A positional argument for a CLI command."""

    name: str = Field(..., description="Argument name (e.g., 'filename')")
    type: str = Field(default="str", description="Type: str, int, float, path")
    required: bool = Field(default=True, description="Whether argument is required")
    help: str = Field(default="", description="Help text for the argument")


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
