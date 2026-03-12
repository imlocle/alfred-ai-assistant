"""Unit tests for validators module."""

import pytest
from shared.validators import sanitize_question


class TestSanitizeQuestion:
    """Test question sanitization."""

    def test_sanitize_valid_question(self):
        """Test sanitizing a valid question."""
        question = "What is your experience with AWS?"
        result = sanitize_question(question)
        assert result == "What is your experience with AWS?"

    def test_sanitize_question_with_extra_whitespace(self):
        """Test sanitizing question with extra whitespace."""
        question = "  What   is   your   experience?  "
        result = sanitize_question(question)
        assert result == "What is your experience?"
        assert result.count("  ") == 0  # No double spaces

    def test_sanitize_question_with_control_characters(self):
        """Test sanitizing question with control characters."""
        question = "What\x00is\x01your\x02experience?"
        result = sanitize_question(question)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result

    def test_sanitize_question_with_newlines(self):
        """Test sanitizing question with newlines."""
        question = "What is your\nexperience\nwith AWS?"
        result = sanitize_question(question)
        assert "\n" not in result
        assert result == "What is your experience with AWS?"

    def test_sanitize_empty_question_raises_error(self):
        """Test that empty question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            sanitize_question("")

    def test_sanitize_whitespace_only_raises_error(self):
        """Test that whitespace-only question raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            sanitize_question("   \n   \t   ")

    def test_sanitize_question_length_limit(self, monkeypatch):
        """Test that question length is limited."""
        monkeypatch.setattr("shared.validators.MAX_QUESTION_LENGTH", 50)
        long_question = "a" * 100
        result = sanitize_question(long_question)
        assert len(result) == 50

    def test_sanitize_none_raises_error(self):
        """Test that None raises ValueError."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            sanitize_question(None)

    def test_sanitize_unicode_question(self):
        """Test sanitizing unicode characters."""
        question = "Qu'est-ce que vous faites? 你做什么?"
        result = sanitize_question(question)
        assert "que vous" in result  # Unicode preserved
