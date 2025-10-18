"""
DSPy Modules for AgentCreator Pipeline

Module Selection Strategy:
- ChainOfThought: Used for reasoning tasks without tool interaction (parsing, planning, reviewing)
- ReAct: Used for CodeGenerator to enable tool usage (code interpreter + MCP tools)
"""

import json
import logging
from typing import Any, Dict, List, Optional

import dspy

from .signatures import (
    CodeGeneratorSignature,
    CodeReviewerSignature,
    PlanDrafterSignature,
    PlanReviewerSignature,
    PromptGeneratorSignature,
    SOPParserSignature,
)
from .signatures.types import (
    PlanReview,
    CodeReview,
    Requirements,
    AgentPlan,
    SystemPrompt,
    CodeGenerationOutput,
)
from .tools import execute_python_code, validate_python_syntax

logger = logging.getLogger(__name__)


class SOPParser(dspy.Module):
    """Parse SOP into structured requirements
    
    Uses ChainOfThought for step-by-step reasoning without tool interaction.
    """

    def __init__(self):
        super().__init__()
        self.parser = dspy.Predict(SOPParserSignature)

    async def aforward(
        self,
        sop: str,
        knowledge_base_description: str,
        human_handoff_description: str,
        voice_personality: Optional[str] = None,
    ) -> Requirements:
        """Parse SOP and return structured requirements as Requirements object
        
        Args:
            sop: Standard Operating Procedure text
            knowledge_base_description: When to use knowledge base
            human_handoff_description: When to escalate to human
            voice_personality: Optional voice personality config (JSON string)
            
        Returns:
            Requirements object with structured requirements
        """
        result = await self.parser.acall(
            sop=sop,
            knowledge_base_description=knowledge_base_description,
            human_handoff_description=human_handoff_description,
            voice_personality=voice_personality,
        )
        return result.requirements


class PlanDrafter(dspy.Module):
    """Draft agent architecture plan
    
    Uses ChainOfThought for systematic planning , leverage the strands documentation tools
    which can help you be grounded to how the agentcore implmenetation is.
    For a practical example of how to work with agentcore
    refer to the docs link : https://strandsagents.com/latest/documentation/docs/user-guide/deploy/deploy_to_bedrock_agentcore/index.md
    by providing to the tools avilable to you.
    And also refer to https://strandsagents.com/latest/documentation/docs/user-guide/concepts/tools/community-tools-package/index.md
    for avialble community tools from strands
    """

    def __init__(self, strands_tools : List[dspy.Tool]):
        super().__init__()
        self.drafter = dspy.ReAct(PlanDrafterSignature, tools = strands_tools)

    async def aforward(self, requirements: Requirements, bedrock_knowledge_base_id: str,
    plan_review: PlanReview = None) -> AgentPlan:
        """Draft agent architecture plan
        
        Args:
            requirements: Structured requirements (Requirements object)
            bedrock_knowledge_base_id: Bedrock KB ID for integration
            
        Returns:
            AgentPlan object with agent architecture plan
        """
        
        result = await self.drafter.acall(
            requirements=requirements,
            bedrock_knowledge_base_id=bedrock_knowledge_base_id,
            plan_review = plan_review
        )
        return result


class PlanReviewer(dspy.Module):
    """Review and critique agent plan
    
    Uses ChainOfThought for thorough review and critique.
    """

    def __init__(self):
        super().__init__()
        self.reviewer = dspy.Predict(PlanReviewerSignature)

    async def aforward(self, plan: AgentPlan, 
        requirements: Requirements,
        review_iteration: int) -> dspy.Prediction:
        """Review agent plan and provide feedback
        
        Args:
            plan: Agent architecture plan (AgentPlan object)
            requirements: Original requirements (Requirements object)
            review_iteration: Current iteration number
            
        Returns:
            dspy.Prediction with both approved and review fields
        """
        
        result = await self.reviewer.acall(
            plan=plan,
            requirements=requirements,
            review_iteration=review_iteration,
        )
        
        # Return the full result so both approved and review are available
        return result


class CodeGenerator(dspy.Module):
    """Generate Strands agent code
    
    Uses ReAct (Reasoning + Acting) to enable tool usage during code generation.
    
    Available Tools:
    - validate_python_syntax: Quick syntax validation
    - execute_python_code: Full execution for testing
    - Strands MCP tools: Documentation access (if available)
    """

    def __init__(self, strands_mcp_tools: Optional[List] = None):
        super().__init__()
        
        # Base tools for code validation
        tools = [validate_python_syntax, execute_python_code]
        
        # Add Strands MCP tools if available
        if strands_mcp_tools:
            tools.extend(strands_mcp_tools)
            logger.info(f"CodeGenerator initialized with {len(strands_mcp_tools)} Strands MCP tools")
        
        # ReAct enables tool usage for code validation
        self.generator = dspy.ReAct(
            CodeGeneratorSignature,
            tools=tools,
            max_iters=10,  # Increased to handle potential formatting issues
        )

    async def aforward(
        self,
        plan: AgentPlan,
        requirements: Requirements,
        bedrock_knowledge_base_id: str,
        code_review_feedback: str = "",
        model_id: str = "amazon.nova-pro-v1:0",
        enable_memory_hooks: bool = True,
    ) -> CodeGenerationOutput:
        """Generate Strands agent code with validation
        
        The ReAct module will:
        1. Reason about the code structure needed
        2. Generate code incrementally
        3. Use validate_python_syntax for quick checks
        4. Use execute_python_code for testing critical sections
        5. Iterate based on tool feedback
        
        Args:
            plan: Approved architecture plan (AgentPlan object)
            requirements: Original requirements (Requirements object)
            bedrock_knowledge_base_id: Bedrock KB ID for integration
            code_review_feedback: Feedback from previous code review
            model_id: Bedrock foundation model identifier
            enable_memory_hooks: Whether hook-based memory persistence must be implemented but not Session Manager
            
        Returns:
            CodeGenerationOutput object containing agent code, validation status, documentation references, and implementation notes
        """
        logger.info("Generating code with ReAct (reasoning + tool usage)...")
        logger.info(
            "Available tools: validate_python_syntax, execute_python_code%s",
            " + MCP tooling" if self.generator.tools and len(self.generator.tools) > 2 else "",
        )


        result = await self.generator.acall(
            plan=plan,
            requirements=requirements,
            bedrock_knowledge_base_id=bedrock_knowledge_base_id,
            model_id=model_id,
            enable_memory_hooks=enable_memory_hooks,
            code_review_feedback=code_review_feedback,
        )
        
        logger.info(
            "Code generation complete (validation_status=%s, documentation_refs=%d)",
            getattr(result.output, "validation_status", "unknown") if hasattr(result, 'output') else "unknown",
            len(getattr(result.output, "documentation_references", []) if hasattr(result, 'output') else []),
        )
        return  result


class CodeReviewer(dspy.Module):
    """Review generated code with documentation verification
    
    Uses ReAct to enable documentation lookup during code review.
    This allows the reviewer to verify imports and patterns against actual documentation.
    """

    def __init__(self, strands_mcp_tools: Optional[List] = None):
        super().__init__()
        
        # Base tools for code validation
        tools = [validate_python_syntax]
        
        # Add Strands MCP tools if available (for documentation verification)
        if strands_mcp_tools:
            tools.extend(strands_mcp_tools)
            logger.info(f"CodeReviewer initialized with {len(strands_mcp_tools)} MCP tools for documentation verification")
        
        # ReAct enables tool usage for import verification
        self.reviewer = dspy.ReAct(
            CodeReviewerSignature,
            tools=tools,
            max_iters=10,  # Increased to handle potential formatting issues
        )

    async def aforward(self, agent_code: str, plan: AgentPlan, requirements: Requirements) -> CodeReview:
        """Review generated code for quality and correctness
        
        The ReAct module will:
        1. Analyze the code structure
        2. Extract imports and verify them against documentation
        3. Check for hallucinated APIs
        4. Validate AgentCore deployment pattern
        5. Provide specific, actionable feedback
        
        Args:
            agent_code: Generated Python code
            plan: Original architecture plan (AgentPlan object)
            requirements: Original requirements (Requirements object)
            
        Returns:
            CodeReview object with code review feedback
        """
        logger.info("Reviewing code with ReAct (documentation verification enabled)...")
        
        result = await self.reviewer.acall(
            agent_code=agent_code,
            plan=plan,
            requirements=requirements,
        )
        
        logger.info("Code review complete")
        return result


class PromptGenerator(dspy.Module):
    """Generate system prompt
    
    Uses ChainOfThought for crafting comprehensive system prompts.
    """

    def __init__(self):
        super().__init__()
        self.generator = dspy.Predict(PromptGeneratorSignature)

    async def aforward(self, requirements: Requirements, plan: AgentPlan, voice_personality: Optional[str] = None) -> SystemPrompt:
        """Generate system prompt for the agent
        
        Args:
            requirements: Structured requirements (Requirements object)
            plan: Agent architecture plan (AgentPlan object)
            voice_personality: Optional voice personality config (JSON string)
            
        Returns:
            SystemPrompt object containing complete system prompt components
        """
        
        result = await self.generator.acall(
            requirements=requirements,
            plan=plan,
            voice_personality=voice_personality,
        )
        return result.system_prompt
