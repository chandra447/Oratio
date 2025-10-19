# Chameleon - Dynamic Agent Loader

Chameleon is a generic AgentCore Runtime that dynamically loads and executes Strands agents from S3. It acts as a universal runtime for all generated agents in the Oratio platform.

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Chameleon Runtime                  │
│  (Single AgentCore deployment for all agents)       │
└─────────────────────────────────────────────────────┘
                         │
                         │ Fetch agent code
                         ▼
                    ┌─────────┐
                    │   S3    │
                    │ Bucket  │
                    └─────────┘
                         │
                         │ Contains generated agent code
                         ▼
              ┌──────────────────────┐
              │  agent_<id>.py       │
              │  - System prompt     │
              │  - KB configuration  │
              │  - Tool definitions  │
              └──────────────────────┘
```

## How It Works

1. **Invocation**: FastAPI receives a request with `agent_id` and `user_id`
2. **Fetch Metadata**: Queries DynamoDB to get agent configuration (S3 key, memory_id)
3. **Download Code**: Fetches the generated agent code from S3
4. **Dynamic Loading**: Uses `importlib` to load the agent code at runtime
5. **Memory Injection**: Creates `MemoryHookProvider` and injects it into the agent
6. **Execution**: Runs the agent with the user's input
7. **Response**: Returns the agent's output

## Key Features

- ✅ **Single Runtime**: One AgentCore deployment serves all generated agents
- ✅ **Dynamic Loading**: No redeployment needed when agents are created/updated
- ✅ **Memory Management**: Automatic short-term memory via `MemoryHookProvider`
- ✅ **Isolation**: Each agent execution is isolated with dedicated memory
- ✅ **Observability**: OpenTelemetry tracing for all agent invocations

## Environment Variables

- `CODE_BUCKET`: S3 bucket containing generated agent code (default: `oratio-generated-code`)
- `AGENTS_TABLE`: DynamoDB table with agent metadata (default: `oratio-agents`)
- `AWS_REGION`: AWS region for services (default: `us-east-1`)

## Deployment

Chameleon is deployed using the `bedrock-agentcore-starter-toolkit`:

```bash
python infrastructure/scripts/deploy_agentcore_toolkit.py \
  --name oratio-chameleon \
  --entrypoint generic_loader.py \
  --role-arn <execution-role-arn> \
  --working-dir agent-creator/chameleon \
  --env "CODE_BUCKET=oratio-generated-code" \
  --env "AGENTS_TABLE=oratio-agents" \
  --env "AWS_REGION=us-east-1"
```

## API Endpoints

### POST `/invocations`

Invoke an agent with user input.

**Request:**
```json
{
  "input": {
    "agent_id": "57e565e9-df2c-4689-a94c-cd80d86b8d2f",
    "user_id": "3458b4c8-9051-70c6-6fad-164681e1d13e",
    "session_id": "session-123",
    "actor_id": "customer-456",
    "input_text": "What is your return policy?"
  }
}
```

**Response:**
```json
{
  "output": {
    "response": "Our return policy allows...",
    "agent_id": "57e565e9-df2c-4689-a94c-cd80d86b8d2f",
    "session_id": "session-123"
  }
}
```

### GET `/ping`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Dependencies

- **FastAPI**: HTTP server
- **Strands Agents**: Agent framework
- **boto3**: AWS SDK for S3 and DynamoDB
- **bedrock-agentcore**: Memory management
- **OpenTelemetry**: Observability

## Security

- Execution role has least-privilege access to:
  - S3 bucket (read-only for agent code)
  - DynamoDB table (read-only for agent metadata)
  - Bedrock models (invoke access)
  - Bedrock Knowledge Bases (retrieve access)
  - S3 Vectors (query access)

## Monitoring

- **CloudWatch Logs**: `/aws/bedrock-agentcore/runtimes/{runtime-id}-DEFAULT`
- **X-Ray Traces**: Distributed tracing for all agent invocations
- **GenAI Observability**: CloudWatch GenAI dashboard for agent metrics

