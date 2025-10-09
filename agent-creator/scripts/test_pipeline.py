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

import mlflow
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.dspy.autolog()
mlflow.langchain.autolog()


mlflow.set_experiment("test-async-sonnet-trim2")

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
        You are a customer service agent for an e-commerce company deals with a loyal customer base and client.
        
        Your responsibilities:
        1. Answer customer questions about products and services 
        2. Help customers track their orders
        3. Process simple returns, refunds
        
        Guidelines:
        - Always be polite and professional
        - Use the knowledge base to find product information and be grounded to this information
        - Escalate to human agents for complex issues or complaints
        """
        
        sample_voice_personality = {
            "identity": "Friendly customer service representative",
            "task": "Help customers with their questions",
            "demeanor": "helpful,patient and obidient",
            "tone": "warm and professional",
            "formalityLevel": "professional",
            "enthusiasmLevel": "moderate",
            "fillerWords": "occasionally",
            "pacing": "moderate",
            "additionalInstructions": "Always confirm customer information before processing requests"
        }
        
        # Create pipeline
        print("Creating pipeline...")
        pipeline = await create_agent_creator_pipeline()
        print("✓ Pipeline created\n")
        
        # Prepare input
        input_data = {
            "sop": sample_sop,
            "knowledge_base_description": "Use knowledge base for product information and FAQs",
            "human_handoff_description": "Escalate complaints, refund requests over $100, and technical issues",
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
        
        result = await pipeline.ainvoke(input_data)
        
        # Display results
        print("\n" + "=" * 60)
        print("Pipeline Results")
        print("=" * 60 + "\n")
        
        if result.get("requirements"):
            print("✓ Requirements extracted")
            try:
                req = json.loads(result["requirements"])
                print(f"  Core goal: {req.get('core_goal', 'N/A')[:80]}...")
            except:
                print(f"  Requirements: {result['requirements'][:100]}...")
        
        if result.get("plan"):
            print("✓ Plan created")
            try:
                plan = json.loads(result["plan"])
                print(f"  Tools needed: {plan.get('tools_needed', 'N/A')}")
            except:
                print(f"  Plan: {result['plan'][:100]}...")
        
        if result.get("final_agent_code"):
            print("✓ Code generated")
            code_lines = result["final_agent_code"].split('\n')
            print(f"  Lines of code: {len(code_lines)}")
            print(f"  Has imports: {'import' in result['final_agent_code']}")
            print(f"  Has Agent class: {'Agent' in result['final_agent_code']}")
        
        if result.get("generated_prompt"):
            print("✓ System prompt generated")
            print(f"  Prompt length: {len(result['generated_prompt'])} chars")
        
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


async def test_mcp_tools_in_pipeline():
    """Test that MCP tools are available in the pipeline"""
    
    print("\n" + "=" * 60)
    print("Testing MCP Tools Integration")
    print("=" * 60 + "\n")
    
    try:
        from agentcreator.mcp_tools import get_all_mcp_tools
        
        print("Loading MCP tools (Strands + AWS Documentation)...")
        tools = await get_all_mcp_tools()
        
        if tools:
            print(f"✓ Loaded {len(tools)} MCP tools:")
            for tool in tools:
                print(f"  - {tool.name}")
            print()
            
            # Test a Strands tool if available
            print("Testing Strands search_docs tool...")
            search_tool = next((t for t in tools if t.name == "search_docs"), None)
            if search_tool:
                try:
                    # Call the tool function (it may or may not be async)
                    result = search_tool.func(query="how to use retrieve tool", k=2)
                    # If it's a coroutine, await it
                    if asyncio.iscoroutine(result):
                        result = await result
                    print(f"✓ search_docs test passed")
                    if result and isinstance(result, (list, tuple)) and len(result) > 0:
                        print(f"  Returned {len(result)} results")
                except Exception as e:
                    print(f"✗ search_docs test failed: {e}")
            
            # Test an AWS docs tool if available
            print("Testing AWS Documentation tool...")
            aws_tool = next((t for t in tools if "aws" in t.name.lower()), None)
            if aws_tool:
                print(f"✓ Found AWS tool: {aws_tool.name}")
            
            print()
            return True
        else:
            print("✗ No MCP tools loaded")
            return False
            
    except Exception as e:
        print(f"✗ MCP tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


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
