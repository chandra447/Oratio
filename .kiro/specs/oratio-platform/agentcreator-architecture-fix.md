# AgentCreator Architecture - Corrected

## Overview
Fixed the AgentCreator Invoker Lambda to properly invoke the **pre-deployed AgentCreator meta-agent on AWS AgentCore** instead of trying to import a local Python module.

## Correct Architecture

```
AgentCreator Invoker Lambda
    ↓
Invokes via bedrock-agent-runtime
    ↓
AgentCreator Meta-Agent (deployed on AgentCore)
    ├─ Built with DSPy + LangGraph
    ├─ Has access to Code Interpreter
    ├─ Has access to Strands SDK
    └─ Generates agent_file.py + prompt
    ↓
Returns JSON response
    ↓
Lambda uploads to S3
```

## Key Changes

### Before (Incorrect)
```python
# Tried to import local module
from agentcreator.pipeline import AgentCreatorPipeline
pipeline = AgentCreatorPipeline()
result = pipeline.run(input)
```

### After (Correct)
```python
# Invokes pre-deployed AgentCore agent
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")

response = bedrock_agent_runtime.invoke_agent(
    agentId=AGENTCREATOR_AGENT_ID,
    agentAliasId=AGENTCREATOR_AGENT_ALIAS_ID,
    sessionId=session_id,
    inputText=json.dumps(agent_creator_input),
)

# Process streaming response
for event_chunk in response.get("completion", []):
    chunk = event_chunk.get("chunk")
    if chunk:
        chunk_bytes = chunk.get("bytes")
        chunk_text = chunk_bytes.decode("utf-8")
        agent_code += chunk_text

# Parse JSON response
result = json.loads(agent_code)
agent_code = result.get("agent_code")
generated_prompt = result.get("generated_prompt")
```

## AgentCreator Meta-Agent

The AgentCreator is a **separate agent deployed on AgentCore** that:

1. **Receives Input** (via invoke_agent):
   ```json
   {
     "sop": "Handle customer inquiries...",
     "knowledge_base_description": "Use for product info",
     "human_handoff_description": "Escalate for refunds",
     "bedrock_knowledge_base_id": "kb-123",
     "agent_id": "agent-456",
     "voice_personality": {
       "identity": "Friendly customer service rep",
       "demeanor": "Patient and empathetic",
       ...
     }
   }
   ```

2. **Runs DSPy + LangGraph Pipeline**:
   - SOP Parser → extracts requirements
   - Plan Drafter → creates architecture
   - Plan Reviewer → reviews plan (2+ cycles)
   - Code Generator → generates Strands agent code
   - Code Reviewer → validates code

3. **Returns Output**:
   ```json
   {
     "agent_code": "# Python code for Strands agent...",
     "generated_prompt": "You are a customer service agent..."
   }
   ```

## Lambda Handler Flow

```python
def lambda_handler(event, context):
    # 1. Extract parameters
    user_id = event.get("userId")
    agent_id = event.get("agentId")
    sop = event.get("sop")
    voice_personality = get_from_dynamodb()  # Get personality config
    
    # 2. Check if AgentCreator is deployed
    if not AGENTCREATOR_AGENT_ID:
        # Use placeholder (for MVP/testing)
        agent_code, prompt = generate_placeholder_agent(...)
    else:
        # 3. Invoke AgentCreator meta-agent
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENTCREATOR_AGENT_ID,
            agentAliasId=AGENTCREATOR_AGENT_ALIAS_ID,
            sessionId=f"agent-creation-{agent_id}",
            inputText=json.dumps({
                "sop": sop,
                "voice_personality": voice_personality,
                ...
            })
        )
        
        # 4. Process streaming response
        agent_code = ""
        for chunk in response.get("completion", []):
            agent_code += chunk["chunk"]["bytes"].decode("utf-8")
        
        # 5. Parse JSON
        result = json.loads(agent_code)
        agent_code = result["agent_code"]
        prompt = result["generated_prompt"]
    
    # 6. Upload to S3
    s3_client.put_object(
        Bucket=CODE_BUCKET,
        Key=f"{user_id}/{agent_id}/agent_file.py",
        Body=agent_code.encode("utf-8"),
        Tagging=f"userId={user_id}&agentId={agent_id}"
    )
    
    # 7. Update DynamoDB
    agents_table.update_item(...)
    
    return {...}
```

## Environment Variables

```python
AGENTS_TABLE = "oratio-agents"
KB_TABLE = "oratio-knowledgebases"
CODE_BUCKET = "oratio-generated-code"
AGENTCREATOR_AGENT_ID = ""  # Set after deploying AgentCreator
AGENTCREATOR_AGENT_ALIAS_ID = "TSTALIASID"
```

## IAM Permissions

```python
{
    "Effect": "Allow",
    "Action": [
        "bedrock:InvokeAgent",
        "bedrock:InvokeModel"
    ],
    "Resource": "*"
}
```

## Placeholder Agent

Until AgentCreator is deployed, the Lambda uses a placeholder that:
- Generates basic Python code structure
- Creates a system prompt from SOP + personality
- Includes voice personality in the prompt
- Stores to S3 for testing

## Voice Personality Integration

The Lambda now:
1. Retrieves `voice_personality` from DynamoDB
2. Passes it to AgentCreator (or placeholder)
3. AgentCreator uses it to generate a rich system prompt

Example generated prompt with personality:
```
You are Sarah, an experienced customer service representative.
Your primary task is to help customers with orders and returns.

Personality:
- Be patient and empathetic in all interactions
- Use a warm and conversational tone
- Maintain a professional level of formality
- Show moderate enthusiasm
- Occasionally use natural filler words like "um" or "let me see"
- Speak at a moderate pace for clarity

Important Instructions:
- Always repeat back names and phone numbers for confirmation
- If a customer corrects any detail, acknowledge it
...
```

## Deployment Steps

### 1. Deploy AgentCreator Meta-Agent (Separate Task)
```bash
# Build DSPy + LangGraph pipeline
# Deploy to AgentCore
# Get agent ID and alias ID
```

### 2. Update Lambda Environment Variable
```bash
aws lambda update-function-configuration \
  --function-name oratio-agentcreator-invoker \
  --environment Variables="{
    AGENTCREATOR_AGENT_ID=<agent-id>,
    AGENTCREATOR_AGENT_ALIAS_ID=<alias-id>
  }"
```

### 3. Test Invocation
```bash
# Create test agent through API
# Check CloudWatch logs for AgentCreator invocation
# Verify generated code in S3
```

## Benefits of This Architecture

1. **Separation of Concerns**: AgentCreator is a separate, reusable agent
2. **Scalability**: AgentCore handles scaling and execution
3. **Observability**: AgentCore provides built-in monitoring
4. **Flexibility**: Can update AgentCreator without redeploying Lambda
5. **Testing**: Can test AgentCreator independently
6. **Fallback**: Placeholder works until AgentCreator is ready

## Next Steps

1. **Implement AgentCreator Meta-Agent** with DSPy + LangGraph
2. **Deploy to AgentCore** and get agent ID
3. **Update Lambda environment variable** with agent ID
4. **Test end-to-end** agent creation workflow
5. **Monitor and optimize** AgentCreator performance

## Files Modified

- `lambdas/agentcreator_invoker/handler.py` - Fixed to invoke AgentCore agent
- `infrastructure/cdk_constructs/compute.py` - Added environment variables
