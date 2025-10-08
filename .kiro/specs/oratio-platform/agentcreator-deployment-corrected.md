# AgentCreator Deployment - Corrected Approach

## Key Learnings from AWS Sample

Based on the [AWS AgentCore SRE Agent sample](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/02-use-cases/SRE-agent), here's the correct approach:

## ✅ Correct Dockerfile

```dockerfile
# Use uv's ARM64 Python base image (AgentCore runs on ARM64/Graviton)
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copy uv project files
COPY pyproject.toml uv.lock ./

# Install dependencies (frozen lockfile, no dev dependencies)
RUN uv sync --frozen --no-dev

# Copy AgentCreator module
COPY agentcreator/ ./agentcreator/

# Set environment variables
ENV PYTHONPATH="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8080

# Run with OpenTelemetry auto-instrumentation
CMD ["uv", "run", "opentelemetry-instrument", "uvicorn", "agentcreator.agent_runtime:app", "--host", "0.0.0.0", "--port", "8080"]
```

## Key Differences

### ❌ What I Had Wrong

1. **Custom entrypoint.sh script** - Not needed!
2. **Multi-stage build** - Unnecessary complexity
3. **Manual pip install** - UV is better
4. **x86_64 platform** - AgentCore uses ARM64

### ✅ What's Correct

1. **UV package manager** - Faster, more reliable
2. **ARM64 platform** - Matches AgentCore infrastructure
3. **OpenTelemetry in CMD** - Simple, no custom script
4. **FastAPI + Uvicorn** - Standard web framework
5. **pyproject.toml** - Modern Python packaging

## Project Structure

```
agentcreator/
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── agentcreator/
│   ├── __init__.py
│   ├── agent_runtime.py      # FastAPI app (entrypoint)
│   ├── pipeline.py            # LangGraph workflow
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── sop_parser.py     # DSPy module
│   │   ├── plan_drafter.py   # DSPy module
│   │   ├── plan_reviewer.py  # DSPy module
│   │   ├── code_generator.py # DSPy module
│   │   └── code_reviewer.py  # DSPy module
│   └── utils/
│       ├── __init__.py
│       └── telemetry.py      # Custom spans
└── tests/
    └── test_pipeline.py
```

## PyProject.toml

```toml
[project]
name = "agentcreator"
version = "1.0.0"
description = "AgentCreator meta-agent with DSPy + LangGraph"
requires-python = ">=3.12"

dependencies = [
    # Core frameworks
    "langgraph>=0.5.4",
    "langchain-core>=0.3.72",
    "langchain-aws>=0.2.29",
    "langchain-anthropic>=0.3.17",
    "dspy-ai>=2.4.0",
    
    # Web framework
    "fastapi>=0.104.0",
    "uvicorn>=0.24.0",
    "python-multipart>=0.0.6",
    
    # AWS
    "boto3>=1.39.0",
    "bedrock-agentcore>=0.1.1",
    
    # OpenTelemetry
    "aws-opentelemetry-distro~=0.10.1",
    "opentelemetry-instrumentation-langchain",
    "langsmith[otel]",
    
    # Utilities
    "pydantic>=2.0.0",
    "pyyaml>=6.0.1",
    "httpx>=0.25.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
]

[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]
```

## Agent Runtime (FastAPI)

### agentcreator/agent_runtime.py

```python
"""
AgentCreator Runtime - FastAPI application for AgentCore
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

from agentcreator.pipeline import AgentCreatorPipeline

logger = logging.getLogger(__name__)

app = FastAPI(title="AgentCreator", version="1.0.0")

# Initialize pipeline
pipeline = AgentCreatorPipeline()


class AgentCreationRequest(BaseModel):
    sop: str
    knowledge_base_description: str
    human_handoff_description: str
    bedrock_knowledge_base_id: str
    agent_id: str
    voice_personality: dict | None = None


class AgentCreationResponse(BaseModel):
    agent_code: str
    generated_prompt: str


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "agentcreator"}


@app.post("/generate", response_model=AgentCreationResponse)
async def generate_agent(request: AgentCreationRequest):
    """Generate agent code from SOP"""
    try:
        logger.info(f"Generating agent for: {request.agent_id}")
        
        result = pipeline.run(request.model_dump())
        
        return AgentCreationResponse(
            agent_code=result["agent_code"],
            generated_prompt=result["generated_prompt"]
        )
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Build and Deploy Commands

### Local Development

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create project
uv init agentcreator
cd agentcreator

# Add dependencies
uv add langgraph langchain-aws dspy-ai fastapi uvicorn boto3 bedrock-agentcore aws-opentelemetry-distro

# Run locally
uv run uvicorn agentcreator.agent_runtime:app --reload

# Run with OpenTelemetry
uv run opentelemetry-instrument uvicorn agentcreator.agent_runtime:app --reload
```

### Build Docker Image

```bash
# Build for ARM64 (AgentCore platform)
docker build --platform linux/arm64 -t agentcreator:latest .

# Test locally (if on ARM64 Mac)
docker run -p 8080:8080 agentcreator:latest

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com
docker tag agentcreator:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/agentcreator:latest
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/agentcreator:latest
```

### Deploy to AgentCore

```python
import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create agent
response = bedrock_agent.create_agent(
    agentName='agentcreator',
    agentResourceRoleArn='arn:aws:iam::account:role/AgentCoreRole',
    description='AgentCreator meta-agent',
    foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
    instruction='You are the AgentCreator meta-agent that generates custom agents from SOPs',
    tags={'platform': 'oratio', 'component': 'agentcreator'}
)

agent_id = response['agent']['agentId']
print(f"AgentCreator deployed: {agent_id}")
```

## OpenTelemetry Configuration

### Environment Variables (Set in AgentCore)

```bash
# Service identification
OTEL_SERVICE_NAME=agentcreator
OTEL_RESOURCE_ATTRIBUTES=service.version=1.0.0,deployment.environment=production

# AWS X-Ray integration
OTEL_PROPAGATORS=xray,tracecontext,baggage
OTEL_PYTHON_ID_GENERATOR=xray

# Exporters
OTEL_TRACES_EXPORTER=otlp
OTEL_METRICS_EXPORTER=otlp
OTEL_LOGS_EXPORTER=otlp

# OTLP endpoint (AgentCore provides this)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc

# Auto-instrumentation
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true
```

## Key Advantages

### 1. UV Package Manager
- **10-100x faster** than pip
- **Deterministic builds** with uv.lock
- **Better dependency resolution**
- **Built-in virtual environment management**

### 2. ARM64 Platform
- **Cost savings** (Graviton is cheaper)
- **Better performance** on AgentCore
- **Native platform** (no emulation)

### 3. Simple CMD
- **No custom scripts** needed
- **OpenTelemetry auto-instrumentation** works out of the box
- **UV run** handles environment automatically

### 4. FastAPI Runtime
- **Standard web framework** for agents
- **Health check endpoints** built-in
- **OpenAPI docs** automatically generated
- **Async support** for LangGraph

## Testing

### Local Testing

```bash
# Run with Docker Compose
docker-compose up

# Test health endpoint
curl http://localhost:8080/health

# Test agent generation
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{
    "sop": "Handle customer inquiries...",
    "knowledge_base_description": "Use for product info",
    "human_handoff_description": "Escalate for refunds",
    "bedrock_knowledge_base_id": "kb-123",
    "agent_id": "agent-456",
    "voice_personality": {
      "identity": "Friendly customer service rep",
      "demeanor": "Patient and empathetic"
    }
  }'
```

### View Traces

```bash
# OpenTelemetry automatically instruments:
# - FastAPI requests
# - LangChain/LangGraph operations
# - Boto3 AWS calls
# - HTTP requests

# View in AWS X-Ray Console
# Or locally in Jaeger: http://localhost:16686
```

## Summary

### ✅ Correct Approach (AWS Best Practice)
- UV package manager
- ARM64 platform
- OpenTelemetry in CMD (no custom script)
- FastAPI + Uvicorn runtime
- pyproject.toml + uv.lock

### ❌ Previous Approach (Overcomplicated)
- ~~Custom entrypoint.sh script~~
- ~~Multi-stage build~~
- ~~Manual pip install~~
- ~~x86_64 platform~~

## References

- [AWS AgentCore SRE Agent Sample](https://github.com/awslabs/amazon-bedrock-agentcore-samples/tree/main/02-use-cases/SRE-agent)
- [UV Package Manager](https://docs.astral.sh/uv/)
- [OpenTelemetry Python Auto-Instrumentation](https://opentelemetry.io/docs/zero-code/python/)
- [AWS OTEL Python](https://aws-otel.github.io/docs/getting-started/python-sdk/auto-instr)

---

**Status**: ✅ Ready for implementation
**Platform**: ARM64 (Graviton)
**Package Manager**: UV
**Runtime**: FastAPI + Uvicorn
**Instrumentation**: OpenTelemetry auto-instrumentation
