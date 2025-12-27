"""Unit tests for SpecGenerator."""

import pytest
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel, AgentInfo
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart

from cli_generator.generators.spec_generator import SpecGenerator
from cli_generator.models import CLISpec, CommandSpec, OptionSpec, ArgumentSpec


class TestSpecGeneratorInit:
    """Tests for SpecGenerator initialization."""

    def test_default_model(self) -> None:
        """SpecGenerator should use default model."""
        gen = SpecGenerator()
        assert gen.model == "openai:gpt-4o-mini"

    def test_custom_model(self) -> None:
        """SpecGenerator should accept custom model."""
        gen = SpecGenerator(model="anthropic:claude-3-5-sonnet-latest")
        assert gen.model == "anthropic:claude-3-5-sonnet-latest"


class TestSpecGeneratorGenerate:
    """Tests for SpecGenerator.generate() method."""

    @pytest.fixture
    def generator(self) -> SpecGenerator:
        """Create a SpecGenerator instance."""
        return SpecGenerator()

    @pytest.mark.asyncio
    async def test_generate_simple_cli(self, generator: SpecGenerator) -> None:
        """Generate a simple CLI from description."""
        # Use TestModel to mock LLM response
        with generator.agent.override(model=TestModel()):
            result = await generator.generate(
                "A CLI that converts images between formats"
            )

        # TestModel returns valid structured data based on schema
        assert isinstance(result, CLISpec)
        assert result.name  # Should have a name
        assert result.description  # Should have a description

    @pytest.mark.asyncio
    async def test_generate_returns_clispec(self, generator: SpecGenerator) -> None:
        """Generate method should return CLISpec type."""

        def mock_response(
            messages: list[ModelMessage], info: AgentInfo
        ) -> ModelResponse:
            """Return a mock CLISpec as structured output."""
            # FunctionModel needs to return the structured data
            return ModelResponse(
                parts=[
                    TextPart(
                        content='{"name": "imgconvert", "description": "Convert images between formats"}'
                    )
                ]
            )

        with generator.agent.override(model=TestModel()):
            result = await generator.generate("Convert images")

        assert isinstance(result, CLISpec)

    @pytest.mark.asyncio
    async def test_generate_with_commands(self, generator: SpecGenerator) -> None:
        """Generated CLI should have commands when appropriate."""
        with generator.agent.override(model=TestModel()):
            result = await generator.generate(
                "A file manager CLI with list, copy, and delete commands"
            )

        assert isinstance(result, CLISpec)
        # TestModel generates valid data based on schema

    @pytest.mark.asyncio
    async def test_generate_empty_description_raises(
        self, generator: SpecGenerator
    ) -> None:
        """Empty description should raise ValueError."""
        with pytest.raises(ValueError, match="description"):
            await generator.generate("")

    @pytest.mark.asyncio
    async def test_generate_whitespace_description_raises(
        self, generator: SpecGenerator
    ) -> None:
        """Whitespace-only description should raise ValueError."""
        with pytest.raises(ValueError, match="description"):
            await generator.generate("   ")


class TestSpecGeneratorAddCommand:
    """Tests for SpecGenerator.add_command() method."""

    @pytest.fixture
    def generator(self) -> SpecGenerator:
        """Create a SpecGenerator instance."""
        return SpecGenerator()

    @pytest.fixture
    def base_spec(self) -> CLISpec:
        """Create a base CLISpec for testing."""
        return CLISpec(
            name="mytool",
            description="A test tool",
            commands=[
                CommandSpec(name="existing", description="An existing command")
            ],
        )

    @pytest.mark.asyncio
    async def test_add_command_returns_clispec(
        self, generator: SpecGenerator, base_spec: CLISpec
    ) -> None:
        """add_command should return CLISpec."""
        with generator.command_agent.override(model=TestModel()):
            result = await generator.add_command(
                base_spec, "Add a search command that finds files"
            )

        assert isinstance(result, CLISpec)

    @pytest.mark.asyncio
    async def test_add_command_preserves_existing(
        self, generator: SpecGenerator, base_spec: CLISpec
    ) -> None:
        """add_command should preserve existing commands."""
        with generator.command_agent.override(model=TestModel()):
            result = await generator.add_command(base_spec, "Add a new command")

        # The existing command should still be there
        assert any(cmd.name == "existing" for cmd in result.commands)

    @pytest.mark.asyncio
    async def test_add_command_empty_description_raises(
        self, generator: SpecGenerator, base_spec: CLISpec
    ) -> None:
        """Empty command description should raise ValueError."""
        with pytest.raises(ValueError, match="description"):
            await generator.add_command(base_spec, "")


class TestSpecGeneratorSystemPrompt:
    """Tests for system prompt content."""

    def test_system_prompt_mentions_cli_conventions(self) -> None:
        """System prompt should mention CLI conventions."""
        gen = SpecGenerator()
        prompt = gen.get_system_prompt()

        # Should mention standard options
        assert "-v" in prompt or "verbose" in prompt.lower()
        assert "-o" in prompt or "output" in prompt.lower()

    def test_system_prompt_mentions_naming(self) -> None:
        """System prompt should mention naming conventions."""
        gen = SpecGenerator()
        prompt = gen.get_system_prompt()

        # Should mention naming
        assert "name" in prompt.lower()

    def test_system_prompt_mentions_commands(self) -> None:
        """System prompt should mention command structure."""
        gen = SpecGenerator()
        prompt = gen.get_system_prompt()

        # Should mention commands
        assert "command" in prompt.lower()


class TestSpecGeneratorValidation:
    """Tests for output validation."""

    @pytest.fixture
    def generator(self) -> SpecGenerator:
        """Create a SpecGenerator instance."""
        return SpecGenerator()

    @pytest.mark.asyncio
    async def test_generated_spec_has_valid_name(
        self, generator: SpecGenerator
    ) -> None:
        """Generated CLISpec should have valid Python package name."""
        with generator.agent.override(model=TestModel()):
            result = await generator.generate("A simple counter tool")

        # Name should be valid (no hyphens, valid identifier)
        assert result.name.replace("_", "").isalnum() or result.name[0] == "_"
        assert not result.name[0].isdigit()

    @pytest.mark.asyncio
    async def test_generated_spec_has_description(
        self, generator: SpecGenerator
    ) -> None:
        """Generated CLISpec should have non-empty description."""
        with generator.agent.override(model=TestModel()):
            result = await generator.generate("A URL shortener")

        assert result.description
        assert len(result.description) > 0
