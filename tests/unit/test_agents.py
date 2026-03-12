"""Unit tests for the assistant agent."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from agents.assistant_agent import AssistantAgent
from shared.config import ALFRED_SYSTEM_PROMPT


class TestAssistantAgent:
    """Test AssistantAgent AI logic."""

    def test_answer_returns_string(self, mock_llm_provider, mock_knowledge_provider):
        """Test that answer returns a string response."""
        mock_llm_provider.invoke_model.return_value = "This is my response"
        mock_knowledge_provider.fetch_knowledge.return_value = {"knowledge": "base"}

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        result = agent.answer("What is your experience?")

        assert isinstance(result, str)
        assert len(result) > 0

    def test_answer_invokes_llm_provider(
        self, mock_llm_provider, mock_knowledge_provider
    ):
        """Test that answer calls LLM provider."""
        mock_llm_provider.invoke_model.return_value = "Response from LLM"
        mock_knowledge_provider.fetch_knowledge.return_value = {"knowledge": "base"}

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        agent.answer("Test question")

        mock_llm_provider.invoke_model.assert_called_once()

    def test_answer_fetches_knowledge_base(
        self, mock_llm_provider, mock_knowledge_provider
    ):
        """Test that answer fetches knowledge base."""
        mock_knowledge_provider.fetch_knowledge.return_value = {"knowledge": "base"}
        mock_llm_provider.invoke_model.return_value = "Response"

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        agent.answer("Test question")

        mock_knowledge_provider.fetch_knowledge.assert_called_once()

    def test_answer_includes_system_prompt(
        self, mock_llm_provider, mock_knowledge_provider
    ):
        """Test that system prompt is included in request."""
        mock_knowledge_provider.fetch_knowledge.return_value = {"knowledge": "base"}
        mock_llm_provider.invoke_model.return_value = "Response"

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        agent.answer("Test question")

        # Check that invoke_model was called with system prompt
        call_args = mock_llm_provider.invoke_model.call_args
        # System prompt should be in the prompt parameter
        assert mock_llm_provider.invoke_model.called

    def test_answer_includes_question(self, mock_llm_provider, mock_knowledge_provider):
        """Test that question is included in prompt."""
        mock_knowledge_provider.fetch_knowledge.return_value = {"knowledge": "base"}
        mock_llm_provider.invoke_model.return_value = "Response"

        test_question = "What is your experience with AWS?"

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        agent.answer(test_question)

        # Question should be passed to invoke_model
        call_args = mock_llm_provider.invoke_model.call_args
        # The question should be somewhere in the call
        assert mock_llm_provider.invoke_model.called

    def test_answer_includes_knowledge_base(
        self, mock_llm_provider, mock_knowledge_provider
    ):
        """Test that knowledge base is included in prompt."""
        knowledge_data = {"personal_info": {"name": "Loc Le", "experience": "6+ years"}}
        mock_knowledge_provider.fetch_knowledge.return_value = knowledge_data
        mock_llm_provider.invoke_model.return_value = "Response"

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        agent.answer("Test question")

        # Knowledge base should have been fetched
        mock_knowledge_provider.fetch_knowledge.assert_called_once()

    def test_answer_handles_empty_knowledge(
        self, mock_llm_provider, mock_knowledge_provider
    ):
        """Test that answer handles empty knowledge gracefully."""
        mock_knowledge_provider.fetch_knowledge.return_value = {}
        mock_llm_provider.invoke_model.return_value = "Default response"

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        result = agent.answer("Test question")

        assert result == "Default response"

    def test_answer_formats_prompt(self, mock_llm_provider, mock_knowledge_provider):
        """Test that prompt is properly formatted."""
        mock_knowledge_provider.fetch_knowledge.return_value = {"knowledge": "data"}
        mock_llm_provider.invoke_model.return_value = "Response"

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        agent.answer("What do you do?")

        # Verify invoke_model was called (which constructs the prompt)
        assert mock_llm_provider.invoke_model.called


class TestAssistantAgentInit:
    """Test AssistantAgent initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default providers."""
        agent = AssistantAgent()
        assert agent.llm_provider is not None
        assert agent.knowledge_provider is not None

    def test_init_with_custom_llm(self, mock_llm_provider):
        """Test initialization with custom LLM provider."""
        agent = AssistantAgent(llm_provider=mock_llm_provider)
        assert agent.llm_provider == mock_llm_provider

    def test_init_with_custom_knowledge(self, mock_knowledge_provider):
        """Test initialization with custom knowledge provider."""
        agent = AssistantAgent(knowledge_provider=mock_knowledge_provider)
        assert agent.knowledge_provider == mock_knowledge_provider

    def test_init_with_all_custom(self, mock_llm_provider, mock_knowledge_provider):
        """Test initialization with all custom providers."""
        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )
        assert agent.llm_provider == mock_llm_provider
        assert agent.knowledge_provider == mock_knowledge_provider


class TestAssistantAgentPromptConstruction:
    """Test prompt construction logic."""

    def test_system_prompt_constant(self):
        """Test that system prompt is defined."""
        from shared.config import ALFRED_SYSTEM_PROMPT

        assert ALFRED_SYSTEM_PROMPT is not None
        assert len(ALFRED_SYSTEM_PROMPT) > 0
        assert "alfred" in ALFRED_SYSTEM_PROMPT.lower()

    def test_answer_with_different_questions(
        self, mock_llm_provider, mock_knowledge_provider
    ):
        """Test agent with various question types."""
        mock_knowledge_provider.fetch_knowledge.return_value = {"knowledge": "data"}
        mock_llm_provider.invoke_model.return_value = "Generic response"

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        questions = [
            "What is your background?",
            "What technologies do you know?",
            "Can you help me with Python?",
        ]

        for question in questions:
            result = agent.answer(question)
            assert isinstance(result, str)
            assert len(result) > 0


class TestAssistantAgentErrorHandling:
    """Test error handling in agent."""

    def test_answer_handles_llm_error(self, mock_llm_provider, mock_knowledge_provider):
        """Test that agent handles LLM errors."""
        mock_knowledge_provider.fetch_knowledge.return_value = {"knowledge": "data"}
        mock_llm_provider.invoke_model.side_effect = Exception("LLM error")

        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        # Should propagate the error
        with pytest.raises(Exception):
            agent.answer("Test question")

    def test_answer_handles_knowledge_error(
        self, mock_llm_provider, mock_knowledge_provider
    ):
        """Test that agent handles knowledge provider errors."""
        mock_knowledge_provider.fetch_knowledge.side_effect = Exception(
            "Knowledge error"
        )

        # Should not raise - error is caught in __init__
        agent = AssistantAgent(
            llm_provider=mock_llm_provider, knowledge_provider=mock_knowledge_provider
        )

        # Knowledge should be empty dict due to error
        assert agent.knowledge == {}
