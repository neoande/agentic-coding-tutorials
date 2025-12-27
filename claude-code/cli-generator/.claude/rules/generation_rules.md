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
