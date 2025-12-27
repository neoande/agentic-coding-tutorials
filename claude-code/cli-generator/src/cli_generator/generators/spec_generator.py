"""Generate CLISpec from natural language descriptions using PydanticAI."""

from typing import Union

from pydantic_ai import Agent
from pydantic_ai.models import Model

from cli_generator.models import CLISpec, CommandSpec


# System prompt that guides the LLM to generate good CLI specifications
SYSTEM_PROMPT = """You are an expert CLI designer. Your task is to convert natural language
descriptions into well-structured CLI specifications.

## CRITICAL: Field Format Rules

### Option and Argument Names
- Option `name` field: Use ONLY the name WITHOUT dashes. Example: "output" NOT "--output"
- Option `short` field: Use ONLY the single letter WITHOUT dash. Example: "o" NOT "-o"
- Argument `name` field: Use ONLY the name. Example: "filename" NOT "<filename>"

### DO NOT include these as options (they are added automatically):
- help/--help/-h (Click adds this)
- version/--version (handled separately)

## CLI Design Principles

### Naming Conventions
- CLI names: lowercase with underscores (e.g., `word_counter`, `file_manager`)
- CLI names must be valid Python identifiers (no hyphens, no spaces)
- Command names: short verbs (e.g., `count`, `list`, `convert`)
- Option names: lowercase, can use hyphens in the actual CLI but store as `output_dir` or `output-dir`

### Standard Options (short name conventions)
- output: short="o" - Output file or directory
- verbose: short="v" - Enable verbose output (type="bool")
- quiet: short="q" - Suppress output (type="bool")
- force: short="f" - Force without confirmation (type="bool")
- dry_run: short="n" - Show what would happen (type="bool")

### Arguments vs Options
- Arguments: Required positional inputs (filename, url)
- Options: Optional flags that modify behavior
- Use arguments for the "what" (target of operation)
- Use options for the "how" (configuration of operation)

### Type Values
- "str": String (default)
- "int": Integer
- "float": Floating point
- "bool": Boolean flag (is_flag=True in Click)
- "path": File path
- "choice": Selection from list (must include `choices` field)

## Example Output Structure

```json
{
  "name": "word_counter",
  "description": "Count words in text files",
  "commands": [
    {
      "name": "count",
      "description": "Count words in a file",
      "arguments": [
        {"name": "file", "type": "path", "required": true, "help": "File to count"}
      ],
      "options": [
        {"name": "verbose", "short": "v", "type": "bool", "help": "Show details"}
      ],
      "examples": ["word_counter count myfile.txt -v"]
    }
  ],
  "global_options": [],
  "python_version": "3.11",
  "dependencies": []
}
```

Keep it simple - only include options that are actually needed for the described functionality.
"""


class SpecGenerator:
    """Generate CLISpec from natural language descriptions using an LLM."""

    def __init__(self, model: Union[str, Model] = "openai:gpt-4o-mini") -> None:
        """Initialize the generator with a model.

        Args:
            model: The model identifier string (e.g., "openai:gpt-4o-mini",
                   "anthropic:claude-3-5-sonnet-latest") or a Model instance
                   (e.g., TestModel for testing).
        """
        self.model = model if isinstance(model, str) else str(type(model).__name__)
        self._model_instance = model
        self.agent = Agent(
            model,
            output_type=CLISpec,
            system_prompt=SYSTEM_PROMPT,
            defer_model_check=True,
        )
        # Separate agent for generating individual commands
        self.command_agent = Agent(
            model,
            output_type=CommandSpec,
            system_prompt=SYSTEM_PROMPT,
            defer_model_check=True,
        )

    def get_system_prompt(self) -> str:
        """Return the system prompt used for generation.

        Returns:
            The system prompt string.
        """
        return SYSTEM_PROMPT

    async def generate(self, description: str) -> CLISpec:
        """Generate a CLISpec from a natural language description.

        Args:
            description: Natural language description of the desired CLI.

        Returns:
            A CLISpec object representing the CLI.

        Raises:
            ValueError: If description is empty or whitespace only.
        """
        if not description or not description.strip():
            raise ValueError("description cannot be empty")

        result = await self.agent.run(
            f"Create a CLI specification for: {description}"
        )
        return result.output

    async def add_command(self, spec: CLISpec, description: str) -> CLISpec:
        """Add a new command to an existing CLISpec.

        Args:
            spec: The existing CLISpec to add a command to.
            description: Natural language description of the new command.

        Returns:
            A new CLISpec with the command added.

        Raises:
            ValueError: If description is empty or whitespace only.
        """
        if not description or not description.strip():
            raise ValueError("description cannot be empty")

        # Generate the new command using the command agent
        result = await self.command_agent.run(
            f"""Add a command to the CLI "{spec.name}" ({spec.description}).

Existing commands: {[cmd.name for cmd in spec.commands]}

New command request: {description}

Generate a CommandSpec for this new command that fits well with the existing CLI."""
        )

        # Create a new CLISpec with the command added
        new_commands = list(spec.commands) + [result.output]

        return CLISpec(
            name=spec.name,
            description=spec.description,
            commands=new_commands,
            global_options=spec.global_options,
            python_version=spec.python_version,
            dependencies=spec.dependencies,
        )
