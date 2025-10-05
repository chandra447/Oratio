from aws_cdk import Stack
from constructs import Construct
from cdk_constructs.database import DatabaseConstruct
from cdk_constructs.storage import StorageConstruct
from cdk_constructs.auth import AuthConstruct
from cdk_constructs.compute import ComputeConstruct
from cdk_constructs.workflow import WorkflowConstruct


class OratioStack(Stack):
    """
    Unified CDK stack for all Oratio infrastructure resources.
    Composed of modular constructs for better organization and maintainability.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create database tables
        database = DatabaseConstruct(self, "Database")

        # Create S3 buckets
        storage = StorageConstruct(self, "Storage")

        # Create Cognito User Pool
        auth = AuthConstruct(self, "Auth")

        # Create Lambda functions
        compute = ComputeConstruct(
            self,
            "Compute",
            agents_table=database.agents_table,
            kb_bucket=storage.kb_bucket,
            code_bucket=storage.code_bucket,
        )

        # Create Step Functions workflow
        workflow = WorkflowConstruct(
            self,
            "Workflow",
            kb_provisioner=compute.kb_provisioner,
            agentcreator_invoker=compute.agentcreator_invoker,
            agentcore_deployer=compute.agentcore_deployer,
        )

        # Export important resources for reference
        self.database = database
        self.storage = storage
        self.auth = auth
        self.compute = compute
        self.workflow = workflow
