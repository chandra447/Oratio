from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class KnowledgeBaseStatus(str, Enum):
    """Status of knowledge base"""

    NOTREADY = "notready"
    READY = "ready"
    ERROR = "error"


class KnowledgeBase(BaseModel):
    """Knowledge Base model for storing document metadata and Bedrock KB info"""

    knowledge_base_id: str = Field(..., description="Unique identifier for the knowledge base")
    user_id: str = Field(..., description="User ID who owns this knowledge base")
    s3_path: str = Field(..., description="S3 path where documents are stored")
    bedrock_knowledge_base_id: Optional[str] = Field(
        None, description="Bedrock Knowledge Base ID after provisioning"
    )
    status: KnowledgeBaseStatus = Field(
        default=KnowledgeBaseStatus.NOTREADY, description="Current status of the knowledge base"
    )
    folder_file_descriptions: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of folder/file paths to their descriptions",
    )
    created_at: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Creation timestamp",
    )
    updated_at: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Last update timestamp",
    )

    class Config:
        use_enum_values = True


class KnowledgeBaseCreate(BaseModel):
    """Request model for creating a knowledge base"""

    user_id: str
    s3_path: str
    folder_file_descriptions: Dict[str, str] = Field(default_factory=dict)


class KnowledgeBaseUpdate(BaseModel):
    """Request model for updating a knowledge base"""

    bedrock_knowledge_base_id: Optional[str] = None
    status: Optional[KnowledgeBaseStatus] = None
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

    class Config:
        use_enum_values = True
