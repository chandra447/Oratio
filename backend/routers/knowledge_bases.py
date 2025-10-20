"""Knowledge Base API endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import Annotated, List
import logging

from models.knowledge_base import KnowledgeBase
from models.user import UserProfile
from services.knowledge_base_service import KnowledgeBaseService
from dependencies import get_current_user
from aws.dynamodb_client import DynamoDBClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])

dynamodb_client = DynamoDBClient()
kb_service = KnowledgeBaseService(dynamodb_client)

@router.get("", response_model=List[KnowledgeBase])
async def list_knowledge_bases(
    current_user: Annotated[UserProfile, Depends(get_current_user)]
):
    """
    List all knowledge bases for the current user.
    
    Returns:
        List of knowledge bases owned by the user
    """
    try:
        knowledge_bases = kb_service.list_user_knowledge_bases(current_user.user_id)
        return knowledge_bases
    except Exception as e:
        logger.error(f"Error listing knowledge bases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge bases"
        )


@router.get("/{knowledge_base_id}", response_model=KnowledgeBase)
async def get_knowledge_base(
    knowledge_base_id: str,
    current_user: Annotated[UserProfile, Depends(get_current_user)]
):
    """
    Get a specific knowledge base by ID.
    
    Args:
        knowledge_base_id: Knowledge base ID
        
    Returns:
        Knowledge base details
    """
    try:
        kb = kb_service.get_knowledge_base(knowledge_base_id)
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        # Verify ownership
        if kb.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this knowledge base"
            )
        
        return kb
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving knowledge base {knowledge_base_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge base"
        )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_files(
    files: List[UploadFile] = File(...),
    current_user: Annotated[UserProfile, Depends(get_current_user)] = None
):
    """
    Upload files to create a new knowledge base.
    
    Args:
        files: List of files to upload
        
    Returns:
        Created knowledge base details
    """
    try:
        # TODO: Implement file upload and knowledge base creation
        # This would involve:
        # 1. Upload files to S3
        # 2. Create knowledge base entry in DynamoDB
        # 3. Trigger Bedrock knowledge base provisioning
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="File upload not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading files: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload files"
        )


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    knowledge_base_id: str,
    current_user: Annotated[UserProfile, Depends(get_current_user)]
):
    """
    Delete a knowledge base.
    
    Args:
        knowledge_base_id: Knowledge base ID
    """
    try:
        kb = kb_service.get_knowledge_base(knowledge_base_id)
        
        if not kb:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Knowledge base not found"
            )
        
        # Verify ownership
        if kb.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this knowledge base"
            )
        
        # TODO: Implement deletion
        # This would involve:
        # 1. Delete files from S3
        # 2. Delete Bedrock knowledge base
        # 3. Delete DynamoDB entry
        
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Knowledge base deletion not yet implemented"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting knowledge base {knowledge_base_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete knowledge base"
        )

