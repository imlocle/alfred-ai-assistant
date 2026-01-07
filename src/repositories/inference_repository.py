import os
from datetime import datetime, timedelta
import re
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
        self.knowledge = self.s3_service.fetch_knowledge()

    def ask(self, question: str) -> str:
        if re.search(r"(schedule|book|meeting|call|appointment)", question):
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
            "ConditionExpression": "attribute_not_exists(pk) OR attribute_exists(sk)",
        }
        self.dynamodb_service.update(update_params)
