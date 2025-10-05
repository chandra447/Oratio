# Technology Stack

## Architecture

Three-tier architecture:
- **Frontend**: Next.js 14 with TypeScript, Tailwind CSS
- **Backend**: FastAPI with Python
- **Infrastructure**: AWS services (DynamoDB, S3, Lambda, Step Functions, Bedrock, AgentCore)

## Frontend Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **UI Components**: shadcn/ui (https://ui.shadcn.com/)
- **Component Primitives**: Radix UI
- **Styling**: Tailwind CSS with custom design system
- **Icons**: Lucide React
- **Forms**: React Hook Form with Zod validation
- **State Management**: React hooks and context
- **API Client**: Fetch/Axios for REST, native WebSocket API
- **Testing**: React Testing Library, Playwright for E2E

## Backend Stack

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Authentication**: AWS Cognito with JWT tokens
- **Database**: DynamoDB (NoSQL)
- **Storage**: S3 for documents, recordings, and generated code
- **Orchestration**: Step Functions for agent creation workflow
- **AI/ML**: AWS Bedrock (Nova Sonic for voice, Claude for text)
- **Agent Platform**: AWS AgentCore for agent deployment
- **Notifications**: SES for email, SNS for alerts
- **Infrastructure as Code**: AWS CDK with Python
- **Testing**: pytest for unit tests, integration tests

## AWS Services

- **Cognito**: User authentication and JWT token management
- **DynamoDB**: Tables for users, agents, sessions, API keys, notifications
- **S3**: Knowledge bases, generated code, audio recordings
- **Lambda**: KB Provisioner, AgentCreator Invoker, AgentCore Deployer
- **Step Functions**: Agent creation workflow orchestration
- **Bedrock**: Nova Sonic (voice), Claude (text), Knowledge Bases (RAG)
- **AgentCore**: Meta-agent and customer agent deployment
- **SES/SNS**: Email and push notifications
- **CloudWatch**: Logging and monitoring
- **Amplify**: Frontend hosting with CI/CD

## Development Commands

### Frontend
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Run E2E tests
npm run test:e2e
```

### Backend
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=.
```

### Infrastructure (Python CDK)
```bash
# Install AWS CDK CLI globally
npm install -g aws-cdk

# Install Python CDK dependencies
pip install aws-cdk-lib constructs

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy AWS infrastructure
cdk deploy

# Synthesize CloudFormation template
cdk synth

# Destroy infrastructure
cdk destroy

# List all stacks
cdk list
```

## Key Design Patterns

- **Multi-tenancy**: All data access includes userId for strict tenant isolation
- **API Key Authentication**: Hash-based validation for agent endpoints
- **WebSocket Updates**: Real-time dashboard updates for sessions and notifications
- **Step Functions Orchestration**: Reliable agent creation pipeline with error handling
- **Meta-Agent Pipeline**: AgentCreator generates custom agent code from SOPs
