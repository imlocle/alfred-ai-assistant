import boto3
import json
import os
from botocore.config import Config
from shared.logging import get_logger

logger = get_logger(__name__)

# Cache S3 Client
_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-west-1")),
            config=Config(
                connect_timeout=5,
                read_timeout=10,
                retries={"max_attempts": 3}
            )
        )
    return _s3_client


class KnowledgeProvider:
    def __init__(self):
        self.client = get_s3_client()
        self.bucket_name = os.environ.get("KNOWLEDGE_BUCKET")

    def fetch_knowledge(self, file_key="knowledge_base.json"):
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=file_key)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except Exception as e:
            logger.error(
                "Failed to fetch knowledge base",
                extra={"bucket": self.bucket_name, "key": file_key, "error": str(e)}
            )
            raise Exception(f"Failed to load knowledge base from s3://{self.bucket_name}/{file_key}") from e
