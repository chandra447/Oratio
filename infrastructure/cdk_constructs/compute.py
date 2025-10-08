from aws_cdk import Duration, aws_lambda as lambda_, aws_iam as iam, aws_dynamodb as dynamodb, aws_s3 as s3
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
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # KB Provisioner Lambda
        self.kb_provisioner = lambda_.Function(
            self,
            "KBProvisioner",
            function_name="oratio-kb-provisioner",
            runtime=lambda_.Runtime.PYTHON_3_11,
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

        # Grant permissions
        agents_table.grant_read_write_data(self.kb_provisioner)
        knowledge_bases_table.grant_read_write_data(self.kb_provisioner)
        kb_bucket.grant_read(self.kb_provisioner)

        # Grant Bedrock permissions
        self.kb_provisioner.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:CreateKnowledgeBase",
                    "bedrock:CreateDataSource",
                    "bedrock:StartIngestionJob",
                ],
                resources=["*"],
            )
        )

        # AgentCreator Invoker Lambda
        self.agentcreator_invoker = lambda_.Function(
            self,
            "AgentCreatorInvoker",
            function_name="oratio-agentcreator-invoker",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambdas/agentcreator_invoker"),
            timeout=Duration.minutes(15),
            memory_size=1024,
            environment={
                "AGENTS_TABLE": agents_table.table_name,
                "KB_TABLE": knowledge_bases_table.table_name,
                "CODE_BUCKET": code_bucket.bucket_name,
                "AGENTCREATOR_AGENT_ID": "",  # To be configured after AgentCreator is deployed
                "AGENTCREATOR_AGENT_ALIAS_ID": "TSTALIASID",
            },
        )

        # Grant permissions
        agents_table.grant_read_write_data(self.agentcreator_invoker)
        knowledge_bases_table.grant_read_data(self.agentcreator_invoker)
        code_bucket.grant_write(self.agentcreator_invoker)

        # Grant Bedrock Agent Runtime permissions to invoke AgentCreator
        self.agentcreator_invoker.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeAgent",
                    "bedrock:InvokeModel",
                ],
                resources=["*"],
            )
        )

        # AgentCore Deployer Lambda
        self.agentcore_deployer = lambda_.Function(
            self,
            "AgentCoreDeployer",
            function_name="oratio-agentcore-deployer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambdas/agentcore_deployer"),
            timeout=Duration.minutes(10),
            memory_size=1024,
            environment={
                "AGENTS_TABLE": agents_table.table_name,
                "CODE_BUCKET": code_bucket.bucket_name,
            },
        )

        # Grant permissions
        agents_table.grant_read_write_data(self.agentcore_deployer)
        code_bucket.grant_read(self.agentcore_deployer)

        # Grant AgentCore deployment permissions
        self.agentcore_deployer.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:CreateAgent",
                    "bedrock:UpdateAgent",
                    "bedrock:CreateAgentAlias",
                    "bedrock:PrepareAgent",
                    "bedrock:GetAgent",
                    "bedrock:AssociateAgentKnowledgeBase",
                ],
                resources=["*"],
            )
        )

        # Code Checker Lambda
        self.code_checker = lambda_.Function(
            self,
            "CodeChecker",
            function_name="oratio-code-checker",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("../lambdas/code_checker"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "CODE_BUCKET": code_bucket.bucket_name,
            },
        )

        # Grant permissions
        code_bucket.grant_read(self.code_checker)

        # Add additional Bedrock permissions for KB Provisioner
        self.kb_provisioner.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:GetIngestionJob",
                    "aoss:APIAccessAll",  # OpenSearch Serverless access
                ],
                resources=["*"],
            )
        )

        # Add S3 tagging permissions
        self.agentcreator_invoker.add_to_role_policy(
            iam.PolicyStatement(
                actions=["s3:PutObjectTagging"],
                resources=[f"{code_bucket.bucket_arn}/*"],
            )
        )
