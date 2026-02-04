from typing import Any, List
import boto3
import json
import os
from botocore.config import Config
from mypy_boto3_bedrock_runtime.client import BedrockRuntimeClient

# Cache Bedrock client
_bedrock_runtime_client: BedrockRuntimeClient | None = None


def get_bedrock_runtime_client() -> BedrockRuntimeClient:
    global _bedrock_runtime_client
    if _bedrock_runtime_client is None:
        _bedrock_runtime_client = boto3.client(
            "bedrock-runtime",
            region_name=os.environ.get("AWS_REGION"),
            config=Config(
                connect_timeout=3600, read_timeout=3600, retries={"max_attempts": 3}
            ),
        )
    return _bedrock_runtime_client


class BedrockService:
    def __init__(self):
        self.client = get_bedrock_runtime_client()
        self.model_id = os.environ.get("MODEL_ID")

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
            # print(f"Usage: {result.get('usage')}")
            resp_messages = result.get("output", {}).get("message", {})
            if resp_messages:
                content = resp_messages.get("content", [])
                for block in content:
                    if "text" in block:
                        answer: str = block.get("text")
                        return answer
            return "Sorry, I don't have an answer."
        except Exception as e:
            print(f"[BedrockService] Error: {e}")
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
            result = response["body"]
            print(result)
            for event in response["body"]:
                if "chunk" in event:
                    # Raw bytes from the stream
                    chunk_bytes = event["chunk"]["bytes"]

                    # Decode to string
                    text = chunk_bytes.decode("utf-8")
                    print(text, end="", flush=True)

            resp_messages = result.get("output", {}).get("message", {})
            if resp_messages:
                content = resp_messages.get("content", [])
                for block in content:
                    if "text" in block:
                        return block["text"]
            return "I'm sorry, I don't have an answer."
        except Exception as e:
            print(f"[BedrockService] Error: {e}")
            return "Sorry, Alfred is unavailable right now."
