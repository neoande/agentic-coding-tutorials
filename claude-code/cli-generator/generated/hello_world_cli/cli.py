"""A simple CLI that greets the user with 'Hello, World!'"""

import click


@click.group()
@click.version_option()
def cli() -> None:
    """A simple CLI that greets the user with 'Hello, World!'"""
    pass


@cli.command()
@click.option("-v", "--verbose", is_flag=True, help="Show additional details")
def greet(verbose: bool) -> None:
    """Outputs a greeting message

    Examples:
        hello_world_cli greet
        hello_world_cli greet -v
    """
    # TODO: Implement greet command
    click.echo("greet command called")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()