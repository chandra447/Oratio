# AWS Implementation Details

## Bedrock AgentCore SDK

### Overview
We use the **bedrock-agentcore-sdk-python** for deploying and managing agents. AgentCore provides enterprise-grade infrastructure for agents with built-in auth, memory, observability, and security.

### Installation
```bash
pip install bedrock-agentcore
```

### Agent Deployment Pattern

```python
from bedrock_agentcore import BedrockAgentCoreApp

app = BedrockAgentCoreApp()

@app.entrypoint
def agent_handler(request):
    """
    Main agent entrypoint - this is where generated agent code runs
    """
    prompt = request.get("prompt")
    # Agent logic here
    return response

# Deploy to AgentCore
app.run()
```

### Key AgentCore Services Used

- **Runtime**: Secure and session-isolated compute for agent execution
- **Memory**: Persistent knowledge across sessions
- **Gateway**: Transform APIs into MCP tools
- **Observability**: OpenTelemetry tracing for monitoring
- **Identity**: AWS & third-party authentication

### Meta-Agent (AgentCreator) Implementation

The AgentCreator meta-agent is pre-deployed on AgentCore and generates custom agent code:

1. **SOP Parser**: Extracts requirements from user SOPs
2. **Plan Drafter**: Creates agent architecture plan
3. **Plan Reviewer**: Multi-cycle review for quality
4. **Code Generator**: Generates Python code for AgentCore
5. **Code Reviewer**: Validates generated code
6. **S3 Writer**: Stores agent.py in S3 for deployment

### Invoking AgentCore Agents

```python
import boto3

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

response = bedrock_agent_runtime.invoke_agent(
    agentId='agent-id',
    agentAliasId='alias-id',
    sessionId='session-id',
    inputText='user prompt'
)

# Process streaming response
completion = ""
for event in response.get("completion"):
    chunk = event["chunk"]
    completion += chunk["bytes"].decode()
```

## Bedrock Knowledge Bases with S3 Vectors

### Creating Knowledge Base with S3 Data Source

```python
import boto3

bedrock_agent = boto3.client('bedrock-agent', region_name='us-east-1')

# Create Knowledge Base
kb_response = bedrock_agent.create_knowledge_base(
    name='agent-knowledge-base',
    description='Knowledge base for agent',
    roleArn='arn:aws:iam::account:role/BedrockKBRole',
    knowledgeBaseConfiguration={
        'type': 'VECTOR',
        'vectorKnowledgeBaseConfiguration': {
            'embeddingModelArn': 'arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0'
        }
    },
    storageConfiguration={
        'type': 'OPENSEARCH_SERVERLESS',
        'opensearchServerlessConfiguration': {
            'collectionArn': 'collection-arn',
            'vectorIndexName': 'bedrock-knowledge-base-index',
            'fieldMapping': {
                'vectorField': 'bedrock-knowledge-base-default-vector',
                'textField': 'AMAZON_BEDROCK_TEXT_CHUNK',
                'metadataField': 'AMAZON_BEDROCK_METADATA'
            }
        }
    }
)

kb_id = kb_response['knowledgeBase']['knowledgeBaseId']

# Create S3 Data Source
data_source_response = bedrock_agent.create_data_source(
    knowledgeBaseId=kb_id,
    name='s3-data-source',
    dataSourceConfiguration={
        's3Configuration': {
            'bucketArn': 'arn:aws:s3:::oratio-knowledge-bases',
            'inclusionPrefixes': [f'{user_id}/{agent_id}/']
        }
    },
    vectorIngestionConfiguration={
        'chunkingConfiguration': {
            'chunkingStrategy': 'FIXED_SIZE',
            'fixedSizeChunkingConfiguration': {
                'maxTokens': 500,
                'overlapPercentage': 20
            }
        }
    }
)

# Start ingestion job
bedrock_agent.start_ingestion_job(
    knowledgeBaseId=kb_id,
    dataSourceId=data_source_response['dataSource']['dataSourceId']
)
```

### Using S3 Vectors Directly

For advanced vector operations, use the S3 Vectors API:

```python
import boto3
import json

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
s3vectors = boto3.client('s3vectors', region_name='us-east-1')

# Generate embedding
response = bedrock_runtime.invoke_model(
    modelId='amazon.titan-embed-text-v2:0',
    body=json.dumps({'inputText': 'query text'})
)
embedding = json.loads(response['body'].read())['embedding']

# Query vector index
results = s3vectors.query_vectors(
    vectorBucketName='oratio-knowledge-bases',
    indexName='agent-index',
    queryVector={'float32': embedding},
    topK=5,
    returnDistance=True,
    returnMetadata=True
)
```

## Nova Sonic Voice Implementation

### SDK and Dependencies

```python
# Required imports
from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.config import Config
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver
import pyaudio
import asyncio
import base64
import json
```

### Bedrock Runtime Client Setup

```python
config = Config(
    endpoint_uri=f"https://bedrock-runtime.{region}.amazonaws.com",
    region=region,
    aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
)
bedrock_client = BedrockRuntimeClient(config=config)
```

### Bidirectional Streaming Pattern

```python
# Initialize bidirectional stream
stream_response = await bedrock_client.invoke_model_with_bidirectional_stream(
    InvokeModelWithBidirectionalStreamOperationInput(
        model_id='amazon.nova-sonic-v1:0'
    )
)

# Send session start event
session_start = {
    "event": {
        "sessionStart": {
            "inferenceConfiguration": {
                "maxTokens": 1024,
                "topP": 0.9,
                "temperature": 0.7
            }
        }
    }
}
await send_event(session_start)

# Send prompt start with audio configuration
prompt_start = {
    "event": {
        "promptStart": {
            "promptName": prompt_id,
            "audioOutputConfiguration": {
                "mediaType": "audio/lpcm",
                "sampleRateHertz": 24000,
                "sampleSizeBits": 16,
                "channelCount": 1,
                "voiceId": "matthew",
                "encoding": "base64",
                "audioType": "SPEECH"
            }
        }
    }
}
await send_event(prompt_start)
```

### Audio Input Streaming

```python
# Audio configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16
CHUNK_SIZE = 1024

# Send content start for audio
content_start = {
    "event": {
        "contentStart": {
            "promptName": prompt_id,
            "contentName": content_id,
            "type": "AUDIO",
            "interactive": True,
            "role": "USER",
            "audioInputConfiguration": {
                "mediaType": "audio/lpcm",
                "sampleRateHertz": 16000,
                "sampleSizeBits": 16,
                "channelCount": 1,
                "audioType": "SPEECH",
                "encoding": "base64"
            }
        }
    }
}
await send_event(content_start)

# Stream audio chunks
audio_bytes = base64.b64encode(audio_chunk)
audio_event = {
    "event": {
        "audioInput": {
            "promptName": prompt_id,
            "contentName": content_id,
            "content": audio_bytes.decode('utf-8')
        }
    }
}
await send_event(audio_event)

# End audio content
content_end = {
    "event": {
        "contentEnd": {
            "promptName": prompt_id,
            "contentName": content_id
        }
    }
}
await send_event(content_end)
```

### Processing Audio Output

```python
# Process responses from Nova Sonic
while is_active:
    output = await stream_response.await_output()
    result = await output[1].receive()
    
    if result.value and result.value.bytes_:
        response_data = result.value.bytes_.decode('utf-8')
        json_data = json.loads(response_data)
        
        if 'event' in json_data:
            if 'audioOutput' in json_data['event']:
                # Decode base64 audio
                audio_content = json_data['event']['audioOutput']['content']
                audio_bytes = base64.b64decode(audio_content)
                
                # Play audio through PyAudio
                stream.write(audio_bytes)
            
            elif 'textOutput' in json_data['event']:
                # Handle text transcript
                text = json_data['event']['textOutput']['content']
                print(f"Assistant: {text}")
```

### Tool Use with Nova Sonic

```python
# Configure tools in prompt start
prompt_start = {
    "event": {
        "promptStart": {
            "promptName": prompt_id,
            "toolConfiguration": {
                "tools": [
                    {
                        "toolSpec": {
                            "name": "trackOrderTool",
                            "description": "Track order status by order ID",
                            "inputSchema": {
                                "json": json.dumps({
                                    "type": "object",
                                    "properties": {
                                        "orderId": {
                                            "type": "string",
                                            "description": "Order ID to track"
                                        }
                                    },
                                    "required": ["orderId"]
                                })
                            }
                        }
                    }
                ]
            }
        }
    }
}

# Handle tool use response
if 'toolUse' in json_data['event']:
    tool_name = json_data['event']['toolUse']['name']
    tool_input = json_data['event']['toolUse']['input']
    tool_use_id = json_data['event']['toolUse']['toolUseId']
    
    # Execute tool
    result = await execute_tool(tool_name, tool_input)
    
    # Send tool result back
    tool_result = {
        "event": {
            "contentStart": {
                "promptName": prompt_id,
                "contentName": f"tool-result-{tool_use_id}",
                "type": "TOOL",
                "role": "TOOL",
                "toolResultInputConfiguration": {
                    "toolUseId": tool_use_id,
                    "type": "TEXT",
                    "textInputConfiguration": {
                        "mediaType": "text/plain"
                    }
                }
            }
        }
    }
    await send_event(tool_result)
    
    # Send actual result
    result_event = {
        "event": {
            "toolResult": {
                "promptName": prompt_id,
                "contentName": f"tool-result-{tool_use_id}",
                "content": json.dumps(result)
            }
        }
    }
    await send_event(result_event)
```

### Session Management

```python
# End prompt
prompt_end = {
    "event": {
        "promptEnd": {
            "promptName": prompt_id
        }
    }
}
await send_event(prompt_end)

# End session
session_end = {
    "event": {
        "sessionEnd": {}
    }
}
await send_event(session_end)
```

## Integration with AgentCore

When Nova Sonic needs agent logic, invoke the deployed AgentCore agent:

```python
async def get_agent_response(user_input, session_id, agent_id):
    """Get response from AgentCore agent during voice conversation"""
    
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')
    
    response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId='production-alias',
        sessionId=session_id,
        inputText=user_input
    )
    
    # Stream response
    completion = ""
    for event in response.get("completion"):
        chunk = event["chunk"]
        completion += chunk["bytes"].decode()
    
    return completion
```

## Key Implementation Notes

1. **Async/Await Pattern**: Nova Sonic requires asyncio for bidirectional streaming
2. **Base64 Encoding**: All audio must be base64 encoded before sending
3. **Event Sequencing**: Events must be sent in correct order (session start → prompt start → content start → data → content end → prompt end → session end)
4. **Audio Format**: Input is 16kHz PCM, output is 24kHz PCM
5. **Tool Integration**: Tools can be configured in prompt start and results sent back during conversation
6. **AgentCore Integration**: Use boto3 bedrock-agent-runtime client to invoke deployed agents
7. **Knowledge Base**: Use S3 data sources with vector embeddings for RAG capabilities
