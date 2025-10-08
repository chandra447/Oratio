from aws_cdk import RemovalPolicy, aws_dynamodb as dynamodb
from constructs import Construct


class DatabaseConstruct(Construct):
    """DynamoDB tables for Oratio platform"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Users table
        self.users_table = dynamodb.Table(
            self,
            "UsersTable",
            table_name="oratio-users",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # Agents table
        self.agents_table = dynamodb.Table(
            self,
            "AgentsTable",
            table_name="oratio-agents",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="agentId", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # Add GSI for querying by agentId
        self.agents_table.add_global_secondary_index(
            index_name="agentId-index",
            partition_key=dynamodb.Attribute(name="agentId", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Sessions table
        self.sessions_table = dynamodb.Table(
            self,
            "SessionsTable",
            table_name="oratio-sessions",
            partition_key=dynamodb.Attribute(name="sessionId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.NUMBER),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # Add GSI for querying by agentId and timestamp
        self.sessions_table.add_global_secondary_index(
            index_name="agentId-timestamp-index",
            partition_key=dynamodb.Attribute(name="agentId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.NUMBER),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # API Keys table
        self.api_keys_table = dynamodb.Table(
            self,
            "ApiKeysTable",
            table_name="oratio-api-keys",
            partition_key=dynamodb.Attribute(name="apiKeyHash", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add GSI for querying by userId and agentId
        self.api_keys_table.add_global_secondary_index(
            index_name="userId-agentId-index",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="agentId", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Notifications table
        self.notifications_table = dynamodb.Table(
            self,
            "NotificationsTable",
            table_name="oratio-notifications",
            partition_key=dynamodb.Attribute(name="notificationId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="timestamp", type=dynamodb.AttributeType.NUMBER),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Add GSI for querying by userId and status
        self.notifications_table.add_global_secondary_index(
            index_name="userId-status-index",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="status", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Knowledge Bases table
        self.knowledge_bases_table = dynamodb.Table(
            self,
            "KnowledgeBasesTable",
            table_name="oratio-knowledgebases",
            partition_key=dynamodb.Attribute(
                name="knowledgeBaseId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True
            ),
        )

        # Add GSI for querying by userId
        self.knowledge_bases_table.add_global_secondary_index(
            index_name="userId-index",
            partition_key=dynamodb.Attribute(name="userId", type=dynamodb.AttributeType.STRING),
            projection_type=dynamodb.ProjectionType.ALL,
        )
