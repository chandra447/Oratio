import logging
from typing import BinaryIO, Dict, List, Tuple

from aws.s3_client import S3Client

logger = logging.getLogger(__name__)


class S3Service:
    """Service for managing S3 file operations"""

    def __init__(self, s3_client: S3Client, kb_bucket: str = "oratio-knowledge-bases"):
        self.s3 = s3_client
        self.kb_bucket = kb_bucket

    def upload_knowledge_base_files(
        self,
        files: List[Tuple[BinaryIO, str, str]],  # (file_obj, filename, content_type)
        user_id: str,
        agent_id: str,
    ) -> Dict[str, bool]:
        """
        Upload knowledge base files to S3 with proper tagging

        Args:
            files: List of (file_obj, filename, content_type) tuples
            user_id: User ID for tagging and path
            agent_id: Agent ID for tagging and path

        Returns:
            Dict[str, bool]: Mapping of filenames to upload success status
        """
        results = {}
        base_path = f"{user_id}/{agent_id}"

        for file_obj, filename, content_type in files:
            # Construct S3 key
            s3_key = f"{base_path}/{filename}"

            # Upload file with tags
            success = self.s3.upload_file(
                file_obj=file_obj,
                bucket=self.kb_bucket,
                key=s3_key,
                user_id=user_id,
                agent_id=agent_id,
                resource_type="knowledge-base",
                content_type=content_type,
            )

            results[filename] = success

            if success:
                logger.info(f"Uploaded {filename} to s3://{self.kb_bucket}/{s3_key}")
            else:
                logger.error(f"Failed to upload {filename}")

        return results

    def generate_folder_structure(
        self, files: List[Tuple[str, str]]  # (filename, description)
    ) -> Dict[str, str]:
        """
        Generate folder/file description structure

        Args:
            files: List of (filename, description) tuples

        Returns:
            Dict[str, str]: Mapping of file paths to descriptions
        """
        folder_structure = {}

        for filename, description in files:
            # Handle folder paths (e.g., "folder/subfolder/file.pdf")
            parts = filename.split("/")

            if len(parts) > 1:
                # Extract folder path
                folder_path = "/".join(parts[:-1])
                # Add folder to structure if not exists
                if folder_path not in folder_structure:
                    folder_structure[folder_path] = f"Folder: {folder_path}"

            # Add file with description
            folder_structure[filename] = description

        return folder_structure

    def get_s3_path(self, user_id: str, agent_id: str) -> str:
        """
        Get S3 path for knowledge base

        Args:
            user_id: User ID
            agent_id: Agent ID

        Returns:
            str: S3 path
        """
        return f"s3://{self.kb_bucket}/{user_id}/{agent_id}/"

    def upload_generated_code(
        self,
        code_content: str,
        user_id: str,
        agent_id: str,
        code_bucket: str = "oratio-generated-code",
    ) -> Tuple[bool, str]:
        """
        Upload generated agent code to S3

        Args:
            code_content: Agent code as string
            user_id: User ID
            agent_id: Agent ID
            code_bucket: S3 bucket for generated code

        Returns:
            Tuple[bool, str]: (success, s3_path)
        """
        try:
            import io

            # Convert string to file-like object
            code_bytes = code_content.encode("utf-8")
            code_file = io.BytesIO(code_bytes)

            # Construct S3 key
            s3_key = f"{user_id}/{agent_id}/agent_file.py"

            # Upload with tags
            success = self.s3.upload_file(
                file_obj=code_file,
                bucket=code_bucket,
                key=s3_key,
                user_id=user_id,
                agent_id=agent_id,
                resource_type="generated-code",
                content_type="text/x-python",
            )

            s3_path = f"s3://{code_bucket}/{s3_key}"

            if success:
                logger.info(f"Uploaded generated code to {s3_path}")
            else:
                logger.error(f"Failed to upload generated code")

            return success, s3_path

        except Exception as e:
            logger.error(f"Error uploading generated code: {e}")
            return False, ""

    def check_code_exists(
        self, user_id: str, agent_id: str, code_bucket: str = "oratio-generated-code"
    ) -> bool:
        """
        Check if generated code exists in S3

        Args:
            user_id: User ID
            agent_id: Agent ID
            code_bucket: S3 bucket for generated code

        Returns:
            bool: True if code exists, False otherwise
        """
        s3_key = f"{user_id}/{agent_id}/agent_file.py"
        return self.s3.file_exists(bucket=code_bucket, key=s3_key)

    def get_generated_code(
        self, user_id: str, agent_id: str, code_bucket: str = "oratio-generated-code"
    ) -> str:
        """
        Get generated code from S3

        Args:
            user_id: User ID
            agent_id: Agent ID
            code_bucket: S3 bucket for generated code

        Returns:
            str: Code content or empty string if not found
        """
        s3_key = f"{user_id}/{agent_id}/agent_file.py"
        code_bytes = self.s3.get_file(bucket=code_bucket, key=s3_key)

        if code_bytes:
            return code_bytes.decode("utf-8")
        return ""
