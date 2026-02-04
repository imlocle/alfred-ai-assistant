from repositories.inference_repository import InferenceRepository


class InferenceService:
    def __init__(
        self,
        inference_repository: InferenceRepository = None,
    ):
        self.inference_repository = inference_repository or InferenceRepository()

    def ask(self, user_id: str, question: str, current_date: str) -> str:
        self.inference_repository.check_usage(
            user_id=user_id, current_date=current_date
        )
        response = self.inference_repository.ask(question=question)
        self.inference_repository.update_usage(
            user_id=user_id, current_date=current_date
        )
        return response
