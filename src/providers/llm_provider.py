from typing import Any, List, cast
import boto3
import json
import os
from botocore.config import Config
from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient
from shared.logging import get_logger

logger = get_logger(__name__)

# Cache Bedrock client
_bedrock_runtime_client: BedrockRuntimeClient | None = None


def get_bedrock_runtime_client() -> BedrockRuntimeClient:
    global _bedrock_runtime_client
    if _bedrock_runtime_client is None:
        _bedrock_runtime_client = cast(
            BedrockRuntimeClient,
            boto3.client(
                "bedrock-runtime",
                region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-1")),
                config=Config(
                    connect_timeout=3600, read_timeout=3600, retries={"max_attempts": 3}
                ),
            )
        )
    return _bedrock_runtime_client


class LLMProvider:
    def __init__(self):
        self.client = get_bedrock_runtime_client()
        model_id = os.environ.get("MODEL_ID")
        if not model_id:
            raise ValueError("MODEL_ID environment variable is required")
        self.model_id: str = model_id

    def invoke_model(
        self, system_blocks: List[dict[str, str]], messages: List[dict[str, Any]]
    ) -> str:
        payload = {
            "system": system_blocks,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 200,
                "temperature": 0.2,
                "topP": 0.9,
                "topK": 1,
                "stopSequences": [],
            },
        }

        try:
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )
            result = json.loads(response["body"].read())
            resp_messages = result.get("output", {}).get("message", {})
            if resp_messages:
                content = resp_messages.get("content", [])
                for block in content:
                    if "text" in block:
                        answer: str = block.get("text")
                        return answer
            return "Sorry, I don't have an answer."
        except Exception as e:
            logger.error("LLM invocation failed", extra={"error": str(e)}, exc_info=True)
            return "Sorry, Alfred is unavailable right now."

    def invoke_model_with_response_stream(
        self, system_blocks: List[dict[str, str]], messages: List[dict[str, Any]]
    ) -> str:
        payload = {
            "system": system_blocks,
            "messages": messages,
            "inferenceConfig": {
                "maxTokens": 200,
                "temperature": 0.2,
                "topP": 0.9,
                "topK": 1,
                "stopSequences": [],
            },
        }

        try:
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(payload),
            )
            
            accumulated_text = ""
            for event in response["body"]:
                if "chunk" in event:
                    chunk_bytes = event["chunk"]["bytes"]
                    chunk_data = json.loads(chunk_bytes.decode("utf-8"))
                    
                    # Handle content block delta
                    if "contentBlockDelta" in chunk_data:
                        delta = chunk_data["contentBlockDelta"].get("delta", {})
                        if "text" in delta:
                            accumulated_text += delta["text"]
            
            return accumulated_text if accumulated_text else "Sorry, I don't have an answer."
        except Exception as e:
            logger.error("LLM streaming invocation failed", extra={"error": str(e)}, exc_info=True)
            return "Sorry, Alfred is unavailable right now."
