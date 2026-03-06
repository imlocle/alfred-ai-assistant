import os
from datetime import datetime, timedelta
from aws.bedrock_service import BedrockService
from aws.dynamodb_service import DynamodbService
from mypy_boto3_dynamodb.type_defs import (
    GetItemInputTableGetItemTypeDef,
    UpdateItemInputTableUpdateItemTypeDef,
)

from aws.s3_service import S3Service
from utils.constants import ALFRED_SYSTEM_PROMPT, CALENDLY_URL
from utils.errors import RateLimitError


class InferenceRepository:
    def __init__(self, bedrock_service=None, dynamodb_service=None, s3_service=None):
        self.table_name = os.getenv("ALFRED_USAGE_TRACKER_TABLE")
        self.bedrock_service = bedrock_service or BedrockService()
        self.dynamodb_service = dynamodb_service or DynamodbService(
            table_name=self.table_name
        )
        self.s3_service = s3_service or S3Service()
        try:
            self.knowledge = self.s3_service.fetch_knowledge()
        except Exception as e:
            print(f"[ERROR] Failed to load knowledge base: {e}")
            self.knowledge = {}

    def ask(self, question: str) -> str:
        keywords = ["schedule", "book", "meeting", "call", "appointment"]
        if any(keyword in question.lower() for keyword in keywords):
            return f"You can schedule a meeting with Loc here: [Book a time with Loc on Calendly]({CALENDLY_URL})"

        system_blocks = [
            {"text": ALFRED_SYSTEM_PROMPT},
            {"text": f"Knowledge Base:\n{self.knowledge}"},
        ]
        messages = [{"role": "user", "content": [{"text": question}]}]
        return self.bedrock_service.invoke_model(system_blocks, messages)

    def check_usage(self, user_id: str, current_date: str) -> None:
        get_params: GetItemInputTableGetItemTypeDef = {
            "Key": {"pk": user_id, "sk": current_date}
        }
        response = self.dynamodb_service.get(get_params)

        count: int = response.get("count", 0)
        if count >= 50:
            print(f"[RATE_LIMIT] User {user_id} exceeded limit: {count}/50 on {current_date}")
            raise RateLimitError()

    def update_usage(self, user_id: str, current_date: str) -> None:
        update_params: UpdateItemInputTableUpdateItemTypeDef = {
            "Key": {"pk": user_id, "sk": current_date},
            "UpdateExpression": "SET #count = if_not_exists(#count, :start) + :inc, #expires_at = :expires_at",
            "ExpressionAttributeNames": {
                "#count": "count",
                "#expires_at": "expires_at",
            },
            "ExpressionAttributeValues": {
                ":start": 0,
                ":inc": 1,
                ":expires_at": int((datetime.now() + timedelta(days=1)).timestamp()),
            },
            "ReturnValues": "ALL_NEW",
        }
        try:
            result = self.dynamodb_service.update(update_params)
            if not result:
                print(f"[WARNING] Usage update returned no result for user {user_id}")
        except Exception as e:
            print(f"[ERROR] Failed to update usage for user {user_id}: {e}")
            # Don't raise - allow request to proceed even if tracking fails
