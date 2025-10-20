# OpenTelemetry Observability Setup

## Overview

The AgentCreator meta-agent is instrumented with OpenTelemetry following AWS best practices for distributed tracing. This enables complete visibility into the agent creation pipeline, from initial SOP parsing through code generation and prompt creation.

## ⚠️ Important: AgentCore Auto-Instrumentation

**AWS Bedrock AgentCore automatically instruments your application with OpenTelemetry!**

When you deploy to AgentCore, it automatically:
- ✅ Creates and configures a `TracerProvider` with proper AWS resource attributes
- ✅ Instruments DSPy and other Python libraries
- ✅ Exports traces to AWS CloudWatch and X-Ray
- ✅ Adds AgentCore-specific span attributes

**You do NOT need to:**
- ❌ Create your own `TracerProvider`
- ❌ Call `DSPyInstrumentor().instrument()`
- ❌ Configure OTLP exporters manually

**You only need to:**
- ✅ Use OpenTelemetry **baggage** for session context propagation
- ✅ Let AgentCore handle all the instrumentation

## Architecture

### Components

1. **TracerProvider**: Automatically configured by AgentCore
2. **Span Exporters**: Automatically configured by AgentCore (CloudWatch, X-Ray)
3. **DSPy Instrumentation**: Automatically enabled by AgentCore
4. **Baggage Context**: Session and user ID propagation (your responsibility)

### Trace Hierarchy

**Note**: Due to LangGraph's async execution model, AgentCore may create **multiple separate traces** instead of one unified trace. This is expected behavior. Use **baggage attributes** (`session.id`, `user.id`) to correlate related traces.

```
Trace 1: Parse Voice Personality (session.id=agent-creation-123)
└── DSPy LLM Call

Trace 2: Parse SOP (session.id=agent-creation-123)
└── DSPy LLM Call

Trace 3: Draft Plan (session.id=agent-creation-123)
└── DSPy LLM Call

... (multiple traces, all with same session.id)
```

To view all traces for a single agent creation:
1. Go to CloudWatch → X-Ray → Traces
2. Filter by `session.id = "agent-creation-{agent_id}-{uuid}"`
3. All related traces will be shown together

## Configuration

### AgentCore Automatic Configuration

AgentCore automatically configures OpenTelemetry with these attributes:

```json
{
  "service.name": "oratio_agentcreator.DEFAULT",
  "cloud.provider": "aws",
  "cloud.platform": "aws_bedrock_agentcore",
  "cloud.region": "us-east-1",
  "deployment.environment.name": "bedrock-agentcore:default",
  "telemetry.sdk.name": "opentelemetry",
  "telemetry.sdk.language": "python",
  "telemetry.auto.version": "0.10.1-aws"
}
```

Traces are automatically exported to:
- **AWS CloudWatch Logs**: `/aws/bedrock-agentcore/runtimes/{runtime-name}`
- **AWS X-Ray**: Integrated automatically

### No Environment Variables Needed!

Unlike traditional OpenTelemetry setups, you **do NOT need** to set:
- ❌ `OTEL_EXPORTER_OTLP_ENDPOINT` (AgentCore handles this)
- ❌ `OTEL_SERVICE_NAME` (AgentCore sets this)
- ❌ `OTEL_RESOURCE_ATTRIBUTES` (AgentCore configures this)

The only thing you control is **baggage context** in your application code.

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

1. **Use baggage for session tracking**: Always call `set_session_context()` with session_id and user_id
2. **View traces in CloudWatch**: Navigate to CloudWatch → X-Ray traces or ServiceLens
3. **Filter by session.id**: Use baggage attributes to find specific agent creation flows
4. **Monitor AgentCore logs**: Check `/aws/bedrock-agentcore/runtimes/{runtime-name}` for issues
5. **Don't override instrumentation**: Let AgentCore handle TracerProvider and instrumentors

## Troubleshooting

### Warning: "Overriding of current TracerProvider is not allowed"

**This is expected!** AgentCore already set up a TracerProvider. Remove any code that creates a new `TracerProvider` or calls `trace_api.set_tracer_provider()`.

### Warning: "Attempting to instrument while already instrumented"

**This is expected!** AgentCore already instrumented DSPy. Remove any calls to `DSPyInstrumentor().instrument()`.

### Traces not appearing in CloudWatch

1. Check CloudWatch Logs: `/aws/bedrock-agentcore/runtimes/{your-runtime-name}`
2. Verify AgentCore runtime is deployed and active
3. Check IAM permissions for CloudWatch Logs and X-Ray

### Missing session.id or user.id in spans

1. Ensure `set_session_context()` is called in `agent_runtime.py`
2. Check that `session_id` and `user_id` are passed in the invocation payload
3. Verify baggage is attached before the pipeline runs

### Performance impact

- OpenTelemetry has minimal overhead (<1% CPU, <10MB memory)
- AgentCore uses BatchSpanProcessor for async export
- No additional configuration needed

## References

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/languages/python/)
- [AWS ADOT Documentation](https://aws-otel.github.io/)
- [OpenTelemetry Baggage Spec](https://opentelemetry.io/docs/specs/otel/baggage/api/)
- [DSPy Instrumentation](https://github.com/Arize-ai/openinference/tree/main/python/instrumentation/openinference-instrumentation-dspy)
- [AWS Bedrock Agent Observability Sample](https://github.com/aws-samples/amazon-bedrock-samples/tree/main/evaluation-observe/open-telemetry-instrumentation)

