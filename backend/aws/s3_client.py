import logging
from typing import BinaryIO, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Client:
    """S3 client wrapper with tagging support for Oratio platform"""

    def __init__(self, region_name: str = "us-east-1"):
        self.s3_client = boto3.client("s3", region_name=region_name)
        self.region_name = region_name

    def upload_file(
        self,
        file_obj: BinaryIO,
        bucket: str,
        key: str,
        user_id: str,
        agent_id: str,
        resource_type: str = "knowledge-base",
        content_type: Optional[str] = None,
    ) -> bool:
        """
        Upload a file to S3 with proper tagging

        Args:
            file_obj: File object to upload
            bucket: S3 bucket name
            key: S3 object key (path)
            user_id: User ID for tagging
            agent_id: Agent ID for tagging
            resource_type: Type of resource (knowledge-base, generated-code, recording)
            content_type: Content type of the file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Prepare tags
            tags = f"userId={user_id}&agentId={agent_id}&resourceType={resource_type}"

            # Prepare extra args
            extra_args = {"Tagging": tags}
            if content_type:
                extra_args["ContentType"] = content_type

            # Upload file
            self.s3_client.upload_fileobj(file_obj, bucket, key, ExtraArgs=extra_args)

            logger.info(f"Successfully uploaded file to s3://{bucket}/{key} with tags: {tags}")
            return True

        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            return False

    def upload_folder(
        self,
        files: List[tuple],  # List of (file_obj, relative_path) tuples
        bucket: str,
        base_key: str,
        user_id: str,
        agent_id: str,
        resource_type: str = "knowledge-base",
    ) -> Dict[str, bool]:
        """
        Upload multiple files to S3 with proper tagging

        Args:
            files: List of (file_obj, relative_path) tuples
            bucket: S3 bucket name
            base_key: Base S3 key (folder path)
            user_id: User ID for tagging
            agent_id: Agent ID for tagging
            resource_type: Type of resource

        Returns:
            Dict[str, bool]: Mapping of file paths to upload success status
        """
        results = {}

        for file_obj, relative_path in files:
            full_key = f"{base_key}/{relative_path}"
            success = self.upload_file(
                file_obj=file_obj,
                bucket=bucket,
                key=full_key,
                user_id=user_id,
                agent_id=agent_id,
                resource_type=resource_type,
            )
            results[relative_path] = success

        return results

    def get_file(self, bucket: str, key: str) -> Optional[bytes]:
        """
        Get a file from S3

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            Optional[bytes]: File content or None if not found
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                logger.warning(f"File not found: s3://{bucket}/{key}")
            else:
                logger.error(f"Failed to get file from S3: {e}")
            return None

    def file_exists(self, bucket: str, key: str) -> bool:
        """
        Check if a file exists in S3

        Args:
            bucket: S3 bucket name
            key: S3 object key

        Returns:
            bool: True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Failed to check file existence: {e}")
            return False

    def list_files(self, bucket: str, prefix: str) -> List[str]:
        """
        List files in S3 with a given prefix

        Args:
            bucket: S3 bucket name
            prefix: S3 key prefix

        Returns:
            List[str]: List of S3 keys
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

            if "Contents" not in response:
                return []

            return [obj["Key"] for obj in response["Contents"]]

        except ClientError as e:
            logger.error(f"Failed to list files from S3: {e}")
            return []

    def generate_presigned_url(
        self, bucket: str, key: str, expiration: int = 3600
    ) -> Optional[str]:
        """
        Generate a presigned URL for downloading a file

        Args:
            bucket: S3 bucket name
            key: S3 object key
            expiration: URL expiration time in seconds (default: 1 hour)

        Returns:
            Optional[str]: Presigned URL or None if failed
        """
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expiration
            )
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None
