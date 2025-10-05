# Oratio Infrastructure

AWS CDK infrastructure code for Oratio platform using Python.

## Overview

This directory contains AWS CDK stacks that define all infrastructure resources for the Oratio platform:

- **DynamoDB Tables**: Users, agents, sessions, API keys, notifications
- **S3 Buckets**: Knowledge bases, generated code, recordings
- **Cognito**: User authentication and management
- **Lambda Functions**: KB provisioner, AgentCreator invoker, AgentCore deployer
- **Step Functions**: Agent creation workflow orchestration

## Prerequisites

- Python 3.11+
- uv package manager
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS credentials configured

## Installation

```bash
# Install dependencies
uv sync

# Install dev dependencies
uv sync --extra dev
```

## CDK Commands

```bash
# List all stacks
cdk list

# Synthesize CloudFormation template
cdk synth

# Show differences between deployed and local
cdk diff

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy OratioAuthStack

# Destroy all stacks
cdk destroy --all

# Bootstrap (first time only)
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

## Stack Organization

### OratioAuthStack
- Cognito User Pool for authentication
- User Pool Client for web application

### OratioDatabaseStack
- DynamoDB tables with GSIs for efficient queries
- Point-in-time recovery enabled
- Pay-per-request billing mode

### OratioStorageStack
- S3 buckets with encryption and versioning
- Lifecycle policies for cost optimization
- Tenant-isolated storage structure

### OratioLambdaStack
- Lambda functions for agent creation workflow
- IAM roles and policies
- Environment variables configuration

### OratioWorkflowStack
- Step Functions state machine
- Agent creation orchestration
- Error handling and retries

## Environment Variables

Set these environment variables before deploying:

```bash
export CDK_DEFAULT_ACCOUNT=your-account-id
export CDK_DEFAULT_REGION=us-east-1
```

## Development

### Code Quality

```bash
# Run linting
uv run ruff check .

# Format code
uv run ruff format .

# Type checking
uv run mypy .
```

### Testing

```bash
# Synthesize to check for errors
cdk synth

# Validate all stacks
cdk diff
```

## Deployment

### First Time Setup

```bash
# Bootstrap CDK (one-time per account/region)
cdk bootstrap

# Deploy all stacks
cdk deploy --all
```

### Updates

```bash
# Check what will change
cdk diff

# Deploy changes
cdk deploy --all
```

## Stack Dependencies

```
OratioAuthStack (independent)
OratioDatabaseStack (independent)
OratioStorageStack (independent)
OratioLambdaStack (depends on Database + Storage)
OratioWorkflowStack (depends on Lambda)
```

## Resources Created

- 5 DynamoDB tables with GSIs
- 3 S3 buckets with lifecycle policies
- 1 Cognito User Pool with client
- 3 Lambda functions
- 1 Step Functions state machine
- IAM roles and policies

## Cost Optimization

- DynamoDB: Pay-per-request billing
- S3: Lifecycle transitions to IA and Glacier
- Lambda: Right-sized memory allocation
- Cognito: Free tier for up to 50,000 MAUs

## Security

- All S3 buckets block public access
- Encryption at rest enabled
- IAM least privilege policies
- Cognito password policies enforced
- Point-in-time recovery for DynamoDB
