"""SOPParser Signature - Extracts structured requirements from SOP"""

import dspy
from typing import Optional


class SOPParserSignature(dspy.Signature):
    """You are an expert requirements analyst. Your task is to carefully read the provided Standard Operating Procedure (SOP) and extract structured requirements that will be used to build an AI agent.

Analyze the SOP and identify:
1. The core goal and purpose of the agent
2. Whether human escalation is required and under what conditions
3. What integrations or tools are needed (especially knowledge base usage)
4. The knowledge domains the agent should understand
5. The tone and personality traits the agent should exhibit
6. Specific behaviors, constraints, and success criteria

Consider the knowledge_base_description to understand when the agent should query external information, and the human_handoff_description to understand escalation triggers.

If voice_personality is provided, incorporate those personality traits into your requirements analysis.

Output a well-structured JSON object with clear, actionable requirements that a developer can use to build the agent."""

    sop: str = dspy.InputField(desc="Standard Operating Procedure text")
    knowledge_base_description: str = dspy.InputField(
        desc="Description of when to use the knowledge base"
    )
    human_handoff_description: str = dspy.InputField(desc="Description of when to escalate to human")
    voice_personality: Optional[str] = dspy.InputField(
        desc="Voice personality configuration (JSON)", default=None
    )

    requirements: str = dspy.OutputField(
        desc="Structured requirements in JSON format with fields: core_goal, requires_escalation, integration_needed, knowledge_domains, tone, personality_traits"
    )
