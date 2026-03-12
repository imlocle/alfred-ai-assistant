import json
from datetime import datetime
from typing import Optional
from services.assistant_service import AssistantService
from shared.config import ALLOWED_ORIGINS
from shared.exceptions import CORSOriginError, InvalidQuestionError
from shared.validators import sanitize_question
from shared.logging import get_logger

logger = get_logger(__name__)


class QueryController:
    def __init__(self, assistant_service: Optional[AssistantService] = None):
        self.assistant_service = assistant_service or AssistantService()

    def handle_event(self, event, request_id: str = "unknown") -> str:
        headers = event.get("headers", {})
        origin = headers.get("origin", "")
        if origin not in ALLOWED_ORIGINS:
            raise CORSOriginError(origin=origin)

        user_id = headers.get("x-forwarded-for", "anonymous")
        time_epoch = (
            event.get("requestContext").get("timeEpoch") / 1000
        )  # Convert ms to s
        current_date = datetime.fromtimestamp(time_epoch).strftime("%Y-%m-%d")

        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        question: str = body.get("question", "")
        logger.info(
            "Question received",
            extra={"request_id": request_id, "user_id": user_id, "question_length": len(question)}
        )
        
        # Sanitize and validate question
        try:
            question = sanitize_question(question)
        except ValueError as e:
            logger.warning(
                "Question sanitization failed",
                extra={"request_id": request_id, "user_id": user_id, "error": str(e)}
            )
            raise InvalidQuestionError(question=question)

        answer = self.assistant_service.ask(user_id, question, current_date, request_id)
        logger.info(
            "Answer generated",
            extra={"request_id": request_id, "user_id": user_id, "answer_length": len(answer)}
        )

        return answer
