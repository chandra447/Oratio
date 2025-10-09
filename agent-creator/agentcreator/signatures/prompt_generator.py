"""PromptGenerator Signature - Creates comprehensive system prompts"""

import dspy
from typing import Optional


class PromptGeneratorSignature(dspy.Signature):
    """You are an expert prompt engineer specializing in AI agent system prompts. Your task is to craft a comprehensive, effective system prompt that will guide the agent's behavior.

Create a system prompt that includes:

1. **Identity & Role**:
   - Who the agent is (from requirements and voice_personality)
   - What their primary purpose is
   - Their area of expertise

2. **Personality & Communication Style** (if voice_personality provided):
   - Identity and task description
   - Demeanor and tone
   - Formality and enthusiasm levels
   - Use of filler words and pacing
   - Any additional personality instructions

3. **Core Responsibilities**:
   - What the agent should do
   - How they should approach conversations
   - When to use different tools (knowledge base, handoff)

4. **Behavioral Guidelines**:
   - How to handle different types of requests
   - When to escalate to humans
   - How to use the knowledge base effectively
   - Error handling and fallback behaviors

5. **Specific Instructions**:
   - Important rules from the SOP
   - Constraints and limitations
   - Success criteria
   - Examples of good responses (if applicable)

6. **Tool Usage**:
   - When and how to query the knowledge base
   - Conditions for human handoff
   - How to handle edge cases

**Style Guidelines**:
- Write in second person ("You are...", "Your role is...")
- Be specific and actionable
- Include examples where helpful
- Make it conversational yet professional
- Ensure consistency with the personality traits

Output a complete, ready-to-use system prompt that will be passed to the agent at runtime."""

    requirements: str = dspy.InputField(desc="Structured requirements")
    plan: str = dspy.InputField(desc="Agent architecture plan")
    voice_personality: Optional[str] = dspy.InputField(desc="Voice personality configuration", default=None)

    system_prompt: str = dspy.OutputField(
        desc="Complete system prompt that will be used with the agent, incorporating personality, SOP guidelines, and behavioral instructions"
    )
