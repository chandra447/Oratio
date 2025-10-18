# Oratio Infrastructure

AWS CDK infrastructure for Oratio platform with GitHub Actions CI/CD.

## Quick Start

### 1. Setup AWS OIDC (One-Time)

Follow **[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)** for complete setup instructions.

**Quick commands**:
```bash
# 1. Create OIDC provider
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# 2. Create deployment role (see GITHUB_ACTIONS_SETUP.md for policy files)
aws iam create-role --role-name GitHubActionsDeploymentRole --assume-role-policy-document file://github-actions-trust-policy.json

# 3. Create AgentCore execution role
aws iam create-role --role-name OratioAgentCoreExecutionRole --assume-role-policy-document file://agentcore-trust-policy.json
```

### 2. Configure GitHub Secrets

In GitHub → Settings → Secrets and variables → Actions:

| Name | Type | Value |
|------|------|-------|
| `AWS_ACCOUNT_ID` | Variable | Your AWS account ID |
| `AWS_ROLE_ARN` | Secret | `arn:aws:iam::ACCOUNT_ID:role/GitHubActionsDeploymentRole` |
| `AGENTCORE_EXECUTION_ROLE_ARN` | Secret | `arn:aws:iam::ACCOUNT_ID:role/OratioAgentCoreExecutionRole` |

### 3. Deploy

```bash
# Push to trigger deployment
git push origin develop  # → staging
git push origin main     # → production (requires approval)
```

Or manually trigger via GitHub Actions UI.

## What Gets Deployed

### Infrastructure
- **DynamoDB**: agents, knowledge-bases, api-keys, sessions, notifications
- **S3**: knowledge-bases, generated-code, recordings
- **Lambda**: kb-provisioner, agentcreator-invoker, agentcore-deployer, code-checker
- **Step Functions**: Agent creation workflow
- **ECR**: Docker image repositories

### Docker Images
- **oratio-agentcreator**: Meta-agent for generating agents
- **oratio-backend**: FastAPI backend services

### Bedrock AgentCore
- **AgentCreator**: Meta-agent deployed and ready

## Project Structure

```
infrastructure/
├── app.py                      # CDK app entry point
├── cdk_constructs/
│   ├── compute.py             # Lambda functions
│   ├── database.py            # DynamoDB tables
│   └── storage.py             # S3 buckets
├── GITHUB_ACTIONS_SETUP.md    # Complete OIDC setup guide
├── DEPLOYMENT_CHECKLIST.md    # Deployment verification
└── README.md                  # This file
```

## GitHub Actions Workflow

The workflow (`.github/workflows/deploy-infrastructure.yml`) performs:

1. ✅ Configure AWS credentials via OIDC
2. ✅ Create ECR repositories
3. ✅ Build and push Docker images
4. ✅ CDK bootstrap (if needed)
5. ✅ CDK diff (preview changes)
6. ✅ CDK deploy (deploy infrastructure)
7. ✅ Deploy AgentCreator to Bedrock AgentCore
8. ✅ Update Lambda environment variables
9. ✅ Create deployment tag

## Local Development

### Prerequisites
```bash
# Install CDK CLI
npm install -g aws-cdk

# Install Python dependencies
pip install -r requirements.txt
```

### Commands
```bash
# Synthesize CloudFormation
cdk synth

# Preview changes
cdk diff

# Deploy (requires AWS credentials)
cdk deploy --all

# Destroy infrastructure
cdk destroy --all
```

## Environment Variables

### Lambda: kb-provisioner
- `AGENTS_TABLE`: DynamoDB agents table
- `KB_TABLE`: DynamoDB knowledge bases table
- `KB_BUCKET`: S3 bucket for knowledge base documents

### Lambda: agentcreator-invoker
- `AGENTS_TABLE`: DynamoDB agents table
- `KB_TABLE`: DynamoDB knowledge bases table
- `CODE_BUCKET`: S3 bucket for generated code
- `AGENTCREATOR_AGENT_ID`: AgentCreator agent ID (set by GitHub Actions)
- `AGENTCREATOR_AGENT_ALIAS_ID`: AgentCreator alias (production)
- `AWS_REGION`: AWS region (us-east-1)

### Lambda: agentcore-deployer
- `AGENTS_TABLE`: DynamoDB agents table
- `CODE_BUCKET`: S3 bucket for generated code
- `AWS_REGION`: AWS region (us-east-1)

### Lambda: code-checker
- `CODE_BUCKET`: S3 bucket for generated code

## Verification

After deployment, verify:

```bash
# Check Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `oratio-`)].FunctionName'

# Check DynamoDB tables
aws dynamodb list-tables --query 'TableNames[?starts_with(@, `oratio-`)]'

# Check S3 buckets
aws s3 ls | grep oratio

# Check AgentCreator agent
aws bedrock-agent list-agents --query 'agentSummaries[?agentName==`oratio-agentcreator`]'
```

See **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** for complete verification steps.

## Troubleshooting

### Common Issues

**OIDC authentication failed**
- Verify OIDC provider exists
- Check trust policy has correct GitHub repo path
- Ensure role ARN is correct in GitHub secrets

**CDK deploy failed**
- Check IAM permissions
- Verify CDK bootstrap completed
- Review CloudFormation events

**AgentCreator deployment failed**
- Verify AgentCore execution role exists
- Check Bedrock permissions
- Ensure Docker image pushed successfully

See **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** for detailed troubleshooting.

## Cost Estimation

Approximate monthly costs:
- DynamoDB: $5-20
- S3: $1-10
- Lambda: $5-50
- ECR: $1-5
- Bedrock AgentCore: $0.10-1.00 per 1000 invocations
- CloudWatch: $1-10

**Total**: ~$15-100/month depending on usage

## Security

- ✅ OIDC authentication (no long-lived credentials)
- ✅ Least privilege IAM roles
- ✅ Environment protection rules
- ✅ Encrypted S3 buckets
- ✅ VPC isolation (optional)

## Documentation

- **[GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)** - Complete OIDC and IAM setup
- **[DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)** - Deployment verification and troubleshooting
- **[../agent-creator/ARCHITECTURE.md](../agent-creator/ARCHITECTURE.md)** - System architecture

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review GitHub Actions logs
3. See troubleshooting guides
4. Contact team lead

---

**Last Updated**: January 2025
