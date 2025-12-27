"""CLI interface for the CLI generator."""

import asyncio
import json
import os
import sys
from pathlib import Path

import click
from dotenv import load_dotenv
from pydantic import ValidationError
from pydantic_ai.models.test import TestModel
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from cli_generator.generators.code_generator import CodeGenerator
from cli_generator.generators.spec_generator import SpecGenerator
from cli_generator.models import CLISpec

# Load environment variables from .env file
load_dotenv()

# Rich console for pretty output
console = Console()
error_console = Console(stderr=True)

# Version
__version__ = "0.1.0"


def print_error(message: str) -> None:
    """Print an error message in red."""
    error_console.print(f"[bold red]Error:[/bold red] {message}")


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def print_spec_json(spec: CLISpec) -> None:
    """Pretty print a CLISpec as JSON with syntax highlighting."""
    json_str = spec.model_dump_json(indent=2)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="[bold]CLI Specification[/bold]", border_style="blue"))


def print_spec_summary(spec: CLISpec) -> None:
    """Print a summary table of the CLISpec."""
    table = Table(title=f"[bold]{spec.name}[/bold] - {spec.description}")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Arguments", style="yellow")
    table.add_column("Options", style="green")

    for cmd in spec.commands:
        args = ", ".join(arg.name for arg in cmd.arguments) or "-"
        opts = ", ".join(f"--{opt.name}" for opt in cmd.options) or "-"
        table.add_row(cmd.name, cmd.description, args, opts)

    if spec.global_options:
        global_opts = ", ".join(f"--{opt.name}" for opt in spec.global_options)
        table.add_row("[dim]global[/dim]", "[dim]Available to all commands[/dim]", "-", f"[dim]{global_opts}[/dim]")

    console.print(table)


@click.group()
@click.version_option(version=__version__, prog_name="cli-gen")
def cli() -> None:
    """Generate CLI tools from natural language descriptions.

    Use 'spec' to generate a specification, 'generate' to create a complete CLI,
    or 'build' to generate from a saved spec file.
    """
    pass


@cli.command("spec")
@click.argument("description")
@click.option(
    "--save", "-s",
    type=click.Path(),
    help="Save spec to a JSON file",
)
@click.option(
    "--model", "-m",
    default="openai:gpt-4o-mini",
    help="Model to use for generation",
)
@click.option(
    "--test-mode",
    is_flag=True,
    hidden=True,
    help="Use test model (for testing)",
)
def spec_cmd(description: str, save: str | None, model: str, test_mode: bool) -> None:
    """Generate a CLI specification from a description.

    DESCRIPTION is a natural language description of the CLI you want to create.

    Examples:

        cli-gen spec "A CLI that converts images between formats"

        cli-gen spec "A file manager with list, copy, and delete commands" --save spec.json
    """
    try:
        print_info(f"Generating CLI specification...")

        # Create generator
        if test_mode:
            generator = SpecGenerator(model=TestModel())
        else:
            generator = SpecGenerator(model=model)

        # Run async generation
        spec = asyncio.run(_generate_spec(generator, description))

        # Display the spec
        print_spec_json(spec)
        print_spec_summary(spec)

        # Save if requested
        if save:
            save_path = Path(save)
            save_path.write_text(spec.model_dump_json(indent=2))
            print_success(f"Specification saved to {save_path}")

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


async def _generate_spec(generator: SpecGenerator, description: str) -> CLISpec:
    """Generate a CLISpec from description."""
    return await generator.generate(description)


@cli.command("generate")
@click.argument("description")
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./generated",
    help="Output directory for generated CLI",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show spec without generating files",
)
@click.option(
    "--model", "-m",
    default="openai:gpt-4o-mini",
    help="Model to use for generation",
)
@click.option(
    "--test-mode",
    is_flag=True,
    hidden=True,
    help="Use test model (for testing)",
)
def generate_cmd(
    description: str,
    output: str,
    dry_run: bool,
    model: str,
    test_mode: bool,
) -> None:
    """Generate a complete CLI from a description.

    DESCRIPTION is a natural language description of the CLI you want to create.

    Examples:

        cli-gen generate "A CLI that downloads YouTube videos"

        cli-gen generate "A task manager CLI" --output ./my-task-cli

        cli-gen generate "A counter tool" --dry-run
    """
    try:
        print_info("Generating CLI specification...")

        # Create spec generator
        if test_mode:
            spec_generator = SpecGenerator(model=TestModel())
        else:
            spec_generator = SpecGenerator(model=model)

        # Generate spec
        spec = asyncio.run(_generate_spec(spec_generator, description))

        # Show the spec
        print_spec_json(spec)
        print_spec_summary(spec)

        if dry_run:
            print_info("Dry run - no files generated")
            return

        # Generate code
        print_info("Generating code...")
        code_generator = CodeGenerator()
        output_path = Path(output)
        result = code_generator.generate(spec, output_path)

        # Show results
        console.print()
        print_success(f"CLI generated successfully in [bold]{output_path}[/bold]")
        console.print()

        table = Table(title="Generated Files")
        table.add_column("Type", style="cyan")
        table.add_column("Path", style="white")

        for file_type, file_path in result.items():
            table.add_row(file_type, str(file_path))

        console.print(table)

        # Print next steps
        console.print()
        console.print(Panel(
            f"[bold]Next steps:[/bold]\n\n"
            f"1. cd {output_path}\n"
            f"2. uv pip install -e .\n"
            f"3. {spec.name} --help",
            title="[bold green]Getting Started[/bold green]",
            border_style="green",
        ))

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


@cli.command("build")
@click.argument("spec_file", type=click.Path(exists=True))
@click.option(
    "--output", "-o",
    type=click.Path(),
    default="./generated",
    help="Output directory for generated CLI",
)
def build_cmd(spec_file: str, output: str) -> None:
    """Build a CLI from a saved specification file.

    SPEC_FILE is a JSON file containing a CLI specification.

    Examples:

        cli-gen build spec.json

        cli-gen build my-cli-spec.json --output ./my-cli
    """
    try:
        spec_path = Path(spec_file)

        if not spec_path.exists():
            print_error(f"File not found: {spec_path}")
            sys.exit(1)

        print_info(f"Loading specification from {spec_path}...")

        # Load and validate spec
        try:
            spec_data = json.loads(spec_path.read_text())
            spec = CLISpec.model_validate(spec_data)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON in {spec_path}: {e}")
            sys.exit(1)
        except ValidationError as e:
            print_error(f"Invalid specification: {e}")
            sys.exit(1)

        # Show the spec
        print_spec_summary(spec)

        # Generate code
        print_info("Generating code...")
        code_generator = CodeGenerator()
        output_path = Path(output)
        result = code_generator.generate(spec, output_path)

        # Show results
        console.print()
        print_success(f"CLI generated successfully in [bold]{output_path}[/bold]")
        console.print()

        table = Table(title="Generated Files")
        table.add_column("Type", style="cyan")
        table.add_column("Path", style="white")

        for file_type, file_path in result.items():
            table.add_row(file_type, str(file_path))

        console.print(table)

        # Print next steps
        console.print()
        console.print(Panel(
            f"[bold]Next steps:[/bold]\n\n"
            f"1. cd {output_path}\n"
            f"2. uv pip install -e .\n"
            f"3. {spec.name} --help",
            title="[bold green]Getting Started[/bold green]",
            border_style="green",
        ))

    except Exception as e:
        print_error(str(e))
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        error_console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
