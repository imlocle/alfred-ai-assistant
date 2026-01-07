from repositories.inference_repository import InferenceRepository


class InferenceService:
    def __init__(
        self,
        chatbot_repository: InferenceRepository = None,
    ):
        self.chatbot_repository = chatbot_repository or InferenceRepository()

    def ask(self, user_id: str, question: str, current_date: str) -> str:
        self.chatbot_repository.check_usage(user_id=user_id, current_date=current_date)
        response = self.chatbot_repository.ask(question=question)
        self.chatbot_repository.update_usage(user_id=user_id, current_date=current_date)
        return response
