#!/usr/bin/env python3
import os
from aws_cdk import App, Environment, Tags
from stacks.oratio_stack import OratioStack

app = App()

# Define environment
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

# Create single unified stack
oratio_stack = OratioStack(app, "OratioStack", env=env)

# Add tags for cost tracking and organization
Tags.of(oratio_stack).add("Project", "Oratio")
Tags.of(oratio_stack).add("Environment", os.environ.get("ENVIRONMENT", "development"))
Tags.of(oratio_stack).add("ManagedBy", "CDK")

app.synth()
