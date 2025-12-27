"""Generate Python/Click code from CLISpec."""

from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape

from cli_generator.models import ArgumentSpec, CLISpec, OptionSpec


class CodeGenerator:
    """Generate Python/Click code from CLISpec using Jinja2 templates."""

    def __init__(self) -> None:
        """Initialize the code generator with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("cli_generator", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Register custom filters
        self.env.filters["to_func_name"] = self._to_func_name
        self.env.filters["to_param_name"] = self._to_param_name
        self.env.filters["python_type"] = self._python_type
        # Register custom functions
        self.env.globals["render_option"] = self._render_option
        self.env.globals["render_argument"] = self._render_argument

    @staticmethod
    def _to_func_name(name: str) -> str:
        """Convert a command name to a valid Python function name."""
        return name.replace("-", "_").replace(" ", "_").lower()

    @staticmethod
    def _to_param_name(name: str) -> str:
        """Convert an option/argument name to a valid Python parameter name."""
        return name.replace("-", "_").replace(" ", "_").lower()

    @staticmethod
    def _python_type(spec: ArgumentSpec | OptionSpec) -> str:
        """Get the Python type annotation for an argument or option."""
        type_map = {
            "str": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "path": "Path",
            "choice": "str",
        }
        base_type = type_map.get(spec.type, "str")

        # For optional parameters
        if isinstance(spec, OptionSpec) and not spec.required:
            if spec.type == "bool":
                return "bool"
            return f"{base_type} | None"

        return base_type

    @staticmethod
    def _render_option(option: OptionSpec) -> str:
        """Render a @click.option decorator for an option."""
        parts = ["@click.option("]

        # Option names
        if option.short:
            parts.append(f'"-{option.short}", ')
        parts.append(f'"--{option.name}"')

        # Type handling
        if option.type == "bool":
            parts.append(", is_flag=True")
        elif option.type == "int":
            parts.append(", type=int")
        elif option.type == "float":
            parts.append(", type=float")
        elif option.type == "path":
            parts.append(", type=click.Path()")
        elif option.type == "choice":
            choices_str = ", ".join(f'"{c}"' for c in (option.choices or []))
            parts.append(f", type=click.Choice([{choices_str}])")

        # Default value
        if option.default is not None and option.type != "bool":
            if isinstance(option.default, str):
                parts.append(f', default="{option.default}"')
            else:
                parts.append(f", default={option.default}")

        # Required flag
        if option.required:
            parts.append(", required=True")

        # Help text
        if option.help:
            # Escape quotes in help text
            help_text = option.help.replace('"', '\\"')
            parts.append(f', help="{help_text}"')

        parts.append(")")

        return "".join(parts)

    @staticmethod
    def _render_argument(arg: ArgumentSpec) -> str:
        """Render a @click.argument decorator for an argument."""
        parts = [f'@click.argument("{arg.name}"']

        # Type handling
        if arg.type == "int":
            parts.append(", type=int")
        elif arg.type == "float":
            parts.append(", type=float")
        elif arg.type == "path":
            parts.append(", type=click.Path(exists=True)")

        # Required flag (arguments are required by default in Click)
        if not arg.required:
            parts.append(", required=False")

        parts.append(")")

        return "".join(parts)

    def _has_path_types(self, spec: CLISpec) -> bool:
        """Check if the spec uses any path types that require Path import."""
        # Check global options
        for opt in spec.global_options:
            if opt.type == "path":
                return True

        # Check commands
        for cmd in spec.commands:
            for arg in cmd.arguments:
                if arg.type == "path":
                    return True
            for opt in cmd.options:
                if opt.type == "path":
                    return True

        return False

    def generate(self, spec: CLISpec, output_dir: Path) -> dict[str, Path]:
        """Generate CLI code from a CLISpec.

        Args:
            spec: The CLI specification to generate code from.
            output_dir: Directory to write generated files to.

        Returns:
            Dict mapping file type to path (cli, init, pyproject, readme).
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create package directory
        package_dir = output_dir / spec.name
        package_dir.mkdir(exist_ok=True)

        result: dict[str, Path] = {}

        # Generate cli.py
        cli_path = package_dir / "cli.py"
        cli_content = self._generate_cli(spec)
        cli_path.write_text(cli_content)
        result["cli"] = cli_path

        # Generate __init__.py
        init_path = package_dir / "__init__.py"
        init_content = self._generate_init(spec)
        init_path.write_text(init_content)
        result["init"] = init_path

        # Generate pyproject.toml
        pyproject_path = output_dir / "pyproject.toml"
        pyproject_content = self._generate_pyproject(spec)
        pyproject_path.write_text(pyproject_content)
        result["pyproject"] = pyproject_path

        # Generate README.md
        readme_path = output_dir / "README.md"
        readme_content = self._generate_readme(spec)
        readme_path.write_text(readme_content)
        result["readme"] = readme_path

        return result

    def _generate_cli(self, spec: CLISpec) -> str:
        """Generate the cli.py file content."""
        template = self.env.get_template("cli.py.j2")
        return template.render(
            cli=spec,
            has_path_types=self._has_path_types(spec),
        )

    def _generate_init(self, spec: CLISpec) -> str:
        """Generate the __init__.py file content."""
        return f'''"""{ spec.description }"""

__version__ = "0.1.0"
'''

    def _generate_pyproject(self, spec: CLISpec) -> str:
        """Generate the pyproject.toml file content."""
        # Collect dependencies
        deps = ["click>=8.1"]
        deps.extend(spec.dependencies)
        deps_str = ",\n    ".join(f'"{d}"' for d in deps)

        return f'''[project]
name = "{spec.name}"
version = "0.1.0"
description = "{spec.description}"
requires-python = ">={spec.python_version}"
dependencies = [
    {deps_str},
]

[project.scripts]
{spec.name} = "{spec.name}.cli:main"

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"
'''

    def _generate_readme(self, spec: CLISpec) -> str:
        """Generate the README.md file content."""
        readme = f"""# {spec.name}

{spec.description}

## Installation

```bash
pip install {spec.name}
```

## Usage

```bash
{spec.name} --help
```
"""

        if spec.commands:
            readme += "\n## Commands\n\n"
            for cmd in spec.commands:
                readme += f"### {cmd.name}\n\n"
                readme += f"{cmd.description}\n\n"
                readme += f"```bash\n{spec.name} {cmd.name} --help\n```\n\n"

        if spec.global_options:
            readme += "## Global Options\n\n"
            for opt in spec.global_options:
                opt_str = f"--{opt.name}"
                if opt.short:
                    opt_str = f"-{opt.short}, {opt_str}"
                readme += f"- `{opt_str}`: {opt.help}\n"

        return readme
