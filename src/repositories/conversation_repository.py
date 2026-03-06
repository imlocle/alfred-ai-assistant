import os
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import hashlib
from providers.storage_provider import StorageProvider
from mypy_boto3_dynamodb.type_defs import (
    GetItemInputTableGetItemTypeDef,
    UpdateItemInputTableUpdateItemTypeDef,
)
from shared.config import CACHE_TTL_SECONDS, RATE_LIMIT_MAX_REQUESTS
from shared.exceptions import RateLimitError
from shared.logging import get_logger

logger = get_logger(__name__)


class ConversationRepository:
    """Data access: caching and usage tracking via DynamoDB."""

    def __init__(self, storage_provider: Optional[StorageProvider] = None):
        self.table_name = os.getenv("USAGE_TRACKER_TABLE")
        self.storage_provider = storage_provider or StorageProvider(
            table_name=self.table_name
        )
        self.cache: Dict[str, Tuple[str, float]] = {}
        self.cache_ttl = CACHE_TTL_SECONDS

    # --- Caching ---

    def get_cached_response(self, question: str) -> Optional[str]:
        cache_key = self._get_cache_key(question)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.info("Cache hit", extra={"cache_key": cache_key[:16]})
        return cached

    def cache_response(self, question: str, response: str) -> None:
        cache_key = self._get_cache_key(question)
        self._add_to_cache(cache_key, response)

    def _get_cache_key(self, question: str) -> str:
        normalized = question.lower().strip()
        return hashlib.md5(normalized.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        if cache_key in self.cache:
            response, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return response
            else:
                del self.cache[cache_key]
        return None

    def _add_to_cache(self, cache_key: str, response: str) -> None:
        self.cache[cache_key] = (response, datetime.now().timestamp())

    # --- Usage tracking ---

    def check_usage(self, user_id: str, current_date: str) -> None:
        get_params: GetItemInputTableGetItemTypeDef = {
            "Key": {"pk": user_id, "sk": current_date}
        }
        response = self.storage_provider.get(get_params)

        count: int = response.get("count", 0)
        if count >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(
                "Rate limit exceeded",
                extra={"user_id": user_id, "count": count, "limit": RATE_LIMIT_MAX_REQUESTS, "date": current_date}
            )
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
            result = self.storage_provider.update(update_params)
            if not result:
                logger.warning("Usage update returned no result", extra={"user_id": user_id})
        except Exception as e:
            logger.error("Failed to update usage", extra={"user_id": user_id, "error": str(e)})
