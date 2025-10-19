"""
FastAPI Runtime for AgentCreator Meta-Agent
"""

import json
import logging
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .pipeline import create_agent_creator_pipeline

# Environment configuration
PORT = int(os.getenv("PORT", "8080"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Configure logging to log to stdout
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="AgentCreator Runtime", version="1.0.0")


# Request/Response models
class InvocationRequest(BaseModel):
    input: Dict[str, Any]


class InvocationResponse(BaseModel):
    output: Dict[str, Any]


# Global pipeline
agent_pipeline = None


async def initialize_pipeline():
    """Initialize the AgentCreator pipeline"""
    global agent_pipeline

    if agent_pipeline is not None:
        return

    try:
        logger.info("Initializing AgentCreator pipeline...")
        agent_pipeline = await create_agent_creator_pipeline()
        logger.info("AgentCreator pipeline initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}", exc_info=True)
        raise


@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    await initialize_pipeline()


@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """
    Main agent invocation endpoint

    Expected input format:
    {
        "input": {
            "sop": "Handle customer inquiries...",
            "knowledge_base_description": "Use for product info",
            "human_handoff_description": "Escalate for refunds",
            "bedrock_knowledge_base_id": "kb-123",
            "agent_id": "agent-456",
            "voice_personality": {
                "identity": "Friendly customer service rep",
                "demeanor": "Patient and empathetic",
                ...
            }
        }
    }

    Returns:
    {
        "output": {
            "agent_code": "# Python code...",
            "generated_prompt": "You are a customer service agent..."
        }
    }
    """
    global agent_pipeline

    logger.info("Received invocation request")

    try:
        # Ensure pipeline is initialized
        await initialize_pipeline()

        # Extract input
        input_data = request.input

        # Validate required fields
        required_fields = ["sop", "knowledge_base_description", "human_handoff_description"]
        missing_fields = [f for f in required_fields if f not in input_data]

        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )

        logger.info(f"Processing agent creation for agent_id: {input_data.get('agent_id')}")

        # Prepare initial state
        initial_state = {
            "sop": input_data["sop"],
            "knowledge_base_description": input_data["knowledge_base_description"],
            "human_handoff_description": input_data["human_handoff_description"],
            "bedrock_knowledge_base_id": input_data.get("bedrock_knowledge_base_id", ""),
            "agent_id": input_data.get("agent_id", ""),
            "voice_personality": input_data.get("voice_personality"),
            "requirements": "",
            "plan": "",
            "review_iteration": 0,
            "plan_approved": False,
            "agent_code": "",
            "code_review": "",
            "code_approved": False,
            "generated_prompt": "",
            "final_agent_code": "",
        }

        # Run the pipeline
        logger.info("Running AgentCreator pipeline...")
        result = await agent_pipeline.ainvoke(initial_state)

        # Extract outputs
        agent_code = result.get("final_agent_code", "")
        generated_prompt_obj = result.get("generated_prompt")

        if not agent_code or not generated_prompt_obj:
            raise HTTPException(
                status_code=500,
                detail="Pipeline did not generate valid output",
            )

        # Serialize SystemPrompt object to dict
        # generated_prompt_obj is a Pydantic SystemPrompt model with full_prompt and voice_prompt
        if hasattr(generated_prompt_obj, "model_dump"):
            # Use Pydantic's model_dump for proper serialization
            generated_prompt_dict = generated_prompt_obj.model_dump()
        else:
            # Fallback for non-Pydantic objects
            generated_prompt_dict = {
                "full_prompt": getattr(generated_prompt_obj, "full_prompt", ""),
                "voice_prompt": getattr(generated_prompt_obj, "voice_prompt", ""),
            }

        logger.info("Agent creation completed successfully")

        # Return output
        return InvocationResponse(
            output={
                "agent_code": agent_code,
                "generated_prompt": generated_prompt_dict,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        # Return error in AgentCore-compatible format
        return InvocationResponse(
            output={
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_code": None,
                "generated_prompt": None,
            }
        )


@app.get("/ping")
async def ping():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agentcreator"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AgentCreator Meta-Agent",
        "version": "1.0.0",
        "status": "running",
    }
