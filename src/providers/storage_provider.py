from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource
from mypy_boto3_dynamodb.type_defs import (
    ScanInputTableScanTypeDef,
    GetItemInputTableGetItemTypeDef,
    PutItemInputTablePutItemTypeDef,
    UpdateItemInputTableUpdateItemTypeDef,
    QueryInputTableQueryTypeDef,
    DeleteItemInputTableDeleteItemTypeDef,
)
from typing import Any, Dict, List, Optional, cast
import boto3
from botocore.exceptions import ClientError


def get_dynamodb_resource() -> DynamoDBServiceResource:
    return cast(DynamoDBServiceResource, boto3.resource("dynamodb"))


class StorageProvider:
    def __init__(self, table_name):
        self.ddb_resource = get_dynamodb_resource()
        self.Table = self.ddb_resource.Table(table_name)

    @staticmethod
    def _enhance_request(
        request: dict[str, Any], default: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        if default is None:
            default = {}
        return default | request

    def batch_get(self, request: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            response = self.ddb_resource.batch_get_item(**request)
        except ClientError as err:
            raise

        items = []

        for table_name, table_items in response.get("Responses", {}).items():
            items.extend(table_items)

        return items

    def get(self, request: GetItemInputTableGetItemTypeDef) -> dict:
        get_request = self._enhance_request(dict(request), {"ReturnConsumedCapacity": "NONE"})
        try:
            response = self.Table.get_item(**get_request)
        except ClientError as err:
            raise
        else:
            return response.get("Item", {})

    def put(
        self, request: PutItemInputTablePutItemTypeDef
    ) -> Optional[Dict[str, Any]]:
        response = self.Table.put_item(**request)
        return cast(Optional[Dict[str, Any]], response.get("ResponseMetadata", None))

    def update(
        self, request: UpdateItemInputTableUpdateItemTypeDef
    ) -> Optional[Dict[str, Any]]:
        response = self.Table.update_item(**request)
        return cast(Optional[Dict[str, Any]], response.get("ResponseMetadata", None))

    def query(
        self, request: QueryInputTableQueryTypeDef
    ) -> Dict[str, Any]:
        response = self.Table.query(**request)
        return {
            "items": response.get("Items", []),
            "lastEvaluatedKey": response.get("LastEvaluatedKey", None),
        }

    def scan(
        self, request: ScanInputTableScanTypeDef
    ) -> Dict[str, Any]:
        response = self.Table.scan(**request)
        return {
            "items": response.get("Items", []),
            "lastEvaluatedKey": response.get("LastEvaluatedKey", None),
        }

    def delete(
        self, request: DeleteItemInputTableDeleteItemTypeDef
    ) -> Dict[str, Any]:
        response = self.Table.delete_item(**request)
        return cast(Dict[str, Any], response)
