import os
from aws_cdk import Stack, CfnOutput
from constructs import Construct
from cdk_constructs.database import DatabaseConstruct
from cdk_constructs.storage import StorageConstruct
from cdk_constructs.auth import AuthConstruct
from cdk_constructs.compute import ComputeConstruct
from cdk_constructs.workflow import WorkflowConstruct
from cdk_constructs.iam_roles import AgentCoreRolesConstruct


class OratioStack(Stack):
    """
    Unified CDK stack for all Oratio infrastructure resources.
    Composed of modular constructs for better organization and maintainability.
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agentcreator_runtime_arn: str = None,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Get AgentCore Runtime ARN from parameter or environment
        self.agentcreator_runtime_arn = agentcreator_runtime_arn or os.getenv("AGENTCREATOR_RUNTIME_ARN", "")

        # Create database tables
        database = DatabaseConstruct(self, "Database")

        # Create S3 buckets
        storage = StorageConstruct(self, "Storage")

        # Create Cognito User Pool
        auth = AuthConstruct(self, "Auth")

        # Create IAM roles for AgentCore runtimes (Chameleon, AgentCreator)
        iam_roles = AgentCoreRolesConstruct(
            self,
            "AgentCoreRoles",
            code_bucket=storage.code_bucket,
            agents_table=database.agents_table,
        )

        # Create Lambda functions
        compute = ComputeConstruct(
            self,
            "Compute",
            agents_table=database.agents_table,
            knowledge_bases_table=database.knowledge_bases_table,
            kb_bucket=storage.kb_bucket,
            code_bucket=storage.code_bucket,
            agentcreator_runtime_arn=self.agentcreator_runtime_arn,
        )

        # Create simplified Step Functions workflow
        workflow = WorkflowConstruct(
            self,
            "Workflow",
            kb_provisioner=compute.kb_provisioner,
            agentcreator_invoker=compute.agentcreator_invoker,
        )

        # Grant Step Functions permission to invoke lambdas
        compute.kb_provisioner.grant_invoke(workflow.state_machine)
        compute.agentcreator_invoker.grant_invoke(workflow.state_machine)

        # Export important resources for reference
        self.database = database
        self.storage = storage
        self.auth = auth
        self.iam_roles = iam_roles
        self.compute = compute
        self.workflow = workflow

        # Export IAM role ARNs for use in GitHub Actions
        CfnOutput(
            self,
            "ChameleonExecutionRoleArn",
            value=iam_roles.chameleon_execution_role.role_arn,
            description="ARN of the Chameleon generic loader execution role",
            export_name="OratioStack-ChameleonExecutionRoleArn",
        )

        CfnOutput(
            self,
            "AgentCreatorExecutionRoleArn",
            value=iam_roles.agentcreator_execution_role.role_arn,
            description="ARN of the AgentCreator meta-agent execution role",
            export_name="OratioStack-AgentCreatorExecutionRoleArn",
        )
