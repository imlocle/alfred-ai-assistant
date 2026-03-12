"""Unit tests for the conversation repository."""

import pytest
import hashlib
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from repositories.conversation_repository import ConversationRepository
from shared.exceptions import RateLimitError
from shared.config import CACHE_TTL_SECONDS, RATE_LIMIT_MAX_REQUESTS


class TestConversationRepositoryCache:
    """Test caching functionality."""

    def test_cache_response(self, mock_dynamodb):
        """Test caching a response."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)
        question = "What is your experience?"
        response = "I am a Senior Cloud Engineer."

        repo.cache_response(question, response)

        # Verify cache entry exists
        cache_key = repo._get_cache_key(question)
        cached_response = repo.get_cached_response(question)

        assert cached_response == response

    def test_get_cached_response_hit(self, mock_dynamodb):
        """Test retrieving a cached response (cache hit)."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)
        question = "What is your experience?"
        response = "I am a Senior Cloud Engineer."

        repo.cache_response(question, response)
        cached = repo.get_cached_response(question)

        assert cached == response

    def test_get_cached_response_miss(self, mock_dynamodb):
        """Test retrieving non-existent cached response (cache miss)."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)

        cached = repo.get_cached_response("Non-existent question")

        assert cached is None

    def test_cache_key_normalization(self, mock_dynamodb):
        """Test that cache keys are normalized."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)

        # These should produce same cache key
        key1 = repo._get_cache_key("What is your experience?")
        key2 = repo._get_cache_key("  WHAT IS YOUR EXPERIENCE?  ")

        assert key1 == key2  # Normalized (lowercase, stripped)

    def test_cache_expiration(self, mock_dynamodb, monkeypatch):
        """Test cache TTL expiration."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)
        repo.cache_ttl = 2  # 2 seconds TTL

        # Add to cache
        cache_key = repo._get_cache_key("Test question")
        repo.cache[cache_key] = (
            "response",
            datetime.now().timestamp() - 3,
        )  # 3 seconds old

        # Should be expired
        cached = repo._get_from_cache(cache_key)

        assert cached is None  # Expired

    def test_get_cache_key_produces_md5_hash(self, mock_dynamodb):
        """Test that cache key is MD5 hash of normalized question."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)
        question = "What is your experience?"

        cache_key = repo._get_cache_key(question)
        expected_key = hashlib.md5(question.lower().strip().encode()).hexdigest()

        assert cache_key == expected_key


class TestConversationRepositoryUsageTracking:
    """Test usage tracking functionality."""

    def test_check_usage_within_limit(self, mock_dynamodb):
        """Test that check_usage passes when under limit."""
        mock_dynamodb.get.return_value = {"count": 5}

        repo = ConversationRepository(storage_provider=mock_dynamodb)
        # With RATE_LIMIT_MAX_REQUESTS=50, count of 5 should pass

        # Should not raise
        repo.check_usage("user-123", "2026-03-12")

    def test_check_usage_at_limit_raises(self, mock_dynamodb, monkeypatch):
        """Test that check_usage raises when at limit."""
        monkeypatch.setattr("shared.config.RATE_LIMIT_MAX_REQUESTS", 50)
        mock_dynamodb.get.return_value = {"count": 50}

        repo = ConversationRepository(storage_provider=mock_dynamodb)

        with pytest.raises(RateLimitError):
            repo.check_usage("user-123", "2026-03-12")

    def test_check_usage_over_limit_raises(self, mock_dynamodb, monkeypatch):
        """Test that check_usage raises when over limit."""
        monkeypatch.setattr("shared.config.RATE_LIMIT_MAX_REQUESTS", 50)
        mock_dynamodb.get.return_value = {"count": 51}

        repo = ConversationRepository(storage_provider=mock_dynamodb)

        with pytest.raises(RateLimitError):
            repo.check_usage("user-123", "2026-03-12")

    def test_check_usage_calls_storage_get(self, mock_dynamodb):
        """Test that check_usage calls storage provider's get method."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)

        repo.check_usage("user-123", "2026-03-12")

        mock_dynamodb.get.assert_called_once()
        call_args = mock_dynamodb.get.call_args[0][0]
        assert call_args["Key"]["pk"] == "user-123"
        assert call_args["Key"]["sk"] == "2026-03-12"

    def test_update_usage_increments_count(self, mock_dynamodb):
        """Test that update_usage increments request count."""
        mock_dynamodb.update.return_value = {"count": 6}

        repo = ConversationRepository(storage_provider=mock_dynamodb)

        repo.update_usage("user-123", "2026-03-12")

        mock_dynamodb.update.assert_called_once()
        call_args = mock_dynamodb.update.call_args[0][0]
        assert call_args["Key"]["pk"] == "user-123"
        assert call_args["Key"]["sk"] == "2026-03-12"
        assert ":inc" in call_args["ExpressionAttributeValues"]
        assert call_args["ExpressionAttributeValues"][":inc"] == 1

    def test_update_usage_sets_ttl(self, mock_dynamodb):
        """Test that update_usage sets TTL for expiration."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)

        repo.update_usage("user-123", "2026-03-12")

        call_args = mock_dynamodb.update.call_args[0][0]
        # Should have :expires_at in expression
        assert ":expires_at" in call_args["ExpressionAttributeValues"]
        expires_at = call_args["ExpressionAttributeValues"][":expires_at"]
        # Should be approximately 1 day from now
        assert isinstance(expires_at, int)

    def test_update_usage_handles_errors(self, mock_dynamodb):
        """Test that update_usage handles errors gracefully."""
        mock_dynamodb.update.side_effect = Exception("DynamoDB error")

        repo = ConversationRepository(storage_provider=mock_dynamodb)

        # Should not raise, just log
        repo.update_usage("user-123", "2026-03-12")


class TestConversationRepositoryInit:
    """Test repository initialization."""

    def test_init_with_table_name_from_env(self, monkeypatch, mock_dynamodb):
        """Test initialization with table name from environment."""
        monkeypatch.setenv("USAGE_TRACKER_TABLE", "test-table")

        repo = ConversationRepository(storage_provider=mock_dynamodb)

        assert repo.table_name == "test-table"

    def test_init_with_default_storage_provider(self, monkeypatch):
        """Test initialization creates default StorageProvider."""
        monkeypatch.setenv("USAGE_TRACKER_TABLE", "test-table")

        with patch("repositories.conversation_repository.StorageProvider") as mock_sp:
            repo = ConversationRepository()
            mock_sp.assert_called_once()

    def test_init_sets_cache_ttl(self, mock_dynamodb, monkeypatch):
        """Test that cache TTL is set from config."""
        # Patch where it's imported, not where it's defined
        monkeypatch.setattr(
            "repositories.conversation_repository.CACHE_TTL_SECONDS", 7200
        )  # 2 hours

        repo = ConversationRepository(storage_provider=mock_dynamodb)

        # After patching, the TTL should match the config
        assert repo.cache_ttl == 7200


class TestConversationRepositoryInternal:
    """Test internal helper methods."""

    def test_get_cache_key_lowercase(self, mock_dynamodb):
        """Test that cache key is lowercase."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)

        key = repo._get_cache_key("UPPERCASE QUESTION")
        expected = hashlib.md5("uppercase question".encode()).hexdigest()

        assert key == expected

    def test_get_cache_key_stripped(self, mock_dynamodb):
        """Test that cache key strips whitespace."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)

        key = repo._get_cache_key("  question with spaces  ")
        expected = hashlib.md5("question with spaces".encode()).hexdigest()

        assert key == expected

    def test_add_to_cache_stores_timestamp(self, mock_dynamodb):
        """Test that add_to_cache stores timestamp."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)

        cache_key = "test-key"
        repo._add_to_cache(cache_key, "response")

        assert cache_key in repo.cache
        response, timestamp = repo.cache[cache_key]
        assert response == "response"
        assert isinstance(timestamp, float)

    def test_get_from_cache_valid(self, mock_dynamodb):
        """Test retrieving valid (non-expired) cache entry."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)
        repo.cache_ttl = 3600  # 1 hour

        cache_key = "test-key"
        repo._add_to_cache(cache_key, "response")

        result = repo._get_from_cache(cache_key)

        assert result == "response"

    def test_get_from_cache_cleans_expired(self, mock_dynamodb):
        """Test that expired entries are cleaned up."""
        repo = ConversationRepository(storage_provider=mock_dynamodb)
        repo.cache_ttl = 1  # 1 second

        cache_key = "test-key"
        # Add entry with old timestamp (expired)
        repo.cache[cache_key] = ("response", datetime.now().timestamp() - 10)

        result = repo._get_from_cache(cache_key)

        assert result is None
        # Entry should be deleted
        assert cache_key not in repo.cache
