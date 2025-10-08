import logging
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class DynamoDBClient:
    """DynamoDB client wrapper for Oratio platform"""

    def __init__(self, region_name: str = "us-east-1"):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.region_name = region_name

    def put_item(self, table_name: str, item: Dict[str, Any]) -> bool:
        """
        Put an item into DynamoDB table

        Args:
            table_name: Name of the DynamoDB table
            item: Item to put

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            table = self.dynamodb.Table(table_name)
            table.put_item(Item=item)
            logger.info(f"Successfully put item into {table_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to put item into {table_name}: {e}")
            return False

    def get_item(
        self, table_name: str, key: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get an item from DynamoDB table

        Args:
            table_name: Name of the DynamoDB table
            key: Primary key of the item

        Returns:
            Optional[Dict[str, Any]]: Item or None if not found
        """
        try:
            table = self.dynamodb.Table(table_name)
            response = table.get_item(Key=key)
            return response.get("Item")

        except ClientError as e:
            logger.error(f"Failed to get item from {table_name}: {e}")
            return None

    def query_by_partition_key(
        self,
        table_name: str,
        partition_key_name: str,
        partition_key_value: Any,
        sort_key_condition: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items by partition key

        Args:
            table_name: Name of the DynamoDB table
            partition_key_name: Name of the partition key
            partition_key_value: Value of the partition key
            sort_key_condition: Optional sort key condition

        Returns:
            List[Dict[str, Any]]: List of items
        """
        try:
            table = self.dynamodb.Table(table_name)

            # Build key condition expression
            from boto3.dynamodb.conditions import Key

            key_condition = Key(partition_key_name).eq(partition_key_value)

            if sort_key_condition:
                # Add sort key condition if provided
                # Example: {'name': 'timestamp', 'operator': 'gt', 'value': 123456}
                sort_key_name = sort_key_condition["name"]
                operator = sort_key_condition["operator"]
                value = sort_key_condition["value"]

                if operator == "eq":
                    key_condition = key_condition & Key(sort_key_name).eq(value)
                elif operator == "gt":
                    key_condition = key_condition & Key(sort_key_name).gt(value)
                elif operator == "lt":
                    key_condition = key_condition & Key(sort_key_name).lt(value)
                elif operator == "between":
                    key_condition = key_condition & Key(sort_key_name).between(
                        value[0], value[1]
                    )

            response = table.query(KeyConditionExpression=key_condition)
            return response.get("Items", [])

        except ClientError as e:
            logger.error(f"Failed to query {table_name}: {e}")
            return []

    def query_by_gsi(
        self,
        table_name: str,
        index_name: str,
        partition_key_name: str,
        partition_key_value: Any,
        sort_key_condition: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query items using a Global Secondary Index

        Args:
            table_name: Name of the DynamoDB table
            index_name: Name of the GSI
            partition_key_name: Name of the partition key in GSI
            partition_key_value: Value of the partition key
            sort_key_condition: Optional sort key condition

        Returns:
            List[Dict[str, Any]]: List of items
        """
        try:
            table = self.dynamodb.Table(table_name)

            from boto3.dynamodb.conditions import Key

            key_condition = Key(partition_key_name).eq(partition_key_value)

            if sort_key_condition:
                sort_key_name = sort_key_condition["name"]
                operator = sort_key_condition["operator"]
                value = sort_key_condition["value"]

                if operator == "eq":
                    key_condition = key_condition & Key(sort_key_name).eq(value)
                elif operator == "gt":
                    key_condition = key_condition & Key(sort_key_name).gt(value)
                elif operator == "lt":
                    key_condition = key_condition & Key(sort_key_name).lt(value)

            response = table.query(
                IndexName=index_name, KeyConditionExpression=key_condition
            )
            return response.get("Items", [])

        except ClientError as e:
            logger.error(f"Failed to query {table_name} using GSI {index_name}: {e}")
            return []

    def update_item(
        self,
        table_name: str,
        key: Dict[str, Any],
        updates: Dict[str, Any],
    ) -> bool:
        """
        Update an item in DynamoDB table

        Args:
            table_name: Name of the DynamoDB table
            key: Primary key of the item
            updates: Dictionary of attributes to update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            table = self.dynamodb.Table(table_name)

            # Build update expression
            update_expression = "SET " + ", ".join(
                [f"#{k} = :{k}" for k in updates.keys()]
            )
            expression_attribute_names = {f"#{k}": k for k in updates.keys()}
            expression_attribute_values = {f":{k}": v for k, v in updates.items()}

            table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
            )

            logger.info(f"Successfully updated item in {table_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to update item in {table_name}: {e}")
            return False

    def delete_item(self, table_name: str, key: Dict[str, Any]) -> bool:
        """
        Delete an item from DynamoDB table

        Args:
            table_name: Name of the DynamoDB table
            key: Primary key of the item

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            table = self.dynamodb.Table(table_name)
            table.delete_item(Key=key)
            logger.info(f"Successfully deleted item from {table_name}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete item from {table_name}: {e}")
            return False
