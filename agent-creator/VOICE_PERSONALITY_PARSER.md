# Voice Personality Parser

## Overview
Added a new pipeline node to convert unstructured voice personality text (from user input) into a structured format for Nova Sonic voice agent configuration.

## Architecture

### Pipeline Flow (Updated)
```
1. Parse Voice Personality → Convert unstructured text to structured format (if provided)
2. Parse SOP → Extract structured requirements
3. Draft Plan → Create agent architecture (with review cycle)
4. Generate Code → Use ReAct with code interpreter
5. Review Code → Validate generated code
6. Generate Prompt → Create system prompt with personality
```

### New Components

#### 1. **VoicePersonalityParser Signature** (`signatures/voice_personality_parser.py`)
- **Input**: Unstructured text describing voice personality
- **Output**: Structured dictionary with 9 fields:
  - `identity`: Who is the agent? (role, expertise, background)
  - `task`: Primary purpose
  - `demeanor`: Behavioral characteristics
  - `tone`: Speaking tone
  - `formality_level`: Language formality (very_formal → very_casual)
  - `enthusiasm_level`: Energy level (very_low → very_high)
  - `filler_words`: Filler words to use or "none"
  - `pacing`: Speech speed (very_slow → very_fast)
  - `additional_instructions`: Special considerations

#### 2. **VoicePersonalityParserModule** (`modules.py`)
- DSPy module wrapper using `dspy.Predict`
- Takes unstructured text + SOP + KB description for context
- Returns structured dictionary

#### 3. **Pipeline Node** (`pipeline.py`)
- New `parse_voice_personality_node` as entry point
- Conditionally executes if `voice_personality_text` is provided
- Populates `voice_personality` field in state

### State Updates

```python
class AgentCreatorState(TypedDict):
    # Input fields
    voice_personality_text: Optional[str]  # Raw unstructured text from user
    voice_personality: Optional[Dict[str, Any]]  # Structured (parsed)
    # ... other fields
```

### Lambda Handler Updates (`lambdas/agentcreator_invoker/handler.py`)

The handler now:
1. Retrieves `voicePersonality` from DynamoDB
2. Handles both string and dict formats
3. Passes `voice_personality_text` to AgentCreator pipeline
4. The pipeline parses it into structured format

## Example

### Input (from user)
```
"A friendly customer support agent who helps users with technical issues. 
Should be patient and empathetic, speaking clearly and not too fast."
```

### Output (structured)
```json
{
  "identity": "Technical customer support specialist with expertise in troubleshooting",
  "task": "Help users resolve technical issues with patience and clarity",
  "demeanor": "Friendly, patient, and empathetic",
  "tone": "Warm and reassuring",
  "formality_level": "neutral",
  "enthusiasm_level": "moderate",
  "filler_words": "none",
  "pacing": "moderate",
  "additional_instructions": "Always acknowledge user frustration and provide step-by-step guidance"
}
```

## Benefits

1. **User-Friendly**: Users can describe personality in natural language
2. **Consistent**: LLM ensures all required fields are populated
3. **Context-Aware**: Uses SOP and KB description to infer appropriate values
4. **Flexible**: Handles missing information gracefully with intelligent defaults
5. **Nova Sonic Ready**: Output format optimized for voice agent configuration

## Integration Points

### Frontend (`frontend/app/dashboard/agents/create/page.tsx`)
- User enters voice personality in a simple textarea
- Stored as string in DynamoDB under `voicePersonality`

### Backend (`backend/routers/agents.py`)
- Receives voice personality as string from frontend
- Stores in DynamoDB as-is

### AgentCreator Pipeline
- Receives unstructured text
- Parses into structured format
- Uses structured format for prompt generation

### Nova Sonic Voice Router (`backend/routers/voice.py`)
- Retrieves structured `voice_personality` from DynamoDB
- Uses fields to configure Nova Sonic system prompt
- Applies personality traits to voice interactions

## Testing

To test the voice personality parser:

```bash
cd agent-creator
uv run python -m scripts.test_pipeline
```

The test pipeline will:
1. Parse a sample voice personality text
2. Show the structured output
3. Verify all fields are populated
4. Continue through the full pipeline

