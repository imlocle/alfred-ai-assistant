"""Unit tests for the assistant service."""

import pytest
from unittest.mock import Mock, call, patch
from services.assistant_service import AssistantService
from shared.exceptions import RateLimitError


class TestAssistantService:
    """Test AssistantService orchestration."""

    def test_ask_returns_cached_response(
        self,
        mock_assistant_agent,
        mock_conversation_repository,
        sample_question,
        sample_response,
    ):
        """Test that cached response is returned without calling agent."""
        mock_conversation_repository.get_cached_response.return_value = sample_response

        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )

        result = service.ask("user-123", sample_question, "2026-03-12")

        assert result == sample_response
        # Agent should NOT be called when cache hit
        mock_assistant_agent.answer.assert_not_called()
        # Cache check should be called
        mock_conversation_repository.get_cached_response.assert_called_once_with(
            sample_question
        )

    def test_ask_invokes_agent_on_cache_miss(
        self,
        mock_assistant_agent,
        mock_conversation_repository,
        sample_question,
        sample_response,
    ):
        """Test that agent is invoked when cache misses."""
        mock_conversation_repository.get_cached_response.return_value = None
        mock_assistant_agent.answer.return_value = sample_response

        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )

        result = service.ask("user-123", sample_question, "2026-03-12")

        assert result == sample_response
        # Agent should be called on cache miss
        mock_assistant_agent.answer.assert_called_once_with(sample_question)

    def test_ask_caches_response(
        self,
        mock_assistant_agent,
        mock_conversation_repository,
        sample_question,
        sample_response,
    ):
        """Test that response is cached after agent invokes."""
        mock_conversation_repository.get_cached_response.return_value = None
        mock_assistant_agent.answer.return_value = sample_response

        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )

        result = service.ask("user-123", sample_question, "2026-03-12")

        # Response should be cached
        mock_conversation_repository.cache_response.assert_called_once_with(
            sample_question, sample_response
        )

    def test_ask_checks_usage_before_processing(
        self, mock_assistant_agent, mock_conversation_repository, sample_question
    ):
        """Test that usage is checked before processing question."""
        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )

        service.ask("user-123", sample_question, "2026-03-12")

        # Usage should be checked first
        assert mock_conversation_repository.check_usage.call_count == 1
        call_args = mock_conversation_repository.check_usage.call_args
        assert call_args[1]["user_id"] == "user-123"
        assert call_args[1]["current_date"] == "2026-03-12"

    def test_ask_raises_on_rate_limit(
        self, mock_assistant_agent, mock_conversation_repository, sample_question
    ):
        """Test that RateLimitError is propagated."""
        mock_conversation_repository.check_usage.side_effect = RateLimitError()

        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )

        with pytest.raises(RateLimitError):
            service.ask("user-123", sample_question, "2026-03-12")

    def test_ask_updates_usage(
        self,
        mock_assistant_agent,
        mock_conversation_repository,
        sample_question,
        sample_response,
    ):
        """Test that usage is updated after response."""
        mock_conversation_repository.get_cached_response.return_value = None
        mock_assistant_agent.answer.return_value = sample_response

        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )

        service.ask("user-123", sample_question, "2026-03-12")

        # Usage should be updated
        mock_conversation_repository.update_usage.assert_called_once()
        call_args = mock_conversation_repository.update_usage.call_args
        assert call_args[1]["user_id"] == "user-123"
        assert call_args[1]["current_date"] == "2026-03-12"

    def test_ask_execution_order(
        self,
        mock_assistant_agent,
        mock_conversation_repository,
        sample_question,
        sample_response,
    ):
        """Test that operations are called in correct order."""
        mock_conversation_repository.get_cached_response.return_value = None
        mock_assistant_agent.answer.return_value = sample_response

        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )

        service.ask("user-123", sample_question, "2026-03-12")

        # Call order should be:
        # 1. check_usage
        # 2. get_cached_response
        # 3. agent.answer
        # 4. cache_response
        # 5. update_usage

        expected_calls = [
            call.check_usage(user_id="user-123", current_date="2026-03-12"),
            call.get_cached_response(sample_question),
            call.cache_response(sample_question, sample_response),
            call.update_usage(user_id="user-123", current_date="2026-03-12"),
        ]

        for exp_call in expected_calls:
            assert exp_call in mock_conversation_repository.method_calls

    def test_ask_with_default_request_id(
        self, mock_assistant_agent, mock_conversation_repository, sample_question
    ):
        """Test that request_id defaults to 'unknown'."""
        mock_conversation_repository.get_cached_response.return_value = "cached"

        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )

        # Call without providing request_id
        result = service.ask("user-123", sample_question, "2026-03-12")

        # Should still work - request_id defaults to "unknown"
        assert result == "cached"


class TestAssistantServiceInit:
    """Test AssistantService initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default dependencies."""
        service = AssistantService()
        assert service.agent is not None
        assert service.repository is not None

    def test_init_with_custom_agent(self, mock_assistant_agent):
        """Test initialization with custom agent."""
        service = AssistantService(assistant_agent=mock_assistant_agent)
        assert service.agent == mock_assistant_agent

    def test_init_with_custom_repository(self, mock_conversation_repository):
        """Test initialization with custom repository."""
        service = AssistantService(conversation_repository=mock_conversation_repository)
        assert service.repository == mock_conversation_repository

    def test_init_with_all_custom(
        self, mock_assistant_agent, mock_conversation_repository
    ):
        """Test initialization with all custom dependencies."""
        service = AssistantService(
            assistant_agent=mock_assistant_agent,
            conversation_repository=mock_conversation_repository,
        )
        assert service.agent == mock_assistant_agent
        assert service.repository == mock_conversation_repository
