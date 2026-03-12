import re
from shared.config import MAX_QUESTION_LENGTH


def sanitize_question(question: str) -> str:
    """
    Sanitize user input to prevent prompt injection and normalize content.
    
    Args:
        question: Raw user input question
        
    Returns:
        Sanitized question string
        
    Raises:
        ValueError: If question is empty after sanitization
    """
    if not question:
        raise ValueError("Question cannot be empty")
    
    # Remove control characters (except newlines and tabs which we'll normalize)
    question = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', question)
    
    # Normalize whitespace (convert tabs, multiple spaces, newlines to single space)
    question = ' '.join(question.split())
    
    # Strip leading/trailing whitespace
    question = question.strip()
    
    # Limit length
    if len(question) > MAX_QUESTION_LENGTH:
        question = question[:MAX_QUESTION_LENGTH]
    
    # Final check
    if not question:
        raise ValueError("Question cannot be empty after sanitization")
    
    return question
