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
