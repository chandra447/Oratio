#!/usr/bin/env python3
"""
Deploy or update an AgentCore Runtime
Usage: python deploy_agentcore.py --name <name> --image <uri> --role-arn <arn> [options]
"""
import argparse
import json
import logging
import sys
import time

import boto3

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def wait_for_runtime(client, runtime_arn: str, max_wait: int = 300) -> bool:
    """Wait for runtime to be available"""
    logger.info(f"Waiting for runtime to be active (max {max_wait}s)...")
    start_time = time.time()
    
    # Extract runtime ID from ARN
    runtime_id = runtime_arn.split('/')[-1]
    
    while time.time() - start_time < max_wait:
        try:
            response = client.get_agent_runtime(agentRuntimeId=runtime_id)
            status = response.get('agentRuntime', {}).get('status')
            
            if status == 'AVAILABLE':
                logger.info("✓ Runtime is now AVAILABLE")
                return True
            elif status in ['FAILED', 'DELETING']:
                logger.error(f"✗ Runtime in failed state: {status}")
                return False
            
            logger.info(f"Status: {status}, waiting...")
            time.sleep(10)
        except Exception as e:
            logger.warning(f"Error checking status: {e}")
            time.sleep(10)
    
    logger.warning("Timeout waiting for runtime, continuing anyway...")
    return False


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


def deploy_agentcore(
    name: str,
    image_uri: str,
    role_arn: str,
    description: str = "",
    env_vars: dict = None,
    region: str = "us-east-1",
) -> str:
    """Deploy or update AgentCore Runtime"""
    # Sanitize the name to meet AWS naming requirements
    sanitized_name = sanitize_runtime_name(name)
    if sanitized_name != name:
        logger.info(f"Sanitized runtime name: '{name}' -> '{sanitized_name}'")
    
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    # Build container configuration
    container_config = {
        "containerUri": image_uri
    }
    
    if env_vars:
        container_config["environmentVariables"] = env_vars
    
    artifact = {
        "containerConfiguration": container_config
    }
    
    network_config = {
        "networkMode": "PUBLIC"
    }
    
    # Check if runtime exists
    logger.info(f"Checking if runtime '{sanitized_name}' exists...")
    try:
        response = client.list_agent_runtimes()
        existing_runtime_arn = None
        existing_runtime_id = None
        
        for runtime in response.get('agentRuntimes', []):
            if runtime.get('agentRuntimeName') == sanitized_name:
                existing_runtime_arn = runtime.get('agentRuntimeArn')
                # Extract runtime ID from ARN: arn:aws:bedrock-agentcore:region:account:runtime/runtime-id
                existing_runtime_id = existing_runtime_arn.split('/')[-1]
                break
        
        if existing_runtime_arn:
            logger.info(f"Found existing runtime: {existing_runtime_arn}")
            logger.info(f"Runtime ID: {existing_runtime_id}")
            logger.info("Updating runtime...")
            
            client.update_agent_runtime(
                agentRuntimeId=existing_runtime_id,
                agentRuntimeArtifact=artifact,
                networkConfiguration=network_config,
                roleArn=role_arn
            )
            
            logger.info(f"✓ Updated runtime: {existing_runtime_arn}")
            wait_for_runtime(client, existing_runtime_arn)
            return existing_runtime_arn
        
        else:
            logger.info("Runtime not found, creating new one...")
            
            response = client.create_agent_runtime(
                agentRuntimeName=sanitized_name,
                description=description or f"AgentCore runtime: {sanitized_name}",
                agentRuntimeArtifact=artifact,
                networkConfiguration=network_config,
                roleArn=role_arn
            )
            
            runtime_arn = response['agentRuntime']['agentRuntimeArn']
            logger.info(f"✓ Created runtime: {runtime_arn}")
            wait_for_runtime(client, runtime_arn)
            return runtime_arn
    
    except Exception as e:
        logger.error(f"✗ Failed to deploy runtime: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Deploy or update AgentCore Runtime')
    parser.add_argument('--name', required=True, help='Runtime name')
    parser.add_argument('--image', required=True, help='Docker image URI')
    parser.add_argument('--role-arn', required=True, help='Execution role ARN')
    parser.add_argument('--description', default='', help='Runtime description')
    parser.add_argument('--env', action='append', help='Environment variables (KEY=VALUE)', default=[])
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--output-file', help='File to write runtime ARN to')
    
    args = parser.parse_args()
    
    # Parse environment variables
    env_vars = {}
    for env_pair in args.env:
        if '=' in env_pair:
            key, value = env_pair.split('=', 1)
            env_vars[key] = value
    
    logger.info(f"Deploying AgentCore Runtime: {args.name}")
    logger.info(f"Image: {args.image}")
    logger.info(f"Role: {args.role_arn}")
    if env_vars:
        logger.info(f"Environment: {json.dumps(env_vars, indent=2)}")
    
    runtime_arn = deploy_agentcore(
        name=args.name,
        image_uri=args.image,
        role_arn=args.role_arn,
        description=args.description,
        env_vars=env_vars if env_vars else None,
        region=args.region
    )
    
    logger.info(f"✓ Deployment complete: {runtime_arn}")
    
    # Write ARN to file if requested
    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(runtime_arn)
        logger.info(f"✓ ARN written to: {args.output_file}")
    
    # Also print for GitHub Actions to capture
    print(f"RUNTIME_ARN={runtime_arn}")
    


if __name__ == '__main__':
    main()

