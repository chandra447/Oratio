#!/usr/bin/env python3
"""
Test AgentCreator Pipeline

Tests the complete DSPy + LangGraph + MCP integration with a sample SOP.
"""

import asyncio
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
run_name = "oratio-multi-agent-test-complex"

from langfuse.langchain import CallbackHandler  

langfuse_handler: CallbackHandler | None = None


async def test_pipeline():
    """Test the complete AgentCreator pipeline"""
    
    print("\n" + "=" * 60)
    print("AgentCreator Pipeline Test")
    print("=" * 60 + "\n")
    
    try:
        # Import pipeline
        from agentcreator.pipeline import create_agent_creator_pipeline
        
        # Sample SOP for testing
        sample_sop = """
           You are a unified support platform coordinating multiple specialized AI agents for a major travel and shopping company. 
            Your system must respond to highly varied customer needs, with the following agent roles:

            1. A travel planner helps users design trip itineraries, book hotels, flights, and recommend attractions.
            2. A shopping advisor finds products, suggests deals, and compares options for customers.
            3. A payment and refunds specialist answers questions about billing, payments, and handles refund or dispute requests.
            4. A loyalty program agent helps with account details, rewards redemption, and status upgrades.

            Guidelines:
            - Always maintain a warm, empathetic, and professional demeanor with customers.
            - Each specialized agent must use only their relevant knowledge base and tools for their domain.
            - If a query spans multiple domains (e.g., booking plus payment), agents should collaborate and hand off the session as needed.
            - Escalate fraudulent transaction alerts or emotionally distressed customers to human agents immediately.
            - Always confirm customer identity using provided context before accessing any personal or payment information.

            Business Rules:
            - Refunds above $1000 or for disputed international bookings always escalate.
            - Loyalty upgrades require confirmation from payment agent before increasing tier.
            - Travel planning cannot finalize booking without payment approval.
            - Shopping advisor must consult loyalty agent if a deal involves a member-exclusive benefit.

            Your platform should log all customer queries with timestamps and agent hand-offs for audit compliance.

            """

        
        sample_voice_personality = {
        "identity": "Conversational AI Concierge",
        "task": "Guide, assist, and resolve customer queries across travel, shopping, payments, and loyalty programs.",
        "demeanor": "empathetic, proactive, collaborative",
        "tone": "warm, approachable yet trustworthy",
        "formalityLevel": "semi-formal (friendly but precise, especially on transactions)",
        "enthusiasmLevel": "high when recommending, measured when discussing issues or policies",
        "pacing": "adaptable—faster for bookings, slower and more deliberate for disputes or financial matters",
        "fillerWords": "rarely, except when building rapport (e.g., \"Let's see...\", \"Good news!\")",
        "additionalInstructions": (
            "If you detect frustration or stress, slow down, affirm the customer's feelings, and offer a handoff."
            " Use customer name frequently, thank them for patience, never guess on financial/legal matters."
            " Confirm context before giving out or committing to any sensitive operation."
            )
        }

        
        # Create pipeline
        print("Creating pipeline...")
        pipeline = await create_agent_creator_pipeline()
        print("✓ Pipeline created\n")
        global langfuse_handler
        langfuse_handler = CallbackHandler()

        pipeline_with_callabacks = pipeline.with_config({
            "callbacks":[langfuse_handler],
            "run_name":run_name,
            "tags":["oratio"]
        })
        
        # Prepare input
        input_data = {
            "sop": sample_sop,
            "knowledge_base_description": "Use knowledge base for product information and FAQs",
            "human_handoff_description": "Escalate complaints, refund requests over $200, and technical issues",
            "bedrock_knowledge_base_id": "kb-test-123",
            "agent_id": "test-agent-001",
            "voice_personality": sample_voice_personality,
        }
        
        print("Input:")
        print(f"  SOP length: {len(sample_sop)} chars")
        print(f"  KB ID: {input_data['bedrock_knowledge_base_id']}")
        print(f"  Agent ID: {input_data['agent_id']}")
        print()
        
        # Run pipeline
        print("Running pipeline...")
        print("This may take 30-60 seconds...\n")
        
        result = await pipeline_with_callabacks.ainvoke(input_data)
        
        # Display results
        print("\n" + "=" * 60)
        print("Pipeline Results")
        print("=" * 60 + "\n")
        
        if result.get("requirements"):
            print("✓ Requirements extracted")
            req = result["requirements"]
            if hasattr(req, 'core_goal'):
                print(f"  Core goal: {req.core_goal[:80]}...")
            else:
                # Fallback for string format
                try:
                    req_dict = json.loads(req) if isinstance(req, str) else req
                    print(f"  Core goal: {req_dict.get('core_goal', 'N/A')[:80]}...")
                except:
                    print(f"  Requirements: {str(req)[:100]}...")
        
        if result.get("plan"):
            print("✓ Plan created")
            plan = result["plan"]
            if hasattr(plan, 'architecture_type'):
                print(f"  Architecture type: {plan.architecture_type}")
                print(f"  Agent roles: {plan.agent_roles if hasattr(plan, 'agent_roles') else 'N/A'}")
                print(f"  Required tools: {plan.required_tools if hasattr(plan, 'required_tools') else 'N/A'}")
            else:
                # Fallback for string format
                try:
                    plan_dict = json.loads(plan) if isinstance(plan, str) else plan
                    print(f"  Architecture type: {plan_dict.get('architecture_type', 'N/A')}")
                    print(f"  Agent roles: {plan_dict.get('agent_roles', 'N/A')}")
                    print(f"  Plan: {str(plan_dict)[:100]}...")
                except:
                    print(f"  Plan: {str(plan)[:100]}...")
        
        if result.get("final_agent_code"):
            print("✓ Code generated")
            code_lines = result["final_agent_code"].split('\n')
            print(f"  Lines of code: {len(code_lines)}")
            print(f"  Has imports: {'import' in result['final_agent_code']}")
            print(f"  Has Agent class: {'Agent' in result['final_agent_code']}")
            print(f"  Has @tool decorator: {'@tool' in result['final_agent_code']}")
            print(f"  Has tool import: {'from strands import Agent, tool' in result['final_agent_code']}")
            
            # Check for multi-agent pattern indicators
            has_multiple_agents = result['final_agent_code'].count('Agent(') > 1
            has_orchestrator = 'orchestrator' in result['final_agent_code'].lower()
            print(f"  Multiple Agent instances: {has_multiple_agents}")
            print(f"  Has orchestrator pattern: {has_orchestrator}")
        
        if result.get("generated_prompt"):
            print("✓ System prompt generated")
            prompt = result["generated_prompt"]
            if hasattr(prompt, 'full_prompt'):
                print(f"  Prompt length: {len(prompt.full_prompt)} chars")
            else:
                print(f"  Prompt length: {len(str(prompt))} chars")
                
        if result.get("code_review"):
            print("✓ Code review completed")
            review = result["code_review"]
            if hasattr(review, 'code_quality_score'):
                print(f"  Code quality score: {review.code_quality_score}/10")
                print(f"  Critical issues: {len(review.critical_issues) if hasattr(review, 'critical_issues') else 0}")
                if hasattr(review, 'multi_agent_compliance') and review.multi_agent_compliance:
                    print(f"  Multi-agent compliance: {review.multi_agent_compliance[:100]}...")
            else:
                print(f"  Code review: {str(review)[:100]}...")
        
        print("\n" + "=" * 60)
        print("Sample Generated Code (first 30 lines):")
        print("=" * 60 + "\n")
        
        if result.get("final_agent_code"):
            code_lines = result["final_agent_code"].split('\n')[:30]
            for i, line in enumerate(code_lines, 1):
                print(f"{i:3d} | {line}")
        
        print("\n" + "=" * 60)
        print("✓ Pipeline test completed successfully!")
        print("=" * 60 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n✗ Test interrupted by user")
        return 1
        
    except Exception as e:
        print(f"\n✗ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


async def main():
    """Run all tests"""
    
    print("\n╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "AgentCreator Test Suite" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    
    exit_code = 0
    
    try:
        
        # Test 2: Full pipeline
        exit_code = await test_pipeline()
        
    finally:
        # Clean up MCP sessions (best effort - may fail due to async context)
        try:
            from agentcreator.mcp_tools import cleanup_mcp_sessions
            print("\nCleaning up MCP sessions...")
            await cleanup_mcp_sessions()
            print("✓ Cleanup complete\n")
        except (RuntimeError, asyncio.CancelledError):
            # Expected error - sessions will cleanup on process exit
            print("✓ MCP sessions will cleanup on exit\n")
        except Exception as e:
            logger.warning(f"Unexpected error during cleanup: {e}")
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
