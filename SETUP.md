# Oratio Platform Setup Guide

This guide walks you through setting up the Oratio platform for development.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js 20+**: For frontend development
- **Python 3.11+**: For backend and infrastructure
- **uv**: Python package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- **AWS CDK CLI**: `npm install -g aws-cdk`
- **AWS CLI**: Configured with credentials
- **Docker** (optional): For containerized development

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd oratio

# Install frontend dependencies
cd frontend
npm install
cd ..

# Install backend dependencies
cd backend
uv sync
cd ..

# Install infrastructure dependencies
cd infrastructure
uv sync
cd ..
```

### 2. Configure Environment

```bash
# Backend configuration
cd backend
cp .env.example .env
# Edit .env with your AWS credentials and configuration
cd ..
```

### 3. Deploy Infrastructure (Optional for local development)

```bash
cd infrastructure

# Bootstrap CDK (first time only)
export CDK_DEFAULT_ACCOUNT=your-account-id
export CDK_DEFAULT_REGION=us-east-1
cdk bootstrap

# Deploy all stacks
cdk deploy --all
```

### 4. Run Development Servers

#### Option A: Run Locally

```bash
# Terminal 1 - Frontend
cd frontend
npm run dev
# Frontend: http://localhost:3000

# Terminal 2 - Backend
cd backend
uv run uvicorn main:app --reload
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

#### Option B: Run with Docker

```bash
# From project root
docker-compose up
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## Project Structure

```
oratio/
├── frontend/              # Next.js 14 application
│   ├── src/
│   │   ├── app/          # App router pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utilities
│   └── package.json
│
├── backend/               # FastAPI application
│   ├── models/           # Data models
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── aws/              # AWS client wrappers
│   ├── main.py           # App entry point
│   └── pyproject.toml
│
├── infrastructure/        # AWS CDK (Python)
│   ├── stacks/           # CDK stack definitions
│   │   ├── dynamodb_stack.py
│   │   ├── s3_stack.py
│   │   ├── cognito_stack.py
│   │   ├── lambda_stack.py
│   │   └── stepfunctions_stack.py
│   ├── app.py            # CDK app entry point
│   └── pyproject.toml
│
└── lambdas/              # Lambda function code
    ├── kb_provisioner/
    ├── agentcreator_invoker/
    └── agentcore_deployer/
```

## Development Workflow

### Frontend Development

```bash
cd frontend

# Development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Format code
npm run format

# Build for production
npm run build
```

### Backend Development

```bash
cd backend

# Development server
uv run uvicorn main:app --reload

# Linting
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy .

# Run tests
uv run pytest
```

### Infrastructure Development

```bash
cd infrastructure

# Synthesize CloudFormation
cdk synth

# Show changes
cdk diff

# Deploy changes
cdk deploy --all

# Linting
uv run ruff check .

# Format code
uv run ruff format .
```

## Verification

### Check Frontend

```bash
curl http://localhost:3000
# Should return Next.js page
```

### Check Backend

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy"}
```

### Check Infrastructure

```bash
cd infrastructure
cdk synth --quiet
# Should synthesize without errors
```

## Next Steps

1. **Add shadcn/ui components** to frontend:
   ```bash
   cd frontend
   npx shadcn@latest init
   npx shadcn@latest add button card form
   ```

2. **Implement authentication** with Cognito integration

3. **Build agent creation workflow** with Step Functions

4. **Integrate Bedrock** for AI capabilities

5. **Implement voice service** with Nova Sonic

## Troubleshooting

### Frontend Issues

- **Port 3000 in use**: Change port with `npm run dev -- -p 3001`
- **Module not found**: Run `npm install` again
- **Type errors**: Run `npm run type-check` to see details

### Backend Issues

- **Port 8000 in use**: Change port in `main.py` or use `--port 8001`
- **Import errors**: Run `uv sync` to reinstall dependencies
- **AWS credentials**: Ensure `~/.aws/credentials` is configured

### Infrastructure Issues

- **CDK bootstrap error**: Ensure AWS credentials are configured
- **Synth errors**: Check Python syntax and imports
- **Deploy failures**: Check AWS permissions and quotas

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [AWS CDK Python Documentation](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [uv Documentation](https://docs.astral.sh/uv/)

## Support

For issues or questions, refer to:
- Project documentation in `.kiro/specs/oratio-platform/`
- README files in each directory
- AWS CDK examples and patterns
