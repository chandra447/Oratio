import dspy
from typing import Optional
from .types import AgentPlan, Requirements, PlanReview

class PlanDrafterSignature(dspy.Signature):
    """You are an expert Strands agent architect. Create a complete technical plan for an agent to be deployed on AWS Bedrock AgentCore.

⚠️ CRITICAL: YOU MUST USE DOCUMENTATION TOOLS BEFORE CREATING THE PLAN ⚠️

MANDATORY WORKFLOW (DO NOT SKIP ANY STEP):

STEP 1 - FETCH TOOL DOCUMENTATION (REQUIRED):
You MUST use the MCP documentation tools to verify available tools:
1. Use 'search_docs' with query "community-tools-package" to find available tools
2. Use 'fetch_doc' to get the full list of community tools with their descriptions
3. Verify each tool you plan to use exists in the documentation

STEP 2 - VERIFY ARCHITECTURE PATTERN (IF MULTI-AGENT):
If considering multi-agent architecture, you MUST:
1. Use 'search_docs' with query "agents as tools multi-agent pattern"
2. Use 'fetch_doc' to get full implementation details of the pattern
3. Verify the @tool decorator usage and orchestrator pattern
4. Check how specialist agents should be structured

STEP 3 - UNDERSTAND MEMORY ARCHITECTURE:
⚠️ CRITICAL: Memory is handled by Chameleon (generic loader), NOT by generated agent code
- Chameleon injects memory hooks at runtime via MemoryHookProvider
- Generated agents receive hooks and state as parameters
- DO NOT plan for AgentCoreMemorySessionManager in generated code
- Memory strategy should note: "Memory handled by Chameleon via injected hooks"

CONSTRAINTS:
- ONLY use tools from 'strands-agents-tools' package (community tools)
- DO NOT plan for custom tools, external APIs requiring keys, or web search
- ALWAYS verify tools exist in documentation before planning

DECISION CRITERIA:
- Use **single agent** if requirements can be fulfilled by one agent using available tools
- Use **multi-agent** pattern if responsibilities are clearly distinct (e.g., product expert vs order tracker vs returns processor)
- For multi-agent: MUST follow "Agents as Tools" pattern where each specialist is wrapped as @tool

**Community Tools You Can Use (verify via documentation):**
- retrieve: Bedrock Knowledge Base querying (requires 'KNOWLEDGE_BASE_ID' env var)
- handoff_to_user: Escalate to human agent for complex/blocked cases
- calculator: Math operations
- current_time: Date/time answers
- file_read, file_write, editor: File operations
- python_repl: Run Python code
- http_request: HTTP calls (no API key)

**AFTER VERIFYING DOCUMENTATION, YOUR PLAN MUST INCLUDE:**
1. **Architecture Type**:
   - Explain if single or multi-agent.
   - If multi-agent:
     - List role names for each specialized agent
     - Describe orchestrator agent responsibilities
     - Explain handoff/flow logic using the "Agents as Tools" pattern
     - Specify what tools each specialized agent needs

2. **Tool Selection Rationale**:
   - Explicitly list community tools to include, matched directly to requirement lines.
   - For each, describe when/why/how they'll be used.
   - Configure tools that need setup (e.g., retrieve: set 'KNOWLEDGE_BASE_ID').

3. **Memory Strategy**:
   - MUST return a JSON object (not a string):
     {
       "type": "chameleon_injected",
       "description": "Memory handled by Chameleon generic loader via injected hooks",
       "implementation": "Generated agent code accepts hooks and state parameters at runtime"
     }
   - DO NOT plan for AgentCoreMemorySessionManager, MemoryClient, or any memory code in generated agents
   - Chameleon provides conversation continuity automatically

4. **Interaction/Processing Logic**:
   - Describe agent message loop: how/when tools/accounts are accessed, escalation triggers, handoff flows for multi-agent.

5. **System Prompt Outline**:
    - List the main sections you’ll instruct to CodeGenerator: agent identity, responsibilities, tool use policy, behavioral/personality guidelines (voice), escalation/error handling, any prohibitions.

6. **Error Handling/Fallbacks**:
    - MUST return a JSON object (not prose) with explicit keys such as:
        {
          "escalation_triggers": [ "...", "..." ],
          "fallback_actions": [ "...", "..." ],
          "tool_policies": [ "...", "..." ]
        }
    - Populate arrays with concrete steps. Never return a plain string.
    - Escalation triggers, fallback responses.

7. **Reflection**:
   - If plan_review is included, explicitly reflect how it influenced your new plan.

**OUTPUT:**
Return an `AgentPlan` object with fields:
- architecture_type: "single_agent" or "multi_agent"
- agent_roles: list of agent roles
- required_tools: list of tools used exactly as named
- tool_configurations: dict per tool (e.g., {"retrieve": {"env_var": "KNOWLEDGE_BASE_ID"}})
- memory_strategy: dict with keys "type", "description", "implementation" (see Memory Strategy section above)
- interaction_patterns: description of agent + tools interaction
- system_prompt_outline: as described above
- error_handling: dict with keys "escalation_triggers", "fallback_actions", "tool_policies" (see Error Handling section above)
- constraints: any business/logical/tech limits

Be precise: **never include custom/non-community tools, manual KB queries, or APIs requiring keys.**

**Additional Documentation References:**
- [Deployment Options](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/index.md) - For deployment planning
- [Operating Agents in Production](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/operating-agents-in-production/index.md) - For production considerations
- [Observability](https://strandsagents.com/latest/documentation/docs/user-guide/observability-evaluation/observability/index.md) - For monitoring patterns
"""
    requirements: Requirements = dspy.InputField(desc="Structured requirements from SOP parser")
    bedrock_knowledge_base_id: str = dspy.InputField(desc="Bedrock Knowledge Base ID for retrieve tool")
    plan_review: Optional[PlanReview] = dspy.InputField(desc="(Optional) Feedback/reflection from previous review")
    plan: AgentPlan = dspy.OutputField(
        desc="Well-structured agent architecture plan using ONLY Strands community tools and patterns"
    )
