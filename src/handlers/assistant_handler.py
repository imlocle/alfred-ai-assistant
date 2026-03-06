from controllers.query_controller import QueryController
from shared.exceptions import (
    InvalidQuestionError,
    ChatbotProcessingError,
    CORSOriginError,
    RateLimitError,
)
from shared.responses import error_response, success_response
from shared.logging import get_logger

logger = get_logger(__name__)


class AssistantHandler:
    def __init__(self):
        self.controller = QueryController()

    def handler(self, event, context):
        # Extract request ID for correlation
        request_id = event.get("requestContext", {}).get("requestId", "unknown")
        
        try:
            logger.info("Processing request", extra={"request_id": request_id})
            result: str = self.controller.handle_event(event, request_id)
            logger.info("Request completed successfully", extra={"request_id": request_id})
            return success_response(body={"reply": result})
        except InvalidQuestionError as e:
            logger.warning(
                "Invalid question error",
                extra={"request_id": request_id, "error": str(e)}
            )
            return error_response(
                message="I am sorry, but that was an invalid question. Please ask another.",
                headers=e.headers,
                status_code=e.http_status,
            )
        except CORSOriginError as e:
            logger.warning(
                "CORS origin error",
                extra={"request_id": request_id, "origin": e.origin}
            )
            return error_response(
                message="I am sorry, but you are chatting with me from a different place. Please continue this conversation through Loc's website.",
                headers=e.headers,
                status_code=e.http_status,
            )
        except RateLimitError as e:
            logger.warning(
                "Rate limit exceeded",
                extra={"request_id": request_id}
            )
            return error_response(
                message="I apologize, but you have reached the limit for today. Please come back tomorrow.",
                headers=e.headers,
                status_code=e.http_status,
            )
        except Exception as e:
            error = ChatbotProcessingError(details=str(e))
            logger.error(
                "Unexpected error processing request",
                extra={"request_id": request_id, "error": str(e)},
                exc_info=True
            )
            return error_response(
                message="My apologies, I am currently unavailable. Please come back soon.",
                headers=error.headers,
                status_code=error.http_status,
            )


def lambda_handler(event, context):
    return AssistantHandler().handler(event, context)
