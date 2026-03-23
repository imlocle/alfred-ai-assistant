from .base_handler import BaseHandler, lambda_handler_with_errors
from controllers.query_controller import QueryController
from shared.responses import success_response
from shared.logging import get_logger

logger = get_logger(__name__)


class AssistantHandler(BaseHandler):
    """Handle assistant queries with automatic error handling via decorator."""

    def __init__(self, event, context):
        super().__init__(event)
        self.controller = QueryController()
        self.lambda_context = context

    def handler(self):
        """Process the assistant query."""
        request_id = self.event.get("requestContext", {}).get("requestId", "unknown")
        logger.info("Processing request", extra={"request_id": request_id})

        result: str = self.controller.handle_event(self.event, request_id)
        logger.info("Request completed successfully", extra={"request_id": request_id})

        return success_response(body={"reply": result})


@lambda_handler_with_errors("process_query")
def lambda_handler(event, context):
    """Lambda handler entry point with automatic error handling."""
    return AssistantHandler(event, context).handler()
