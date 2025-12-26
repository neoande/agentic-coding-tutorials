# CLI Generator

Generate complete, working CLI applications from natural language descriptions.

```
Input:  "A CLI that downloads YouTube videos with quality selection"
Output: A complete Python package with Click commands, help text, error handling, and tests
```

## Overview

This project demonstrates how to use AI agents for structured code generation. It takes a natural language description of a CLI tool and produces:

- A working Python package with Click-based commands
- Proper argument and option handling
- Help text and documentation
- Error handling with user-friendly messages
- pytest test suite

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/agentic-coding-tutorials.git
cd agentic-coding-tutorials/claude-code/cli-generator

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

## Usage

```bash
# Generate a CLI from a description
cli-gen "A tool that converts images between formats with resize options"

# Generated output appears in the generated/ directory
```

## Architecture

The generator follows a three-stage pipeline:

```
Natural Language → CLISpec (Pydantic) → Python Code (Jinja2)
```

### 1. Spec Generation
Parses natural language into a structured `CLISpec` model using PydanticAI.

### 2. Validation
Validates the spec for completeness, naming conventions, and forbidden patterns.

### 3. Code Generation
Uses Jinja2 templates to produce Python code from the validated spec.

## Data Models

### CLISpec
Top-level specification for the CLI:
- `name` - CLI name (e.g., "imgconvert")
- `description` - What the CLI does
- `commands` - List of commands
- `global_options` - Options available to all commands
- `dependencies` - Required pip packages

### CommandSpec
A single command:
- `name` - Command name
- `description` - Help text
- `arguments` - Positional arguments
- `options` - Command-line options
- `examples` - Usage examples

### OptionSpec
A command-line option:
- `name` - Long name (e.g., "output")
- `short` - Short alias (e.g., "o")
- `type` - Data type (str, int, float, bool, path, choice)
- `required` - Whether required
- `default` - Default value
- `choices` - Valid values for choice type

## Project Structure

```
cli-generator/
├── src/cli_generator/
│   ├── cli.py              # Main CLI interface
│   ├── models.py           # Pydantic data models
│   ├── generators/         # Code generation logic
│   │   ├── spec_generator.py   # NL → CLISpec
│   │   ├── code_generator.py   # CLISpec → Python
│   │   └── test_generator.py   # CLISpec → pytest
│   ├── validators/         # Validation logic
│   └── templates/          # Jinja2 templates
├── tests/                  # Test suite
├── generated/              # Output directory
└── examples/               # Example descriptions
```

## Technology Choices

| Technology | Purpose | Why |
|------------|---------|-----|
| **Click** | CLI framework | Most widely used, explicit decorators ideal for generation |
| **Pydantic** | Data models | Type-safe validation, great error messages |
| **PydanticAI** | LLM integration | Structured output parsing, built-in retries |
| **Jinja2** | Templates | Industry standard, readable syntax |
| **Rich** | Terminal output | Beautiful formatting, progress bars |

## Generated CLI Conventions

Every generated CLI follows these standards:

- `--help` flag (automatic with Click)
- `--version` flag
- `--verbose/-v` for debug output
- `--quiet/-q` to suppress output
- `--no-color` to disable colors
- Exit codes: 0 (success), 1 (user error), 2 (system error)
- User-friendly error messages (no stack traces unless verbose)

## Development

```bash
# Run tests
pytest

# Run a specific test
pytest tests/test_models.py -v
```

## Current Status

This project is under active development as part of the agentic coding tutorial series.

**Completed:**
- Data models (CLISpec, CommandSpec, OptionSpec, ArgumentSpec)
- Project structure and configuration

**In Progress:**
- Spec generator (NL → CLISpec)
- Code generator (CLISpec → Python)

**Planned:**
- Test generator
- Validation layer
- CLI interface

## License

MIT License - see the repository root for details.
