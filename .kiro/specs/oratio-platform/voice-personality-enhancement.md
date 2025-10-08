# Voice Personality Enhancement

## Overview
Enhanced the Agent model to support detailed voice personality configuration for better agent output and personality customization.

## New Model: VoicePersonality

```python
class VoicePersonality(BaseModel):
    """Voice agent personality configuration"""
    
    identity: Optional[str]              # Who/what the AI represents
    task: Optional[str]                  # High-level task description
    demeanor: Optional[str]              # Overall attitude (patient, upbeat, empathetic)
    tone: Optional[str]                  # Voice style (warm, authoritative)
    formality_level: Optional[str]       # Casual vs professional
    enthusiasm_level: Optional[str]      # Energy level (calm, moderate, enthusiastic)
    filler_words: Optional[str]          # Frequency (none, occasionally, often)
    pacing: Optional[str]                # Speed of delivery
    additional_instructions: Optional[str] # Other personality instructions
```

## Updated Models

### Agent Model
- Added `voice_personality: Optional[VoicePersonality]` field
- Keeps existing `voice_config` for technical configuration
- Separates personality from technical settings

### AgentCreate Model
- Added `voice_personality: Optional[VoicePersonality]` parameter
- Accepts personality configuration during agent creation

### AgentResponse Model
- Includes `voice_personality` in API responses
- Allows frontend to display personality settings

## API Changes

### POST /api/agents
**New Field**:
```
voice_personality: JSON string (optional)
```

**Example**:
```json
{
  "identity": "Friendly customer service representative with 5 years of experience",
  "task": "Handle customer inquiries and returns professionally",
  "demeanor": "Patient and empathetic",
  "tone": "Warm and conversational",
  "formality_level": "professional",
  "enthusiasm_level": "moderate",
  "filler_words": "occasionally",
  "pacing": "moderate",
  "additional_instructions": "Always confirm spelling of names and phone numbers"
}
```

## Benefits for MVP/Hackathon

### 1. Better Agent Personality
- **Identity**: Gives the agent a clear role and backstory
- **Demeanor & Tone**: Creates consistent personality across conversations
- **Formality**: Matches the business context (casual startup vs formal enterprise)

### 2. Improved Voice Quality
- **Filler Words**: Makes conversations more natural and human-like
- **Pacing**: Controls speed for better comprehension
- **Enthusiasm**: Matches energy to use case

### 3. Task-Specific Behavior
- **Task Field**: Clearly defines what the agent should do
- **Additional Instructions**: Allows custom rules (e.g., "always confirm spelling")

## Usage Example

### Creating a Voice Agent with Personality

```bash
curl -X POST http://localhost:8000/api/agents \
  -H "Authorization: Bearer <token>" \
  -F "agentName=Customer Service Agent" \
  -F "agentType=voice" \
  -F "sop=Handle customer inquiries professionally..." \
  -F "knowledgeBaseDescription=Use for product info" \
  -F "humanHandoffDescription=Escalate for refunds" \
  -F 'voice_personality={
    "identity": "Experienced customer service rep named Sarah",
    "task": "Help customers with orders and returns",
    "demeanor": "Patient and empathetic",
    "tone": "Warm and conversational",
    "formality_level": "professional",
    "enthusiasm_level": "moderate",
    "filler_words": "occasionally",
    "pacing": "moderate",
    "additional_instructions": "Always repeat back names and phone numbers for confirmation"
  }' \
  -F "files=@product_catalog.pdf"
```

### Response

```json
{
  "agentId": "uuid",
  "agentName": "Customer Service Agent",
  "agentType": "voice",
  "status": "creating",
  "voice_personality": {
    "identity": "Experienced customer service rep named Sarah",
    "task": "Help customers with orders and returns",
    "demeanor": "Patient and empathetic",
    "tone": "Warm and conversational",
    "formality_level": "professional",
    "enthusiasm_level": "moderate",
    "filler_words": "occasionally",
    "pacing": "moderate",
    "additional_instructions": "Always repeat back names and phone numbers for confirmation"
  },
  ...
}
```

## Integration with AgentCreator

The `voice_personality` will be passed to the AgentCreator meta-agent, which will:

1. **Parse Personality**: Extract personality traits from the configuration
2. **Generate System Prompt**: Create a detailed system prompt that includes:
   - Identity and role
   - Task description
   - Personality traits (demeanor, tone, formality)
   - Behavioral instructions (filler words, pacing)
   - Custom instructions
3. **Optimize for Voice**: Ensure the prompt works well with Nova Sonic voice model

### Example Generated Prompt

```
You are Sarah, an experienced customer service representative with 5 years of experience. 
Your primary task is to help customers with orders and returns.

Personality:
- Be patient and empathetic in all interactions
- Use a warm and conversational tone
- Maintain a professional level of formality
- Show moderate enthusiasm
- Occasionally use natural filler words like "um" or "let me see" to sound more human
- Speak at a moderate pace for clarity

Important Instructions:
- Always repeat back names and phone numbers for confirmation before proceeding
- If a customer corrects any detail, acknowledge it and confirm the new information
- Use the knowledge base for product information
- Escalate to a human agent for refund requests

Remember: You're here to help customers feel heard and supported while efficiently 
resolving their inquiries.
```

## Frontend Integration

The frontend can provide a form with these fields:

```typescript
interface VoicePersonalityForm {
  identity?: string;           // Text area
  task?: string;              // Text area
  demeanor?: string;          // Dropdown: patient, upbeat, empathetic, serious
  tone?: string;              // Dropdown: warm, professional, authoritative
  formality_level?: string;   // Dropdown: casual, professional, formal
  enthusiasm_level?: string;  // Dropdown: calm, moderate, enthusiastic
  filler_words?: string;      // Dropdown: none, occasionally, often
  pacing?: string;            // Dropdown: slow, moderate, fast
  additional_instructions?: string; // Text area
}
```

## Database Storage

The `voice_personality` is stored as a JSON object in DynamoDB:

```json
{
  "userId": "user-123",
  "agentId": "agent-456",
  "agentName": "Customer Service Agent",
  "voicePersonality": {
    "identity": "Experienced customer service rep named Sarah",
    "task": "Help customers with orders and returns",
    "demeanor": "Patient and empathetic",
    "tone": "Warm and conversational",
    "formalityLevel": "professional",
    "enthusiasmLevel": "moderate",
    "fillerWords": "occasionally",
    "pacing": "moderate",
    "additionalInstructions": "Always repeat back names and phone numbers"
  },
  ...
}
```

## Key Improvements for Hackathon

1. **Differentiation**: Stands out from basic chatbots with personality
2. **Demo-Friendly**: Easy to show different personalities in demos
3. **User Control**: Gives users fine-grained control over agent behavior
4. **Voice Quality**: Improves naturalness of voice interactions
5. **Business Value**: Matches agent personality to brand and use case

## Files Modified

- `backend/models/agent.py` - Added VoicePersonality model
- `backend/models/__init__.py` - Exported VoicePersonality
- `backend/routers/agents.py` - Added voice_personality parameter and parsing
- All agent responses now include voice_personality

## Next Steps

1. **AgentCreator Integration**: Use voice_personality in prompt generation
2. **Frontend Form**: Build UI for personality configuration
3. **Validation**: Add validation for personality field values
4. **Presets**: Create personality presets (e.g., "Friendly Support", "Professional Advisor")
5. **Testing**: Test different personalities with Nova Sonic
