# CLI Generator
## What This Project Does
Generates complete, working CLI applications from natural language descriptions.
Input: "A CLI that downloads YouTube videos with quality selection"
Output: A complete Python package with Click commands, help text, error handling, and tests.
## Current State
Week 1: Building foundation - core generator working, basic commands.
## Technology Decisions
### Why Click (not Typer or argparse)?
- Most widely used in production
- Excellent documentation
- Decorators are explicit (good for generation)
- Better error messages than argparse
### Why Jinja2 for Templates?
- Industry standard
- Easy to read template syntax
- Good error messages for template issues
- Supports template inheritance
### Why PydanticAI?
- Type-safe LLM interactions
- Structured output parsing
- Built-in retry logic
- Works with multiple providers
## My CLI Preferences (Use These for Generation)
### Structure
- One command per file in `commands/` directory
- Main CLI group in `cli.py`
- Shared utilities in `utils.py`
### Style
- Always include `--help` (Click does this automatically)
- Always include `--version` flag
- Use `--verbose/-v` for debug output
- Use `--quiet/-q` to suppress output
- Color output by default, `--no-color` to disable
### Error Handling
- Catch exceptions and show user-friendly messages
- Exit code 0 for success, 1 for user error, 2 for system error
- Never show stack traces unless `--verbose`
### Documentation
- Every command has a docstring (becomes help text)
- Every option has `help=` parameter
- Include usage examples in command docstrings
## Data Models
### CLISpec
The specification for a CLI to generate:
```python
class CLISpec(BaseModel):
name: str # CLI name (e.g., "imgconvert")
description: str # What it does
commands: list[CommandSpec] # Commands to generate
global_options: list[OptionSpec] # Options for all commands
python_version: str = "3.11"
dependencies: list[str] = []
CommandSpec
A single command in the CLI:
class CommandSpec(BaseModel):
name: str # Command name (e.g., "convert")
description: str # Help text
arguments: list[ArgumentSpec]
options: list[OptionSpec]
examples: list[str] = []
OptionSpec
A command-line option:
class OptionSpec(BaseModel):
name: str # Long name (e.g., "output")
short: str | None = None # Short name (e.g., "o")
type: str = "str" # str, int, float, bool, path, choice
required: bool = False
default: Any = None
help: str = ""
choices: list[str] | None = None # For choice type
ArgumentSpec
A positional argument:
class ArgumentSpec(BaseModel):
name: str
type: str = "str"
required: bool = True
help: str = ""
File Structure
cli-generator/
├── .claude/
│ ├── CLAUDE.md # This file
│ ├── commands/ # Slash commands
│ ├── hooks/ # Quality gates
│ ├── skills/ # Context-aware behaviors
│ ├── subagents/ # Specialized agents
│ ├── mcp/ # External tool definitions
│ └── rules/ # Standards and guidelines
├── src/cli_generator/
│ ├── __init__.py
│ ├── cli.py # Main CLI (our own interface)
│ ├── models.py # Pydantic models
│ ├── generators/
│ │ ├── __init__.py
│ │ ├── spec_generator.py # NL → CLISpec
│ │ ├── code_generator.py # CLISpec → Python code
│ │ └── test_generator.py # CLISpec → pytest tests
│ ├── validators/
│ │ ├── __init__.py
│ │ ├── spec_validator.py # Validate CLISpec
│ │ └── code_validator.py # Validate generated code
│ └── templates/
│ ├── cli.py.j2 # Main CLI template
│ ├── command.py.j2 # Command template
│ └── test.py.j2 # Test template
├── tests/
├── generated/ # Output directory
└── examples/ # Example descriptions
Common Workflows
Generate a New CLI
1. User provides natural language description
2. LLM parses into CLISpec
3. Validator checks spec
4. Code generator creates Python files
5. Test generator creates pytest files
6. Output validator checks code compiles
Add Command to Existing CLI
1. Load existing CLISpec from generated CLI
2. Parse new command description
3. Merge into existing spec
4. Regenerate code (preserving customizations?)
What's Not Built Yet
Spec generator (Day 2)
Code generator (Day 2)
Slash commands (Days 3-4)
Hooks (Day 5)
Skills (Day 6)
Subagents (Day 7)
MCP tools (Day 8)
Testing Strategy
Unit tests: Each generator/validator in isolation
Integration tests: Full NL → working CLI flow
Golden tests: Known inputs produce expected outputs
### Create Rules Files
Create `.claude/rules/code_standards.md`:
```markdown
# Code Standards
## Python Style
- Python 3.11+ features allowed (match statements, type unions with |)
- Type hints required on all function signatures
- Docstrings required on all public functions
- Use `pathlib.Path` for file paths
- Use `async/await` for I/O operations
## Generated Code Style
Generated CLIs should follow these conventions:
- Imports at top, stdlib first, then third-party, then local
- One class per file for complex commands
- Helper functions prefixed with underscore
- Constants in UPPER_SNAKE_CASE
## Testing
- Every generator function needs tests
- Use pytest fixtures for common test data
- Mock LLM calls in unit tests
- Integration tests can use real LLM (marked slow)
## Error Messages
- User-facing: Friendly, actionable
- Developer-facing: Include context (what was being generated)
- Never expose internal details to users
Create .claude/rules/generation_rules.md:
# CLI Generation Rules
## Naming Conventions
- CLI names: lowercase, hyphens allowed (e.g., `my-tool`)
- Command names: lowercase, underscores for multi-word (e.g., `list_items`)
- Option names: lowercase, hyphens (e.g., `--output-dir`)
- Short options: single letter, common conventions (e.g., `-o` for output, `-v` for verbose)
## Required Elements
Every generated CLI must have:
1. `--help` flag (Click provides automatically)
2. `--version` flag
3. Proper exit codes (0=success, 1=user error, 2=system error)
4. Error handling that doesn't show tracebacks
## Forbidden Patterns
- Never generate `eval()` or `exec()`
- Never generate hardcoded credentials
- Never generate commands that delete without confirmation
- Never generate `sudo` or privilege escalation
## Template Variables
Templates receive these variables:
- `cli`: The full CLISpec object
- `command`: The current CommandSpec (in command template)
- `timestamp`: Generation timestamp
- `generator_version`: Version of cli-generator
