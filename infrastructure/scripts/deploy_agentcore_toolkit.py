#!/usr/bin/env python3
"""
Deploy AgentCore Runtime using bedrock-agentcore-starter-toolkit
This replaces manual Docker builds with automated deployment

Usage:
    python deploy_agentcore_toolkit.py --name chameleon --entrypoint generic_loader.py --role-arn <arn>
"""
import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def sanitize_runtime_name(name: str) -> str:
    """
    Sanitize runtime name to meet AWS requirements:
    - Must start with a letter
    - Can only contain letters, numbers, and underscores
    - Pattern: [a-zA-Z][a-zA-Z0-9_]{0,47}
    """
    if not name:
        raise ValueError("Runtime name cannot be empty")
    
    # Replace hyphens with underscores
    sanitized = name.replace('-', '_')
    
    # Ensure it starts with a letter
    if not sanitized or not sanitized[0].isalpha():
        sanitized = 'agent_' + sanitized
    
    # Remove any invalid characters
    sanitized = ''.join(c for c in sanitized if c.isalnum() or c == '_')
    
    # Ensure we still have a valid name after sanitization
    if not sanitized:
        raise ValueError(f"Cannot sanitize runtime name: '{name}' results in empty string")
    
    # Truncate to 48 characters max
    sanitized = sanitized[:48]
    
    return sanitized


def deploy_with_toolkit(
    name: str,
    entrypoint: str,
    role_arn: str,
    region: str = "us-east-1",
    working_dir: str = None,
    env_vars: dict = None,
) -> str:
    """
    Deploy AgentCore Runtime using the starter toolkit
    
    Args:
        name: Runtime name (will be sanitized)
        entrypoint: Path to the entrypoint file (e.g., "generic_loader.py")
        role_arn: IAM execution role ARN
        region: AWS region
        working_dir: Working directory containing the agent code
        env_vars: Environment variables to pass to the runtime
    
    Returns:
        Runtime ARN
    """
    try:
        from bedrock_agentcore_starter_toolkit import Runtime
    except ImportError:
        logger.error("❌ bedrock-agentcore-starter-toolkit not installed")
        logger.info("Install with: uv add bedrock-agentcore-starter-toolkit")
        sys.exit(1)
    
    # Sanitize the name
    sanitized_name = sanitize_runtime_name(name)
    if sanitized_name != name:
        logger.info(f"Sanitized runtime name: '{name}' -> '{sanitized_name}'")
    
    # Change to working directory if specified
    original_dir = Path.cwd()
    if working_dir:
        working_path = Path(working_dir).resolve()
        logger.info(f"📂 Changing to working directory: {working_path}")
        import os
        os.chdir(working_path)
    
    try:
        logger.info("🚀 Starting AgentCore Deployment with Starter Toolkit")
        logger.info(f"   📝 Agent Name: {sanitized_name}")
        logger.info(f"   📍 Region: {region}")
        logger.info(f"   🎯 Entrypoint: {entrypoint}")
        logger.info(f"   🔐 Role ARN: {role_arn}")
        
        # Step 1: Determine dependency management approach
        if Path("pyproject.toml").exists():
            logger.info("📦 Using uv with pyproject.toml for dependency management")
            requirements_file = "pyproject.toml"
        elif Path("requirements.txt").exists():
            logger.info("📦 Using pip with requirements.txt for dependency management")
            requirements_file = "requirements.txt"
        else:
            raise FileNotFoundError("No pyproject.toml or requirements.txt found")
        
        # Step 2: Initialize runtime
        runtime = Runtime()
        
        # Step 3: Configure the runtime
        logger.info("⚙️ Configuring runtime...")
        
        runtime.configure(
            execution_role=role_arn,
            entrypoint=entrypoint,
            requirements_file=requirements_file,
            region=region,
            agent_name=sanitized_name,
            auto_create_ecr=True,
            disable_otel=False
        )
        logger.info("✅ Configuration completed")
        
        # Step 4: Launch the runtime
        # Note: runtime.launch() is idempotent - it will create if new, update if exists
        logger.info("🚀 Launching runtime (this may take several minutes)...")
        if env_vars:
            logger.info(f"   🔧 Environment Variables: {json.dumps(env_vars, indent=2)}")
        logger.info("   📦 Building container image...")
        logger.info("   ⬆️ Pushing to ECR...")
        logger.info("   🏗️ Creating/Updating AgentCore Runtime...")
        
        # Pass environment variables and auto_update_on_conflict to launch
        # auto_update_on_conflict=True allows updating existing runtimes
        runtime.launch(
            env_vars=env_vars if env_vars else None,
            auto_update_on_conflict=True
        )
        logger.info("✅ Launch completed (runtime created or updated)")
        
        # Step 5: Get status and extract ARN
        logger.info("📊 Getting runtime status...")
        status = runtime.status()
        
        # Extract runtime ARN
        runtime_arn = None
        if hasattr(status, 'agent_arn'):
            runtime_arn = status.agent_arn
        elif hasattr(status, 'config') and hasattr(status.config, 'agent_arn'):
            runtime_arn = status.config.agent_arn
        elif isinstance(status, dict) and 'agent_arn' in status:
            runtime_arn = status['agent_arn']
        
        if not runtime_arn:
            logger.error("❌ Could not extract runtime ARN from status")
            logger.info(f"Status object: {status}")
            sys.exit(1)
        
        logger.info("\n🎉 AgentCore Runtime Deployed Successfully!")
        logger.info(f"🏷️ Runtime ARN: {runtime_arn}")
        logger.info(f"📍 Region: {region}")
        logger.info(f"🔐 Execution Role: {role_arn}")
        
        # Show CloudWatch logs info
        agent_id = runtime_arn.split('/')[-1]
        log_group = f"/aws/bedrock-agentcore/runtimes/{agent_id}-DEFAULT"
        logger.info("\n📊 Monitoring:")
        logger.info(f"   CloudWatch Logs: {log_group}")
        logger.info(f"   Tail logs: aws logs tail {log_group} --follow")
        
        return runtime_arn
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        import traceback
        logger.error(f"Full error: {traceback.format_exc()}")
        sys.exit(1)
    finally:
        # Change back to original directory
        if working_dir:
            import os
            os.chdir(original_dir)


def main():
    parser = argparse.ArgumentParser(
        description='Deploy AgentCore Runtime using starter toolkit'
    )
    parser.add_argument('--name', required=True, help='Runtime name')
    parser.add_argument('--entrypoint', required=True, help='Entrypoint file (e.g., generic_loader.py)')
    parser.add_argument('--role-arn', required=True, help='Execution role ARN')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--working-dir', help='Working directory containing agent code')
    parser.add_argument('--env', action='append', help='Environment variables (KEY=VALUE)', default=[])
    parser.add_argument('--output-file', help='File to write runtime ARN to')
    
    args = parser.parse_args()
    
    # Parse environment variables
    env_vars = {}
    for env_pair in args.env:
        if '=' in env_pair:
            key, value = env_pair.split('=', 1)
            env_vars[key] = value
    
    runtime_arn = deploy_with_toolkit(
        name=args.name,
        entrypoint=args.entrypoint,
        role_arn=args.role_arn,
        region=args.region,
        working_dir=args.working_dir,
        env_vars=env_vars if env_vars else None,
    )
    
    # Write ARN to file if requested
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(runtime_arn)
        logger.info(f"✓ ARN written to: {args.output_file}")
    
    # Print for GitHub Actions to capture
    print(f"RUNTIME_ARN={runtime_arn}")


if __name__ == '__main__':
    main()

