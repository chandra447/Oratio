"""
Conversation Logger Service
Logs voice conversation history to DynamoDB for analytics and replay
Based on: https://github.com/aws-samples/amazon-nova-samples/blob/main/speech-to-speech/repeatable-patterns/chat-history-logger/chat_history.py
"""

import logging
import boto3
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ConversationLoggerService:
    """
    Service for logging voice conversation history
    
    Stores:
    - User speech transcripts
    - Assistant responses (text + audio metadata)
    - Tool calls (Chameleon invocations)
    - Timestamps and session metadata
    """
    
    def __init__(
        self,
        agent_id: str,
        user_id: str,
        actor_id: str,
        session_id: str,
        dynamodb_table_name: str = "oratio-voice-sessions"
    ):
        self.agent_id = agent_id
        self.user_id = user_id
        self.actor_id = actor_id
        self.session_id = session_id
        self.conversation_turns = []
        
        # DynamoDB client
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = dynamodb_table_name
        self.table = None
        
        # Session metadata
        self.session_start_time = datetime.utcnow()
        self.session_end_time = None
        
        logger.info(
            f"[ConversationLogger] Initialized for agent={agent_id}, "
            f"user={user_id}, actor={actor_id}, session={session_id}"
        )
    
    def log_turn(
        self,
        role: str,
        content: str,
        content_type: str = "text",
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a conversation turn
        
        Args:
            role: "USER" or "ASSISTANT"
            content: Text content (transcript or response)
            content_type: "text" or "audio"
            timestamp: Optional timestamp (defaults to now)
            metadata: Optional additional metadata
        """
        turn = {
            "role": role,
            "content": content,
            "content_type": content_type,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
        }
        
        if metadata:
            turn["metadata"] = metadata
        
        self.conversation_turns.append(turn)
        
        # Log preview (truncate long content)
        content_preview = content[:100] + "..." if len(content) > 100 else content
        logger.info(f"[ConversationLogger] {role}: {content_preview}")
    
    def log_tool_call(
        self,
        tool_name: str,
        tool_input: Dict,
        tool_output: str,
        timestamp: Optional[datetime] = None
    ):
        """
        Log a tool invocation (Chameleon call)
        
        Args:
            tool_name: Name of the tool (e.g., "business_agent")
            tool_input: Tool input parameters
            tool_output: Tool result/output
            timestamp: Optional timestamp (defaults to now)
        """
        tool_turn = {
            "role": "TOOL",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
        }
        
        self.conversation_turns.append(tool_turn)
        
        logger.info(f"[ConversationLogger] Tool call: {tool_name}")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get all conversation turns"""
        return self.conversation_turns
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the session"""
        user_turns = sum(1 for t in self.conversation_turns if t.get("role") == "USER")
        assistant_turns = sum(1 for t in self.conversation_turns if t.get("role") == "ASSISTANT")
        tool_calls = sum(1 for t in self.conversation_turns if t.get("role") == "TOOL")
        
        duration = None
        if self.session_end_time:
            duration = (self.session_end_time - self.session_start_time).total_seconds()
        
        return {
            "total_turns": len(self.conversation_turns),
            "user_turns": user_turns,
            "assistant_turns": assistant_turns,
            "tool_calls": tool_calls,
            "duration_seconds": duration,
            "session_start": self.session_start_time.isoformat(),
            "session_end": self.session_end_time.isoformat() if self.session_end_time else None,
        }
    
    async def save_to_dynamodb(self):
        """
        Save conversation history to DynamoDB
        
        Schema:
        - PK: sessionId (session_id)
        - SK: userId (user_id)
        - agentId
        - actorId (end customer)
        - conversationTurns (list of turn objects)
        - sessionSummary (stats)
        - sessionStart, sessionEnd
        - createdAt, updatedAt
        """
        try:
            # Mark session end time
            self.session_end_time = datetime.utcnow()
            
            # Initialize table if not already done
            if not self.table:
                self.table = self.dynamodb.Table(self.table_name)
            
            # Prepare item
            item = {
                "sessionId": self.session_id,  # PK
                "userId": self.user_id,        # SK
                "agentId": self.agent_id,
                "actorId": self.actor_id,
                "conversationTurns": self.conversation_turns,
                "sessionSummary": self.get_session_summary(),
                "sessionStart": self.session_start_time.isoformat(),
                "sessionEnd": self.session_end_time.isoformat(),
                "createdAt": int(self.session_start_time.timestamp()),
                "updatedAt": int(self.session_end_time.timestamp()),
            }
            
            # Save to DynamoDB
            self.table.put_item(Item=item)
            
            logger.info(
                f"[ConversationLogger] Session saved to DynamoDB: "
                f"{len(self.conversation_turns)} turns, "
                f"duration: {self.get_session_summary()['duration_seconds']:.1f}s"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"[ConversationLogger] Error saving to DynamoDB: {e}", exc_info=True)
            return False
    
    async def get_session_history(
        session_id: str,
        user_id: str,
        table_name: str = "oratio-voice-sessions"
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a session's conversation history from DynamoDB
        
        Static method for fetching historical sessions
        """
        try:
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(table_name)
            
            response = table.get_item(
                Key={
                    "sessionId": session_id,
                    "userId": user_id
                }
            )
            
            item = response.get('Item')
            
            if item:
                logger.info(f"[ConversationLogger] Retrieved session {session_id}")
                return item
            else:
                logger.warning(f"[ConversationLogger] Session {session_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"[ConversationLogger] Error retrieving session: {e}", exc_info=True)
            return None
    
    async def list_user_sessions(
        user_id: str,
        agent_id: Optional[str] = None,
        limit: int = 20,
        table_name: str = "oratio-voice-sessions"
    ) -> List[Dict[str, Any]]:
        """
        List voice sessions for a user
        
        Static method for retrieving multiple sessions
        """
        try:
            dynamodb = boto3.resource('dynamodb')
            table = dynamodb.Table(table_name)
            
            # Query by userId (SK) - requires GSI
            # For now, scan and filter (add GSI in production)
            response = table.scan(
                FilterExpression="userId = :user_id",
                ExpressionAttributeValues={":user_id": user_id},
                Limit=limit
            )
            
            items = response.get('Items', [])
            
            # Filter by agent_id if provided
            if agent_id:
                items = [item for item in items if item.get('agentId') == agent_id]
            
            # Sort by most recent
            items.sort(key=lambda x: x.get('createdAt', 0), reverse=True)
            
            logger.info(f"[ConversationLogger] Found {len(items)} sessions for user {user_id}")
            return items
            
        except Exception as e:
            logger.error(f"[ConversationLogger] Error listing sessions: {e}", exc_info=True)
            return []

