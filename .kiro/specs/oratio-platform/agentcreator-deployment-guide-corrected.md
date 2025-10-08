# AgentCreator Deployment Guide - Corrected

## Overview
Based on the official AWS Bedrock AgentCore samples, here's the correct way to deploy the AgentCreator meta-agent.

**Reference**: https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/02-use-cases/SRE-agent

## Project Structure

```
agentcreator/
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── agentcreator/
    ├── __init__.py
    ├── agent_runtime.py      # FastAPI app with /invocations endpoint
    ├── pipeline.py            # LangGraph workflow
    ├── modules/
    │   ├── sop_parser.py     # DSPy module
    │   ├── plan_drafter.py   # DSPy module
    │   ├── plan_reviewer.py  # DSPy module
    │   ├── code_generator.py # DSPy module
    │   └── code_reviewer.py  # DSPy module
    └── prompts/
        └── strands_templates.py
```

## Dockerfile (Correct)

```dockerfile
# Use uv's ARM64 Python base image
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy uv files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy agentcreator module
COPY agentcreator/ ./agentcreator/

# Set environment variables
ENV PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run application with OpenTelemetry instrumentation
CMD ["uv", "run", "opentelemetry-instrument", "uvicorn", "agentcreator.agent_runtime:app", "--host", "0.0.0.0", "--port", "8080"]
```

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "agentcreator"
version = "1.0.0"
description = "Meta-agent for generating custom AI agents"
requires-python = ">=3.12"

dependencies = [
    "langgraph>=0.5.4",
    "langchain-core>=0.3.72",
    "langchain-aws>=0.2.29",
    "langchain-anthropic>=0.3.17",
    "pydantic>=2.0.0",
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "httpx>=0.25.0",
    "python-dotenv>=1.0.0",
    "anthropic>=0.57.1",
    "python-multipart>=0.0.6",
    "boto3>=1.39.0",
    "bedrock-agentcore>=0.1.1",
    "opentelemetry-instrumentation-langchain",
    "aws-opentelemetry-distro~=0.10.1",
    "dspy-ai>=2.5.0",
]

[tool.setuptools.packages.find]
where = ["."]
include = ["agentcreator*"]
```

## agent_runtime.py (FastAPI App)

```python
import logging
import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .pipeline import create_agent_creator_pipeline

logger = logging.getLogger(__name__)

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
        logger.error(f"Failed to initialize pipeline: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    await initialize_pipeline()

@app.post("/invocations", response_model=InvocationResponse)
async def invoke_agent(request: InvocationRequest):
    """Main agent invocation endpoint"""
    global agent_pipeline
    
    logger.info("Received invocation request")
    
    try:
        # Ensure pipeline is initialized
        await initialize_pipeline()
        
        # Extract input
        input_data = request.input
        
        # Required fields
        sop = input_data.get("sop")
        if not sop:
            raise HTTPException(status_code=400, detail="Missing 'sop' in input")
        
        logger.info(f"Processing agent creation request")
        
        # Run the pipeline
        result = await agent_pipeline.ainvoke(input_data)
        
        # Extract agent_code and generated_prompt from result
        agent_code = result.get("agent_code")
        generated_prompt = result.get("generated_prompt")
        
        if not agent_code or not generated_prompt:
            raise HTTPException(
                status_code=500,
                detail="Pipeline did not generate valid output"
            )
        
        logger.info("Agent creation completed successfully")
        
        # Return output in expected format
        return InvocationResponse(
            output={
                "agent_code": agent_code,
                "generated_prompt": generated_prompt
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ping")
async def ping():
    """Health check endpoint"""
    return {"status": "healthy"}
```

## Key Differences from Previous Guide

### ❌ Old (Incorrect)
- Complex OpenTelemetry setup
- Manual instrumentation
- Custom OTEL configuration
- Multiple environment variables

### ✅ New (Correct)
- Simple `uv` based Dockerfile
- Automatic OpenTelemetry via `opentelemetry-instrument`
- FastAPI app with `/invocations` endpoint
- Clean, minimal setup

## Building and Deploying

### 1. Build Docker Image
```bash
cd agentcreator
docker build --platform linux/arm64 -t agentcreator:latest .
```

### 2. Test Locally
```bash
docker run -p 8080:8080 \
  -e AWS_REGION=us-east-1 \
  -e AWS_ACCESS_KEY_ID=<key> \
  -e AWS_SECRET_ACCESS_KEY=<secret> \
  agentcreator:latest
```

### 3. Test Endpoint
```bash
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "sop": "Handle customer inquiries professionally",
      "knowledge_base_description": "Use for product info",
      "human_handoff_description": "Escalate for refunds",
      "bedrock_knowledge_base_id": "kb-123",
      "agent_id": "agent-456",
      "voice_personality": {
        "identity": "Friendly customer service rep",
        "demeanor": "Patient and empathetic"
      }
    }
  }'
```

### 4. Push to ECR
```bash
# Create ECR repository
aws ecr create-repository --repository-name agentcreator

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag agentcreator:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/agentcreator:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/agentcreator:latest
```

### 5. Deploy to AgentCore
```bash
# Create agent with Docker image
aws bedrock create-agent \
  --agent-name "AgentCreator" \
  --description "Meta-agent for generating custom agents" \
  --foundation-model "anthropic.claude-3-sonnet-20240229-v1:0" \
  --instruction "You are a meta-agent that generates custom AI agents based on SOPs" \
  --agent-resource-role-arn "arn:aws:iam::<account>:role/AgentCoreRole" \
  --tags userId=system,platform=oratio,environment=production \
  --container-configuration '{
    "imageUri": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/agentcreator:latest",
    "port": 8080
  }'
```

## Environment Variables

The container needs these environment variables:
```bash
AWS_REGION=us-east-1
PYTHONPATH=/app
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

## Dependencies

Key dependencies from pyproject.toml:
- `langgraph` - Workflow orchestration
- `dspy-ai` - LLM pipeline modules
- `langchain-aws` - AWS Bedrock integration
- `bedrock-agentcore` - AgentCore SDK
- `fastapi` + `uvicorn` - Web server
- `opentelemetry-instrumentation-langchain` - Auto-instrumentation

## Next Steps

1. **Implement Pipeline** - Create the DSPy + LangGraph pipeline
2. **Test Locally** - Run Docker container and test /invocations
3. **Deploy to ECR** - Push image to ECR
4. **Deploy to AgentCore** - Create agent with container
5. **Update Lambda** - Set AGENTCREATOR_AGENT_ID environment variable

## Files to Delete

The old guide had incorrect information. Delete:
- ❌ `agentcreator-docker-otel-guide.md` (if exists)
- ❌ Any manual OTEL configuration files

## Summary

The correct approach is:
1. Use `uv` for dependency management
2. Simple Dockerfile with automatic OTEL instrumentation
3. FastAPI app with `/invocations` endpoint
4. Deploy as container to AgentCore
5. No complex OTEL setup needed!

Much simpler and follows AWS best practices! 🚀
