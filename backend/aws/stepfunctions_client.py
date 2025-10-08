import json
import logging
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class StepFunctionsClient:
    """Step Functions client wrapper for Oratio platform"""

    def __init__(self, region_name: str = "us-east-1"):
        self.sfn_client = boto3.client("stepfunctions", region_name=region_name)
        self.region_name = region_name

    def start_execution(
        self,
        state_machine_arn: str,
        execution_name: str,
        input_data: Dict[str, Any],
    ) -> Optional[Dict]:
        """
        Start a Step Functions execution

        Args:
            state_machine_arn: ARN of the state machine
            execution_name: Name for this execution
            input_data: Input data for the execution

        Returns:
            Optional[Dict]: Execution details or None if failed
        """
        try:
            response = self.sfn_client.start_execution(
                stateMachineArn=state_machine_arn,
                name=execution_name,
                input=json.dumps(input_data),
            )

            execution_arn = response["executionArn"]
            logger.info(f"Successfully started execution: {execution_arn}")

            return {
                "executionArn": execution_arn,
                "startDate": response["startDate"].isoformat(),
            }

        except ClientError as e:
            logger.error(f"Failed to start execution: {e}")
            return None

    def describe_execution(self, execution_arn: str) -> Optional[Dict]:
        """
        Get details about a Step Functions execution

        Args:
            execution_arn: ARN of the execution

        Returns:
            Optional[Dict]: Execution details or None if failed
        """
        try:
            response = self.sfn_client.describe_execution(executionArn=execution_arn)

            return {
                "executionArn": response["executionArn"],
                "stateMachineArn": response["stateMachineArn"],
                "name": response["name"],
                "status": response["status"],
                "startDate": response["startDate"].isoformat(),
                "stopDate": (
                    response["stopDate"].isoformat() if "stopDate" in response else None
                ),
                "input": json.loads(response["input"]),
                "output": json.loads(response["output"]) if "output" in response else None,
            }

        except ClientError as e:
            logger.error(f"Failed to describe execution: {e}")
            return None

    def stop_execution(self, execution_arn: str, error: str = "User stopped", cause: str = "Manual stop") -> bool:
        """
        Stop a running Step Functions execution

        Args:
            execution_arn: ARN of the execution
            error: Error code
            cause: Cause of the stop

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.sfn_client.stop_execution(
                executionArn=execution_arn, error=error, cause=cause
            )
            logger.info(f"Successfully stopped execution: {execution_arn}")
            return True

        except ClientError as e:
            logger.error(f"Failed to stop execution: {e}")
            return False
