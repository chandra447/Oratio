"""IAM roles for Bedrock AgentCore runtimes"""
from aws_cdk import aws_iam as iam, aws_s3 as s3
from constructs import Construct


class AgentCoreRolesConstruct(Construct):
    """IAM roles for AgentCore runtimes (Chameleon, AgentCreator, etc.)"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        code_bucket: s3.Bucket,
        kb_bucket: s3.Bucket,
        agents_table,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Chameleon Generic Loader Execution Role
        # This role is used by the shared Chameleon runtime to load and execute agent code
        self.chameleon_execution_role = iam.Role(
            self,
            "ChameleonExecutionRole",
            role_name="oratio-chameleon-execution-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("bedrock.amazonaws.com"),
                iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            ),
            description="Execution role for Chameleon generic loader AgentCore runtime",
        )

        # S3 Access - Read generated agent code
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3AccessForAgentCode",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket",
                ],
                resources=[
                    code_bucket.bucket_arn,
                    f"{code_bucket.bucket_arn}/*",
                ],
            )
        )

        # S3 Access - Read knowledge base files (for S3 vector store)
        # Includes both the main KB bucket and all dynamically created vector buckets
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3AccessForKnowledgeBase",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket",
                ],
                resources=[
                    kb_bucket.bucket_arn,
                    f"{kb_bucket.bucket_arn}/*",
                    "arn:aws:s3:::oratio-kb-vectors-*",  # All vector buckets
                    "arn:aws:s3:::oratio-kb-vectors-*/*",  # All objects in vector buckets
                ],
            )
        )

        # DynamoDB Access - Read agent metadata (for memory_id)
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="DynamoDBAccessForAgentMetadata",
                effect=iam.Effect.ALLOW,
                actions=[
                    "dynamodb:GetItem",
                    "dynamodb:Query",
                ],
                resources=[agents_table.table_arn],
            )
        )

        # Bedrock Foundation Model Access (includes inference profiles)
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockFoundationModelAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/*",
                    "arn:aws:bedrock:*:*:inference-profile/*",  # For cross-region inference
                ],
            )
        )

        # Bedrock Knowledge Base Access - ALL knowledge bases
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockKnowledgeBaseAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:Retrieve",
                    "bedrock:RetrieveAndGenerate",
                ],
                resources=["arn:aws:bedrock:*:*:knowledge-base/*"],
            )
        )

        # S3 Vectors Access - ALL vector buckets and indexes
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="S3VectorsAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3vectors:GetObject",
                    "s3vectors:ListBucket",
                    "s3vectors:Query",
                    "s3vectors:Search",
                ],
                resources=[
                    "arn:aws:s3vectors:*:*:bucket/*",
                    "arn:aws:s3vectors:*:*:bucket/*/index/*",
                ],
            )
        )

        # AgentCore Memory Access - Read/write conversation history
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="AgentCoreMemoryAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:GetMemory",
                    "bedrock:ListMemories",
                    "bedrock:CreateMemoryEvent",
                    "bedrock:GetMemoryEvents",
                ],
                resources=["arn:aws:bedrock:*:*:memory/*"],
            )
        )

        # CloudWatch Logs for Observability
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogsForObservability",
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["arn:aws:logs:*:*:log-group:/aws/bedrock-agentcore/*"],
            )
        )

        # X-Ray Tracing
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="XRayTracing",
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                ],
                resources=["*"],
            )
        )

        # ECR Access - Pull Docker images for AgentCore runtime
        self.chameleon_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="ECRImagePull",
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchCheckLayerAvailability",
                ],
                resources=["*"],  # GetAuthorizationToken doesn't support resource-level permissions
            )
        )

        # AgentCreator Meta-Agent Execution Role
        # This role is used by the AgentCreator meta-agent runtime
        self.agentcreator_execution_role = iam.Role(
            self,
            "AgentCreatorExecutionRole",
            role_name="oratio-agentcreator-execution-role",
            assumed_by=iam.CompositePrincipal(
                iam.ServicePrincipal("bedrock.amazonaws.com"),
                iam.ServicePrincipal("bedrock-agentcore.amazonaws.com"),
            ),
            description="Execution role for AgentCreator meta-agent AgentCore runtime",
        )

        # Bedrock Foundation Model Access for AgentCreator (includes inference profiles)
        self.agentcreator_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="BedrockFoundationModelAccess",
                effect=iam.Effect.ALLOW,
                actions=[
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream",
                ],
                resources=[
                    "arn:aws:bedrock:*::foundation-model/*",
                    "arn:aws:bedrock:*:*:inference-profile/*",  # For cross-region inference
                ],
            )
        )

        # CloudWatch Logs
        self.agentcreator_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="CloudWatchLogsForObservability",
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["arn:aws:logs:*:*:log-group:/aws/bedrock-agentcore/*"],
            )
        )

        # X-Ray Tracing
        self.agentcreator_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="XRayTracing",
                effect=iam.Effect.ALLOW,
                actions=[
                    "xray:PutTraceSegments",
                    "xray:PutTelemetryRecords",
                ],
                resources=["*"],
            )
        )

        # ECR Access - Pull Docker images for AgentCore runtime
        self.agentcreator_execution_role.add_to_policy(
            iam.PolicyStatement(
                sid="ECRImagePull",
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchCheckLayerAvailability",
                ],
                resources=["*"],  # GetAuthorizationToken doesn't support resource-level permissions
            )
        )

