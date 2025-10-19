# OpenTelemetry Observability Setup

## Overview

The AgentCreator meta-agent is instrumented with OpenTelemetry following AWS best practices for distributed tracing. This enables complete visibility into the agent creation pipeline, from initial SOP parsing through code generation and prompt creation.

## Architecture

### Components

1. **TracerProvider**: Configured with service name, version, and environment
2. **Span Exporters**: 
   - Console exporter (debug mode only)
   - OTLP exporter (production)
3. **DSPy Instrumentation**: Automatic tracing of all DSPy LLM calls
4. **Baggage Context**: Session and user ID propagation across all spans

### Trace Hierarchy

```
Root Span: AgentCreator Invocation (session.id=agent-123)
├── Parse Voice Personality
│   └── DSPy LLM Call
├── Parse SOP
│   └── DSPy LLM Call
├── Draft Plan (iteration 1-4)
│   └── DSPy LLM Call
├── Review Plan (iteration 1-4)
│   └── DSPy LLM Call
├── Generate Code (iteration 1-3)
│   ├── DSPy ReAct LLM Call
│   └── Code Interpreter Tool
├── Review Code (iteration 1-3)
│   └── DSPy LLM Call
└── Generate Prompt
    └── DSPy LLM Call
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP endpoint URL for traces | None | No* |
| `OTEL_DEBUG` | Enable console span exporter | `false` | No |
| `ENVIRONMENT` | Deployment environment | `production` | No |

*If not set, traces will only be logged to console in debug mode.

### AWS Integration

#### CloudWatch (via OTLP)
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318/v1/traces"
# Run AWS Distro for OpenTelemetry Collector sidecar
```

#### X-Ray (via OTLP)
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318/v1/traces"
# Configure ADOT Collector with X-Ray exporter
```

#### Langfuse (Direct OTLP)
```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://us.cloud.langfuse.com/api/public/otel"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer YOUR_API_KEY"
```

## Session Context (Baggage)

Following AWS best practices, we use OpenTelemetry baggage to propagate session information across all spans:

```python
# Automatically set in agent_runtime.py
set_session_context(agent_id="agent-123", user_id="user-456")
```

This adds the following attributes to all spans:
- `session.id`: The agent ID being created
- `user.id`: The user who initiated the creation (optional)

### Benefits

1. **Correlation**: All spans for a single agent creation are linked
2. **Filtering**: Easy filtering in observability platforms by session/user
3. **Debugging**: Trace the entire agent creation flow for a specific agent
4. **Analytics**: Aggregate metrics by user or agent

## Observability Platforms

### Supported Platforms

Any OTLP-compatible observability platform:
- **AWS CloudWatch** (via ADOT Collector)
- **AWS X-Ray** (via ADOT Collector)
- **Langfuse** (direct OTLP)
- **Grafana Tempo** (direct OTLP)
- **Datadog** (direct OTLP)
- **Honeycomb** (direct OTLP)
- **New Relic** (direct OTLP)

### Recommended: AWS Distro for OpenTelemetry (ADOT)

For production deployments on AWS, use ADOT Collector as a sidecar:

```yaml
# docker-compose.yml or ECS task definition
services:
  agentcreator:
    image: your-agentcreator-image
    environment:
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://adot-collector:4318/v1/traces
    depends_on:
      - adot-collector
  
  adot-collector:
    image: public.ecr.aws/aws-observability/aws-otel-collector:latest
    command: ["--config=/etc/otel-config.yaml"]
    volumes:
      - ./otel-config.yaml:/etc/otel-config.yaml
```

## Metrics and Attributes

### Span Attributes

All spans include:
- `service.name`: `agentcreator-meta-agent`
- `service.version`: `1.0.0`
- `deployment.environment`: From `ENVIRONMENT` env var
- `session.id`: Agent ID (from baggage)
- `user.id`: User ID (from baggage, if provided)

### DSPy Spans

DSPy instrumentation automatically adds:
- `gen_ai.prompt`: The prompt sent to the LLM
- `gen_ai.completion`: The LLM response
- `gen_ai.usage.prompt_tokens`: Input tokens
- `gen_ai.usage.completion_tokens`: Output tokens
- `gen_ai.usage.total_tokens`: Total tokens
- `gen_ai.system`: `bedrock`
- `gen_ai.request.model`: Model ID (e.g., `amazon.nova-pro-v1:0`)

## Local Development

### Debug Mode

Enable console output for traces:

```bash
export OTEL_DEBUG=true
uv run python -m scripts.test_pipeline
```

This will print all spans to the console for debugging.

### Testing with Langfuse (Free Tier)

1. Sign up at https://cloud.langfuse.com
2. Get your API key
3. Configure environment:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="https://us.cloud.langfuse.com/api/public/otel"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=Bearer YOUR_API_KEY"
```

## Production Best Practices

1. **Always set `ENVIRONMENT`**: Helps distinguish dev/staging/prod traces
2. **Use ADOT Collector**: Don't send traces directly from Lambda/ECS to external services
3. **Set proper timeouts**: OTLP exporter has default 10s timeout
4. **Monitor collector health**: Ensure ADOT Collector is running and healthy
5. **Use sampling**: For high-volume workloads, configure sampling in ADOT Collector
6. **Secure credentials**: Use AWS Secrets Manager for OTLP endpoint credentials

## Troubleshooting

### Traces not appearing

1. Check `OTEL_EXPORTER_OTLP_ENDPOINT` is set correctly
2. Verify network connectivity to OTLP endpoint
3. Enable debug mode: `OTEL_DEBUG=true`
4. Check ADOT Collector logs (if using)
5. Verify authentication headers (if required)

### Missing span attributes

1. Ensure `set_session_context()` is called before pipeline execution
2. Check that `agent_id` is provided in the invocation payload
3. Verify DSPy instrumentation is initialized: `DSPyInstrumentor().instrument()`

### Performance impact

- OpenTelemetry has minimal overhead (<1% CPU, <10MB memory)
- Use BatchSpanProcessor (default) for async export
- Configure appropriate batch sizes in ADOT Collector

## References

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/languages/python/)
- [AWS ADOT Documentation](https://aws-otel.github.io/)
- [OpenTelemetry Baggage Spec](https://opentelemetry.io/docs/specs/otel/baggage/api/)
- [DSPy Instrumentation](https://github.com/Arize-ai/openinference/tree/main/python/instrumentation/openinference-instrumentation-dspy)
- [AWS Bedrock Agent Observability Sample](https://github.com/aws-samples/amazon-bedrock-samples/tree/main/evaluation-observe/open-telemetry-instrumentation)

