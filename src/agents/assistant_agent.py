from typing import Dict, List, Optional
from providers.llm_provider import LLMProvider
from providers.knowledge_provider import KnowledgeProvider
from shared.config import ALFRED_SYSTEM_PROMPT, CALENDLY_URL
from shared.logging import get_logger

logger = get_logger(__name__)

SCHEDULING_KEYWORDS = ["schedule", "book", "meeting", "call", "appointment"]


class AssistantAgent:
    """Core AI logic: prompt construction, knowledge injection, and response routing."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None, knowledge_provider: Optional[KnowledgeProvider] = None):
        self.llm_provider = llm_provider or LLMProvider()
        self.knowledge_provider = knowledge_provider or KnowledgeProvider()
        try:
            self.knowledge = self.knowledge_provider.fetch_knowledge()
        except Exception as e:
            logger.error("Failed to load knowledge base", extra={"error": str(e)})
            self.knowledge = {}

    def answer(self, question: str) -> str:
        """Route the question and generate a response."""
        if self._is_scheduling_request(question):
            return f"You can schedule a meeting with Loc here: [Book a time with Loc on Calendly]({CALENDLY_URL})"

        system_blocks = self._build_system_context()
        messages = [{"role": "user", "content": [{"text": question}]}]
        return self.llm_provider.invoke_model(system_blocks, messages)

    def _is_scheduling_request(self, question: str) -> bool:
        return any(kw in question.lower() for kw in SCHEDULING_KEYWORDS)

    def _build_system_context(self) -> List[Dict[str, str]]:
        return [
            {"text": ALFRED_SYSTEM_PROMPT},
            {"text": f"Knowledge Base:\n{self.knowledge}"},
        ]
