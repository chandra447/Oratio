# Project Structure

## Repository Organization

```
oratio/
├── frontend/                 # Next.js application
│   ├── app/                 # App router pages
│   │   ├── (auth)/         # Authentication pages
│   │   ├── (dashboard)/    # Dashboard pages
│   │   └── api/            # API routes (if needed)
│   ├── components/          # React components
│   ├── lib/                # Utilities and API client
│   ├── public/             # Static assets
│   └── styles/             # Global styles
│
├── backend/                 # FastAPI application
│   ├── main.py             # App entry point
│   ├── config.py           # Configuration
│   ├── dependencies.py     # Shared dependencies
│   ├── models/             # Data models
│   │   ├── user.py
│   │   ├── agent.py
│   │   ├── session.py
│   │   ├── notification.py
│   │   └── api_key.py
│   ├── routers/            # API endpoints
│   │   ├── auth.py
│   │   ├── agents.py
│   │   ├── sessions.py
│   │   ├── notifications.py
│   │   ├── api_keys.py
│   │   └── websocket.py
│   ├── services/           # Business logic
│   │   ├── auth_service.py
│   │   ├── agent_service.py
│   │   ├── session_service.py
│   │   ├── notification_service.py
│   │   └── api_key_service.py
│   ├── aws/                # AWS client wrappers
│   │   ├── dynamodb_client.py
│   │   ├── s3_client.py
│   │   ├── stepfunctions_client.py
│   │   ├── bedrock_client.py
│   │   └── ses_client.py
│   └── utils/              # Helper functions
│
├── infrastructure/          # AWS CDK code (Python)
│   ├── app.py              # CDK app entry point
│   ├── cdk.json            # CDK configuration
│   ├── requirements.txt    # CDK dependencies
│   └── stacks/             # CDK stack definitions
│       ├── __init__.py
│       ├── dynamodb_stack.py
│       ├── s3_stack.py
│       ├── lambda_stack.py
│       ├── stepfunctions_stack.py
│       ├── cognito_stack.py
│       └── bedrock_stack.py
│
├── lambdas/                # Lambda function code
│   ├── kb_provisioner/
│   ├── agentcreator_invoker/
│   ├── agentcore_deployer/
│   └── notification_handler/
│
├── voice_service/          # Voice WebSocket service
│   └── main.py
│
├── text_service/           # Text REST service
│   └── main.py
│
└── docs/                   # Documentation
```

## Key Conventions

### File Naming
- **Python**: snake_case for files and functions
- **TypeScript**: PascalCase for components, camelCase for utilities
- **Models**: Singular nouns (user.py, agent.py)
- **Services**: Descriptive names with _service suffix

### Code Organization
- **Separation of Concerns**: Models, services, routers are strictly separated
- **AWS Clients**: Wrapped in dedicated modules for testability
- **Business Logic**: Lives in service layer, not in routers
- **Validation**: Pydantic models for request/response validation

### Database Schema
- **DynamoDB Tables**: Prefixed with "oratio-" (oratio-users, oratio-agents)
- **Primary Keys**: userId as PK, resource-specific ID as SK
- **GSI**: Created for common query patterns (agentId-index, userId-timestamp-index)

### S3 Structure
```
oratio-knowledge-bases/
  {userId}/
    {agentId}/
      *.pdf, *.md

oratio-generated-code/
  {agentId}/
    agent.py

oratio-recordings/
  {sessionId}/
    audio.wav
```

### API Endpoints
- **Authentication**: /api/auth/*
- **Agents**: /api/agents/*
- **Sessions**: /api/sessions/*
- **Notifications**: /api/notifications/*
- **API Keys**: /api/api-keys/*
- **WebSocket**: /ws/dashboard

### Environment Variables
- AWS credentials and region
- DynamoDB table names
- S3 bucket names
- Cognito User Pool ID
- Step Functions ARN
- Bedrock model IDs
