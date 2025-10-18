from aws_cdk import Duration, Stack, aws_lambda as lambda_, aws_iam as iam, aws_dynamodb as dynamodb, aws_s3 as s3
from constructs import Construct


class ComputeConstruct(Construct):
    """Lambda functions for agent creation workflow"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        agents_table: dynamodb.Table,
        knowledge_bases_table: dynamodb.Table,
        kb_bucket: s3.Bucket,
        code_bucket: s3.Bucket,
        agentcreator_runtime_arn: str = "",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # KB Provisioner Lambda
        self.kb_provisioner = lambda_.Function(
            self,
            "KBProvisioner",
            function_name="oratio-kb-provisioner",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambdas/kb_provisioner"),
            timeout=Duration.minutes(5),
            memory_size=512,
            environment={
                "AGENTS_TABLE": agents_table.table_name,
                "KB_TABLE": knowledge_bases_table.table_name,
                "KB_BUCKET": kb_bucket.bucket_name,
            },
        )

        # Grant permissions for DynamoDB and S3
        agents_table.grant_read_write_data(self.kb_provisioner)
        knowledge_bases_table.grant_read_write_data(self.kb_provisioner)
        kb_bucket.grant_read(self.kb_provisioner)

        # --- START: CORRECTED PERMISSIONS FOR KB PROVISIONER ---
        # Policy for direct Bedrock and IAM actions that the Lambda needs to call
        # NOTE: The condition must NOT be applied to these actions, or they will fail
        self.kb_provisioner.add_to_role_policy(
            iam.PolicyStatement(
                sid="BedrockAndIamActions",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:*",          # Allows creating, managing KBs
                    "iam:CreateRole",     # Allows creating the service role for Bedrock
                    "iam:AttachRolePolicy" # Allows attaching policies to that role
                ],
                resources=["*"], # Scope down in production if possible
            )
        )

        # A separate, dedicated policy to securely grant PassRole
        # This condition only applies to PassRole, not to the other actions
        self.kb_provisioner.add_to_role_policy(
            iam.PolicyStatement(
                sid="SecurePassRoleForBedrock",
                effect=iam.Effect.ALLOW,
                actions=["iam:PassRole"],
                resources=["*"], # You can scope this to the specific role ARN pattern
                conditions={
                    "StringEquals": {
                        "iam:PassedToService": "bedrock.amazonaws.com"
                    }
                }
            )
        )
        
        # Attach AWS managed policy for comprehensive Bedrock access
        self.kb_provisioner.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )
        # --- END: CORRECTED PERMISSIONS ---

        # AgentCreator Invoker Lambda
        self.agentcreator_invoker = lambda_.Function(
            self,
            "AgentCreatorInvoker",
            function_name="oratio-agentcreator-invoker",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambdas/agentcreator_invoker"),
            timeout=Duration.minutes(15),
            memory_size=1024,
            environment={
                "AGENTS_TABLE": agents_table.table_name,
                "KB_TABLE": knowledge_bases_table.table_name,
                "CODE_BUCKET": code_bucket.bucket_name,
                "CHAMELEON_RUNTIME_ARN_SSM_PATH": "/oratio/chameleon/runtime-arn",
            },
        )

        # Grant permissions
        agents_table.grant_read_write_data(self.agentcreator_invoker)
        knowledge_bases_table.grant_read_data(self.agentcreator_invoker)
        code_bucket.grant_write(self.agentcreator_invoker)

        # Grant Bedrock AgentCore Runtime permissions to invoke AgentCreator (permissive for hackathon)
        self.agentcreator_invoker.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock-agentcore:*",
                    "bedrock:*",
                ],
                resources=["*"],
            )
        )

        # Note: Removed agentcore_deployer and code_checker Lambdas
        # agentcreator_invoker now marks agents as active directly (simpler workflow)

        # Add S3 tagging permissions
        self.agentcreator_invoker.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObjectTagging"],
                resources=[f"{code_bucket.bucket_arn}/*"],
            )
        )
        
        # Grant SSM Parameter Store read access (for AgentCreator Runtime ARN)
        # Get stack context for region and account
        stack = Stack.of(self)
        
        self.agentcreator_invoker.add_to_role_policy(
            iam.PolicyStatement(
                sid="SSMParameterAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                ],
                resources=[
                    f"arn:aws:ssm:{stack.region}:{stack.account}:parameter/oratio/*",
                ],
            )
        )
