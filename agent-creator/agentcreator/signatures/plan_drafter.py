"""PlanDrafter Signature - Creates agent architecture plan"""

import dspy


class PlanDrafterSignature(dspy.Signature):
    """You are an expert AI agent architect. Your task is to design a comprehensive architecture plan for a Strands agent based on the provided requirements.

**IMPORTANT CONSTRAINTS**:
- ONLY use Strands SDK community tools from 'strands-agents-tools' package
- DO NOT plan for custom tools that require API keys
- DO NOT plan for web search or external API integrations requiring authentication

**Available Strands Tools to Choose From**:

**Knowledge & Memory**:
- `retrieve` - Query Bedrock Knowledge Base (use for knowledge_base requirements)
- `memory` - Agent memory persistence
- `agent_core_memory` - Bedrock Agent Core Memory

**Human Interaction**:
- `handoff_to_user` - Human escalation (use for human_handoff requirements)

**Utilities**:
- `calculator` - Mathematical operations
- `current_time` - Get current date/time
- `http_request` - Make HTTP calls (no API key)

**File Operations**:
- `file_read`, `file_write`, `editor` - File operations

**Code Execution**:
- `python_repl` - Run Python code

Create a detailed technical plan that includes:

1. **Agent Structure**: 
   - Use Strands Agent class with tools parameter
   - Specify which Strands SDK tools to use (from list above)
   - Define tool_config for tools that need configuration (e.g., retrieve needs knowledge_base_id)

2. **Tools Selection**: 
   - Choose appropriate Strands SDK tools based on requirements
   - For knowledge base: use `retrieve` tool with bedrock_knowledge_base_id
   - For human handoff: use `handoff_to_user` tool
   - For calculations: use `calculator` tool
   - DO NOT specify custom tools or tools requiring API keys

3. **Reasoning Approach**: 
   - Describe how the agent should process messages
   - When to use each Strands tool
   - Decision logic for tool selection

4. **Knowledge Base Integration**: 
   - Use `retrieve` tool from strands_tools
   - Configure with bedrock_knowledge_base_id: {bedrock_knowledge_base_id}
   - Define when to query the knowledge base

5. **Handoff Logic**: 
   - Use `handoff_to_user` tool from strands_tools
   - Define clear conditions and triggers for escalation

6. **System Prompt Outline**: 
   - Sketch key elements for the agent's system prompt
   - Include tool usage guidelines
   - Define personality and behavioral guidelines

7. **Error Handling**: 
   - Specify fallback responses
   - Escalation triggers
   - Recovery strategies

Output a well-structured JSON object that specifies ONLY Strands SDK community tools (no custom tools, no API keys)."""

    requirements: str = dspy.InputField(desc="Structured requirements from SOP parser")
    bedrock_knowledge_base_id: str = dspy.InputField(desc="Bedrock Knowledge Base ID for retrieve tool")

    plan: str = dspy.OutputField(
        desc="Detailed agent architecture plan using ONLY Strands SDK community tools (no custom tools with API keys)"
    )
