from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Status of agent"""

    CREATING = "creating"
    ACTIVE = "active"
    FAILED = "failed"
    PAUSED = "paused"


class AgentType(str, Enum):
    """Type of agent"""

    VOICE = "voice"
    TEXT = "text"
    BOTH = "both"


class VoicePersonality(BaseModel):
    """Voice agent personality configuration"""

    identity: Optional[str] = Field(
        None,
        description="Who or what the AI represents (e.g., friendly teacher, customer service rep)",
    )
    task: Optional[str] = Field(
        None, description="High-level task description (e.g., handle customer returns accurately)"
    )
    demeanor: Optional[str] = Field(
        None, description="Overall attitude (e.g., patient, upbeat, empathetic)"
    )
    tone: Optional[str] = Field(
        None, description="Voice style (e.g., warm and conversational, polite and authoritative)"
    )
    formality_level: Optional[str] = Field(
        None, description="Casual vs professional (e.g., casual, professional, formal)"
    )
    enthusiasm_level: Optional[str] = Field(
        None, description="Energy level (e.g., calm, moderate, highly enthusiastic)"
    )
    filler_words: Optional[str] = Field(
        "occasionally",
        description="Frequency of filler words like 'um', 'uh' (none, occasionally, often)",
    )
    pacing: Optional[str] = Field(
        None, description="Rhythm and speed of delivery (e.g., slow and deliberate, moderate, fast)"
    )
    additional_instructions: Optional[str] = Field(
        None, description="Any other personality or behavior instructions"
    )


class Agent(BaseModel):
    """Agent model for storing agent configuration and metadata"""

    agent_id: str = Field(..., description="Unique identifier for the agent")
    user_id: str = Field(..., description="User ID who owns this agent")
    agent_name: str = Field(..., description="Human-readable name for the agent")
    agent_type: AgentType = Field(..., description="Type of agent (voice, text, or both)")
    sop: str = Field(..., description="Standard Operating Procedure for the agent")
    knowledge_base_id: str = Field(..., description="Associated knowledge base ID")
    knowledge_base_description: str = Field(
        ..., description="Description of when to use the knowledge base"
    )
    human_handoff_description: str = Field(
        ..., description="Description of when to escalate to human"
    )
    voice_personality: Optional[VoicePersonality] = Field(
        default=None, description="Voice agent personality configuration"
    )
    voice_config: Optional[Dict] = Field(
        default=None, description="Additional voice-specific technical configuration"
    )
    text_config: Optional[Dict] = Field(default=None, description="Text-specific configuration")
    bedrock_knowledge_base_arn: Optional[str] = Field(
        None, description="Bedrock Knowledge Base ARN"
    )
    agentcore_agent_id: Optional[str] = Field(None, description="AgentCore agent ID")
    agentcore_agent_arn: Optional[str] = Field(None, description="AgentCore agent ARN")
    generated_prompt: Optional[str] = Field(
        None, description="Generated prompt from AgentCreator for voice agents"
    )
    agent_code_s3_path: Optional[str] = Field(
        None, description="S3 path to generated agent_file.py"
    )
    status: AgentStatus = Field(
        default=AgentStatus.CREATING, description="Current status of the agent"
    )
    created_at: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Creation timestamp",
    )
    updated_at: int = Field(
        default_factory=lambda: int(datetime.now().timestamp()),
        description="Last update timestamp",
    )
    websocket_url: Optional[str] = Field(None, description="WebSocket URL for voice agent")
    api_endpoint: Optional[str] = Field(None, description="REST API endpoint for text agent")

    class Config:
        use_enum_values = True


class AgentCreate(BaseModel):
    """Request model for creating an agent"""

    agent_name: str = Field(..., min_length=3, max_length=100)
    agent_type: AgentType
    sop: str = Field(..., min_length=10)
    knowledge_base_description: str = Field(..., min_length=10)
    human_handoff_description: str = Field(..., min_length=10)
    voice_personality: Optional[VoicePersonality] = None
    voice_config: Optional[Dict] = None
    text_config: Optional[Dict] = None

    class Config:
        use_enum_values = True


class AgentUpdate(BaseModel):
    """Request model for updating an agent"""

    bedrock_knowledge_base_arn: Optional[str] = None
    agentcore_agent_id: Optional[str] = None
    agentcore_agent_arn: Optional[str] = None
    generated_prompt: Optional[str] = None
    agent_code_s3_path: Optional[str] = None
    status: Optional[AgentStatus] = None
    websocket_url: Optional[str] = None
    api_endpoint: Optional[str] = None
    updated_at: int = Field(default_factory=lambda: int(datetime.now().timestamp()))

    class Config:
        use_enum_values = True


class AgentResponse(BaseModel):
    """Response model for agent with knowledge base details"""

    agent_id: str
    user_id: str
    agent_name: str
    agent_type: AgentType
    sop: str
    knowledge_base_id: str
    knowledge_base_description: str
    human_handoff_description: str
    voice_personality: Optional[VoicePersonality]
    voice_config: Optional[Dict]
    text_config: Optional[Dict]
    bedrock_knowledge_base_arn: Optional[str]
    agentcore_agent_id: Optional[str]
    agentcore_agent_arn: Optional[str]
    generated_prompt: Optional[str]
    agent_code_s3_path: Optional[str]
    status: AgentStatus
    created_at: int
    updated_at: int
    websocket_url: Optional[str]
    api_endpoint: Optional[str]
    knowledge_base: Optional[Dict] = None  # Will be populated with KB details

    class Config:
        use_enum_values = True
