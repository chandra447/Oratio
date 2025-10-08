# AgentCreator Docker + OpenTelemetry Packaging Guide

## Overview
Best practices for packaging the AgentCreator meta-agent (DSPy + LangGraph) with Docker and OpenTelemetry instrumentation for deployment to AWS AgentCore.

## Architecture

```
AgentCreator Container
├── Python Application (DSPy + LangGraph)
├── OpenTelemetry Auto-Instrumentation
├── OpenTelemetry Collector (Sidecar)
└── AWS X-Ray Integration
```

## Dockerfile Structure

### Using UV Package Manager (AWS Best Practice)

```dockerfile
# Use uv's ARM64 Python base image (AgentCore runs on ARM64)
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
# uv run automatically uses the virtual environment
CMD ["uv", "run", "opentelemetry-instrument", "uvicorn", "agentcreator.agent_runtime:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Key Differences from Standard Approach

1. **UV Package Manager**: Faster, more reliable than pip
2. **ARM64 Platform**: AgentCore runs on ARM64 (Graviton)
3. **No Custom Entrypoint Script**: OpenTelemetry instrumentation in CMD
4. **UV Run**: Automatically manages virtual environment
5. **FastAPI/Uvicorn**: Standard web framework for AgentCore agents

## PyProject.toml Configuration

### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

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
    "botocore>=1.39.0",
    "bedrock-agentcore>=0.1.1",
    
    # OpenTelemetry
    "aws-opentelemetry-distro~=0.10.1",
    "opentelemetry-instrumentation-langchain",
    "langsmith[otel]",
    
    # Utilities
    "pydantic>=2.0.0",
    "pyyaml>=6.0.1",
    "httpx>=0.25.0",
    "python-dotenv>=1.0.0",
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

## Agent Runtime Structure

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
    """
    Generate agent code from SOP
    
    This endpoint is invoked by the AgentCreator Invoker Lambda
    """
    try:
        logger.info(f"Generating agent for: {request.agent_id}")
        
        # Run pipeline
        result = pipeline.run({
            "sop": request.sop,
            "knowledge_base_description": request.knowledge_base_description,
            "human_handoff_description": request.human_handoff_description,
            "bedrock_knowledge_base_id": request.bedrock_knowledge_base_id,
            "agent_id": request.agent_id,
            "voice_personality": request.voice_personality,
        })
        
        return AgentCreationResponse(
            agent_code=result["agent_code"],
            generated_prompt=result["generated_prompt"]
        )
        
    except Exception as e:
        logger.error(f"Error generating agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

## Application Structure

```
agentcreator/
├── __init__.py
├── main.py                    # Entry point
├── pipeline.py                # LangGraph workflow
├── config.py                  # Configuration
├── modules/
│   ├── __init__.py
│   ├── sop_parser.py         # DSPy module
│   ├── plan_drafter.py       # DSPy module
│   ├── plan_reviewer.py      # DSPy module
│   ├── code_generator.py     # DSPy module
│   └── code_reviewer.py      # DSPy module
├── prompts/
│   └── strands_templates.py  # Strands agent templates
└── utils/
    ├── __init__.py
    ├── telemetry.py          # Custom telemetry helpers
    └── logging.py            # Logging configuration
```

## Main Application with Telemetry

### agentcreator/main.py

```python
import logging
import os
from opentelemetry import trace
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from agentcreator.pipeline import AgentCreatorPipeline
from agentcreator.utils.telemetry import setup_custom_spans

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get tracer
tracer = trace.get_tracer(__name__)

def main():
    """Main entry point for AgentCreator"""
    logger.info("Starting AgentCreator service")
    
    # Initialize pipeline
    pipeline = AgentCreatorPipeline()
    
    # Setup custom telemetry
    setup_custom_spans()
    
    # Start service (FastAPI, Lambda handler, etc.)
    # This depends on your deployment model
    logger.info("AgentCreator service ready")

if __name__ == "__main__":
    main()
```

### agentcreator/utils/telemetry.py

```python
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from functools import wraps
import logging

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

def trace_dspy_module(module_name: str):
    """Decorator to trace DSPy module execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(
                f"dspy.{module_name}",
                attributes={
                    "dspy.module": module_name,
                    "dspy.input_keys": list(kwargs.keys()),
                }
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("dspy.success", True)
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("dspy.error", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator

def trace_langgraph_node(node_name: str):
    """Decorator to trace LangGraph node execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with tracer.start_as_current_span(
                f"langgraph.node.{node_name}",
                attributes={
                    "langgraph.node": node_name,
                }
            ) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator

def setup_custom_spans():
    """Setup custom span processors for AgentCreator"""
    logger.info("Custom telemetry spans configured")
```

## Docker Compose for Local Development

```yaml
version: '3.8'

services:
  agentcreator:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - OTEL_SERVICE_NAME=agentcreator
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - ENVIRONMENT=development
      - AWS_REGION=us-east-1
    depends_on:
      - otel-collector
    volumes:
      - ./agentcreator:/app/agentcreator  # For development

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC receiver
      - "4318:4318"   # OTLP HTTP receiver
      - "8888:8888"   # Prometheus metrics
      - "13133:13133" # Health check
    environment:
      - AWS_REGION=us-east-1

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # Jaeger UI
      - "14250:14250"  # Jaeger gRPC
```

## OpenTelemetry Collector Configuration

### otel-collector-config.yaml

```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024
  
  resource:
    attributes:
      - key: service.namespace
        value: oratio
        action: insert
  
  attributes:
    actions:
      - key: agent.type
        value: agentcreator
        action: insert

exporters:
  # AWS X-Ray
  awsxray:
    region: us-east-1
  
  # CloudWatch Metrics
  awsemf:
    region: us-east-1
    namespace: Oratio/AgentCreator
  
  # Jaeger (for local development)
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true
  
  # Logging (for debugging)
  logging:
    loglevel: info

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch, resource, attributes]
      exporters: [awsxray, jaeger, logging]
    
    metrics:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [awsemf, logging]
    
    logs:
      receivers: [otlp]
      processors: [batch, resource]
      exporters: [logging]
```

## AWS AgentCore Deployment

### Deploy to AgentCore

```python
import boto3

bedrock_agent = boto3.client('bedrock-agent')

# Create agent with container image
response = bedrock_agent.create_agent(
    agentName='agentcreator',
    agentResourceRoleArn='arn:aws:iam::account:role/AgentCoreRole',
    description='AgentCreator meta-agent with DSPy + LangGraph',
    foundationModel='anthropic.claude-3-sonnet-20240229-v1:0',
    instruction='You are the AgentCreator meta-agent...',
    # Container configuration
    containerConfiguration={
        'imageUri': '123456789012.dkr.ecr.us-east-1.amazonaws.com/agentcreator:latest',
        'environment': {
            'OTEL_SERVICE_NAME': 'agentcreator',
            'OTEL_EXPORTER_OTLP_ENDPOINT': 'http://otel-collector:4317',
        }
    },
    tags={
        'platform': 'oratio',
        'component': 'agentcreator',
    }
)
```

## Key Benefits

### 1. Observability
- **Distributed Tracing**: Track requests across DSPy modules and LangGraph nodes
- **Metrics**: Monitor performance, latency, error rates
- **Logs**: Structured logging with trace correlation

### 2. AWS Integration
- **X-Ray**: Native AWS X-Ray support for distributed tracing
- **CloudWatch**: Metrics and logs in CloudWatch
- **AgentCore**: Seamless integration with AgentCore observability

### 3. Development Experience
- **Auto-Instrumentation**: No code changes needed for basic telemetry
- **Custom Spans**: Add custom spans for DSPy/LangGraph specific operations
- **Local Testing**: Docker Compose setup with Jaeger UI

### 4. Production Ready
- **Multi-Stage Build**: Optimized image size
- **Health Checks**: Built-in health check endpoints
- **Resource Limits**: Configurable CPU/memory limits
- **Security**: Non-root user, minimal attack surface

## Best Practices

### 1. Instrumentation
- ✅ Use auto-instrumentation for standard libraries
- ✅ Add custom spans for DSPy modules and LangGraph nodes
- ✅ Include relevant attributes (module name, input keys, etc.)
- ✅ Record exceptions with context

### 2. Performance
- ✅ Use batch processor to reduce overhead
- ✅ Sample traces in production (e.g., 10% sampling)
- ✅ Set appropriate timeout values
- ✅ Monitor instrumentation overhead

### 3. Security
- ✅ Don't log sensitive data (API keys, user data)
- ✅ Use IAM roles instead of credentials
- ✅ Scan container images for vulnerabilities
- ✅ Use private ECR registry

### 4. Deployment
- ✅ Use multi-stage builds for smaller images
- ✅ Pin dependency versions
- ✅ Include health check endpoints
- ✅ Set resource limits

## Testing

### Local Testing

```bash
# Build image
docker build -t agentcreator:latest .

# Run with Docker Compose
docker-compose up

# View traces in Jaeger
open http://localhost:16686

# Test the agent
curl -X POST http://localhost:8080/generate \
  -H "Content-Type: application/json" \
  -d '{"sop": "Handle customer inquiries..."}'
```

### Verify Telemetry

```bash
# Check OpenTelemetry instrumentation
docker exec agentcreator opentelemetry-instrument --help

# View logs
docker logs agentcreator

# Check metrics
curl http://localhost:8888/metrics
```

## References

- [OpenTelemetry Python Auto-Instrumentation](https://opentelemetry.io/docs/zero-code/python/)
- [AWS OTEL Python](https://aws-otel.github.io/docs/getting-started/python-sdk/auto-instr)
- [LangGraph Observability](https://langfuse.com/blog/2024-10-opentelemetry-for-llm-observability)
- [AWS Bedrock AgentCore](https://docs.aws.amazon.com/bedrock-agentcore/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)

## Next Steps

1. Implement AgentCreator pipeline with DSPy + LangGraph
2. Add custom telemetry decorators to modules
3. Build and test Docker image locally
4. Deploy to ECR
5. Deploy to AWS AgentCore
6. Monitor with X-Ray and CloudWatch
