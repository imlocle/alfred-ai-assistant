from typing import Optional
from agents.assistant_agent import AssistantAgent
from repositories.conversation_repository import ConversationRepository


class AssistantService:
    def __init__(
        self,
        assistant_agent: Optional[AssistantAgent] = None,
        conversation_repository: Optional[ConversationRepository] = None,
    ):
        self.agent = assistant_agent or AssistantAgent()
        self.repository = conversation_repository or ConversationRepository()

    def ask(self, user_id: str, question: str, current_date: str, request_id: str = "unknown") -> str:
        self.repository.check_usage(user_id=user_id, current_date=current_date)

        # Check cache first
        cached = self.repository.get_cached_response(question)
        if cached:
            return cached

        # Agent handles AI logic
        response = self.agent.answer(question)

        # Cache the response
        self.repository.cache_response(question, response)

        self.repository.update_usage(user_id=user_id, current_date=current_date)
        return response
