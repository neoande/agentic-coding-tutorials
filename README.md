# Agentic Coding Tutorials

Learn how to build software using AI coding agents. This repository contains hands-on projects that teach you to work effectively with tools like Claude Code, Cursor, and other AI-assisted development environments.

## What is Agentic Coding?

Agentic coding is a development approach where AI agents actively participate in the software development process. Instead of just autocompleting code, these agents can:

- **Understand context** - Read your codebase, documentation, and project structure
- **Plan and execute** - Break down tasks and implement them step by step
- **Use tools** - Run commands, search files, make API calls, and interact with external systems
- **Iterate and improve** - Test their work, fix errors, and refine solutions

## Projects

### [Claude Code](/claude-code)

Projects built with [Claude Code](https://claude.ai/claude-code), Anthropic's CLI tool for agentic coding.

| Project | Description | Concepts Covered |
|---------|-------------|------------------|
| [cli-generator](/claude-code/cli-generator) | Generate CLI apps from natural language | Structured prompts, code generation, Pydantic models |

## Key Concepts

### Project Configuration

Effective agentic coding starts with good project setup:

- **CLAUDE.md / Rules files** - Instructions that guide the AI's behavior
- **Structured data models** - Define clear schemas for AI-generated content
- **Validation layers** - Verify AI output meets your requirements

### Working with AI Agents

Tips for productive collaboration:

1. **Be specific** - Clear requirements produce better results
2. **Provide context** - Share relevant code, docs, and examples
3. **Iterate** - Review output and refine through conversation
4. **Trust but verify** - AI makes mistakes; always review generated code

### Common Patterns

- **Natural language → Structured data → Code** - Parse intent into schemas, then generate
- **Templates + Models** - Combine Jinja2/similar with validated data models
- **Layered validation** - Check specs, then generated code, then runtime behavior

## Getting Started

1. Clone this repository
2. Choose a project that interests you
3. Read the project's README for setup instructions
4. Follow along, experimenting with your own variations

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- An AI coding tool (Claude Code, Cursor, etc.)

## Contributing

Found an issue or want to add a tutorial? Contributions welcome! Please open an issue first to discuss.

## License

MIT License - see [LICENSE](LICENSE) for details.
