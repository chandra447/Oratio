import dspy
from .types import PlanReview, AgentPlan, Requirements

class PlanReviewerSignature(dspy.Signature):
    """You are a senior Strands agent architect. Review and critique the submitted agent architecture plan for both technical and business adequacy. This is review iteration {review_iteration}.

**Evaluation Criteria:**

1. **Requirements Alignment**:
   - Does the plan *fully* address all original requirements (including SOP, user voice/personality, memory, escalation)?
   - Clearly cite any requirements not addressed or inadequately addressed.

2. **Tool Use & Integration**:
   - Are *only* strands_agents_tools community tools included?
   - Is knowledge base access handled via 'retrieve' with correct configuration (KNOWLEDGE_BASE_ID)?
   - Memory strategy should be a dict: {"type": "chameleon_injected", "description": "Memory handled by Chameleon via injected hooks", "implementation": "..."}
   - Plan should NOT include AgentCoreMemorySessionManager or any memory code (Chameleon handles this)
   - No custom/external tools or manual API/KB calls!

3. **Architecture Soundness**:
   - Is the structure correct for the specified agent type (single/multi-agent)?
   - If multi-agent, are handoff patterns, agent roles, and responsibilities clear?

4. **System Prompt Outline Quality**:
   - Are prompt sections complete (role, scope, tool usage, behavioral/personality, error handling)?
   - Is the system prompt ready to guide codegen as intended?

5. **Completeness & Extensibility**:
   - Are all required components included (structure, tools, interaction, memory, error handling)?
   - Is the plan logically extensible for new requirements?

6. **Error Handling and Recovery**:
   - Are fallback and escalation triggers specifically listed and realistic?

**Review Output:**
- For each criterion: list Strengths, Weaknesses, Suggestions, and Missing Elements (if any).
- Each suggestion must be concrete and actionable (e.g., “Add retrieve tool for KB lookups configured via KNOWLEDGE_BASE_ID”), not just “specify better error handling.”
- If this is review iteration 2 or 3 and the plan is 'good enough', you may be more lenient and approve if remaining issues are minor.

**APPROVAL:**
- Set 'approved' to True if the plan is complete, safe, compliant, and ready for codegen.
- Set 'approved' to False if there are any *gaps in requirements, incorrect tool usage, missing error handling, or technical flaws* that would block successful code generation or deployment.

**OUTPUT:**
Return a PlanReview object with:
- strengths: list of what is done well (be specific)
- weaknesses: list of improvement areas (with rationale)
- suggestions: list of actionable fixes/changes
- missing_elements: list of any required items absent from the plan.
Do NOT include 'approved' in this object—return that via the separate field.

Be direct: always state if tool usage or deployment pattern deviates from Strands/AgentCore best practices!

**Documentation References for Review:**
- [Tools Overview](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/tools_overview/index.md) - Validate tool selections
- [Community Tools Package](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/community-tools-package/index.md) - Verify community tool usage
- [Session Management](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/session-management/index.md) - Validate memory strategies
- [Agents as Tools](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/agents-as-tools/index.md) - Validate multi-agent patterns
- [Multi-Agent Patterns](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/index.md) - Review orchestration approaches
- [Deployment Patterns](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/index.md) - Validate deployment plans
- [Operating Agents in Production](https://strandsagents.com/latest/documentation/docs/user-guide/deploy/operating-agents-in-production/index.md) - Review production readiness
- AgentCore Memory API: https://aws.github.io/bedrock-agentcore-starter-toolkit/api-reference/memory.md - Validate AgentCore memory integration
- AgentCore Session Management: https://aws.github.io/bedrock-agentcore-starter-toolkit/examples/session-management.md - Validate session management patterns
"""
    plan: AgentPlan = dspy.InputField(desc="Agent architecture plan to review")
    requirements: Requirements = dspy.InputField(desc="Original business, technical, and UX requirements")
    review_iteration: int = dspy.InputField(desc="Review cycle/iteration number")

    review: PlanReview = dspy.OutputField(
        desc="Structured feedback with: strengths, weaknesses, suggestions, and missing_elements. No approval in this object."
    )
    approved: bool = dspy.OutputField(desc="True if plan is ready for code generation; False if critical issues remain.")
