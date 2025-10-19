"""
DSPy Signatures for AgentCreator Pipeline

All signatures include proper type hints for better IDE support and type safety.

IMPORTANT: The docstrings in these signatures are NOT just documentation - they are
instructions that will be passed to the LLM agent. Each docstring should:
1. Define the agent's role and expertise
2. Provide clear, actionable instructions
3. Specify the expected output format
4. Include any relevant guidelines or constraints

The LLM will read these docstrings and follow them to generate the appropriate output.
"""

from .sop_parser import SOPParserSignature
from .plan_drafter import PlanDrafterSignature
from .plan_reviewer import PlanReviewerSignature
from .code_generator import CodeGeneratorSignature
from .code_reviewer import CodeReviewerSignature
from .prompt_generator import PromptGeneratorSignature
from .voice_personality_parser import VoicePersonalityParser
from .types import (
    PlanReview,
    CodeReview,
    Requirements,
    AgentPlan,
    SystemPrompt,
    CodeGenerationOutput,
)

__all__ = [
    "SOPParserSignature",
    "PlanDrafterSignature",
    "PlanReviewerSignature",
    "CodeGeneratorSignature",
    "CodeReviewerSignature",
    "PromptGeneratorSignature",
    "VoicePersonalityParser",
    "PlanReview",
    "CodeReview",
    "Requirements",
    "AgentPlan",
    "SystemPrompt",
    "CodeGenerationOutput",
]
