# Code Review Checklist

## Quick Review Guide

### ✅ Infrastructure (CDK)

**Files to Review:**
- [ ] `infrastructure/cdk_constructs/database.py` - KB table added
- [ ] `infrastructure/cdk_constructs/compute.py` - All 4 Lambdas configured
- [ ] `infrastructure/cdk_constructs/workflow.py` - Step Functions with error handling
- [ ] `infrastructure/stacks/oratio_stack.py` - Everything wired together

**Key Points:**
- KB table has userId GSI
- Lambda IAM permissions are correct
- Step Functions has retries and error handling
- Environment variables configured

### ✅ Backend Models

**Files to Review:**
- [ ] `backend/models/agent.py` - Agent + VoicePersonality models
- [ ] `backend/models/knowledge_base.py` - KB models

**Key Points:**
- VoicePersonality has all fields (identity, task, demeanor, tone, etc.)
- Agent model includes voice_personality field
- Enums for status and type

### ✅ Backend Services

**Files to Review:**
- [ ] `backend/services/agent_service.py` - Agent CRUD
- [ ] `backend/services/knowledge_base_service.py` - KB CRUD
- [ ] `backend/services/s3_service.py` - File uploads with tagging

**Key Points:**
- Tenant isolation (userId in all queries)
- Error handling
- Status updates

### ✅ Backend API

**Files to Review:**
- [ ] `backend/routers/agents.py` - All 3 endpoints

**Key Points:**
- POST /api/agents accepts voice_personality
- Multipart form data handling
- Step Functions triggered
- Tenant isolation enforced

### ✅ AWS Clients

**Files to Review:**
- [ ] `backend/aws/s3_client.py` - Tagging support
- [ ] `backend/aws/dynamodb_client.py` - CRUD operations
- [ ] `backend/aws/bedrock_client.py` - KB creation with tags
- [ ] `backend/aws/stepfunctions_client.py` - Workflow execution

**Key Points:**
- S3 uploads include tags (userId, agentId, resourceType)
- DynamoDB queries use GSI
- Bedrock KB creation includes tags

### ✅ Lambda Functions

**Files to Review:**
- [ ] `lambdas/kb_provisioner/handler.py` - ~200 lines
- [ ] `lambdas/agentcreator_invoker/handler.py` - ~150 lines (LEAN!)
- [ ] `lambdas/code_checker/handler.py` - ~60 lines
- [ ] `lambdas/agentcore_deployer/handler.py` - ~200 lines

**Key Points:**
- No placeholder logic in agentcreator_invoker
- Proper error handling
- Status updates to DynamoDB
- Resource tagging

## Quick Test Commands

### 1. Check Models
```bash
cd backend
python -c "from models.agent import VoicePersonality, Agent; print('✅ Models OK')"
```

### 2. Check Services
```bash
python -c "from services.agent_service import AgentService; print('✅ Services OK')"
```

### 3. Check API
```bash
python -c "from routers.agents import router; print('✅ Router OK')"
```

### 4. Validate CDK
```bash
cd infrastructure
cdk synth > /dev/null && echo "✅ CDK OK"
```

## Common Issues to Check

### ❌ Import Errors
- [ ] All imports use correct paths
- [ ] No circular dependencies
- [ ] Models exported in __init__.py

### ❌ Environment Variables
- [ ] All Lambdas have required env vars
- [ ] Config.py has all settings
- [ ] No hardcoded values

### ❌ Tenant Isolation
- [ ] All DynamoDB queries include userId
- [ ] S3 paths include userId
- [ ] API endpoints validate ownership

### ❌ Error Handling
- [ ] Try-catch blocks in all Lambdas
- [ ] Status updates on failure
- [ ] Proper logging

## Files Count

```
Infrastructure: 4 files
Backend Models: 3 files
Backend Services: 4 files
Backend Routers: 1 file
Backend AWS Clients: 5 files
Lambda Functions: 4 files
---
Total: 21 core files
```

## Lines of Code

```
Infrastructure: ~500 lines
Backend: ~2,500 lines
Lambdas: ~800 lines
---
Total: ~3,800 lines
```

## Review Time Estimate

- Quick scan: 15 minutes
- Detailed review: 45 minutes
- Testing: 30 minutes
- **Total: ~90 minutes**

## Priority Review Order

1. **Lambda Functions** (most critical)
   - agentcreator_invoker/handler.py
   - kb_provisioner/handler.py
   - agentcore_deployer/handler.py

2. **API Endpoint**
   - routers/agents.py

3. **Models**
   - models/agent.py (VoicePersonality)

4. **Infrastructure**
   - cdk_constructs/workflow.py
   - cdk_constructs/compute.py

5. **Services** (if time permits)
   - services/agent_service.py
   - services/s3_service.py

## What to Skip

- ❌ Test files (optional)
- ❌ Documentation files
- ❌ Summary files
- ❌ AWS client implementations (standard boto3)

## Key Questions to Answer

1. ✅ Does AgentCreator Invoker properly invoke AgentCore agent?
2. ✅ Is voice_personality properly passed through the workflow?
3. ✅ Are all resources tagged correctly?
4. ✅ Is tenant isolation enforced everywhere?
5. ✅ Does Step Functions have proper error handling?

## Sign-Off

- [ ] Infrastructure reviewed
- [ ] Backend reviewed
- [ ] Lambda functions reviewed
- [ ] No placeholder logic
- [ ] Clean and lean code
- [ ] Ready for deployment

---

**Reviewer**: _______________
**Date**: _______________
**Status**: ⬜ Approved / ⬜ Changes Requested
