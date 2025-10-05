# AWS CDK with Python

## Overview

We use **AWS CDK (Cloud Development Kit) with Python** for infrastructure as code. This allows us to define AWS resources using Python instead of CloudFormation YAML/JSON or TypeScript.

## Why Python CDK?

- **Consistency**: Same language as backend (FastAPI) and meta-agent (DSPy/LangGraph)
- **Type Safety**: Python type hints for better IDE support
- **Familiarity**: Team already proficient in Python
- **Integration**: Easy to share code between CDK and application logic

## Installation

### Prerequisites
```bash
# Install Node.js (required for CDK CLI)
# macOS:
brew install node

# Install AWS CDK CLI globally
npm install -g aws-cdk

# Verify installation
cdk --version
```

### Python CDK Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install CDK libraries
pip install aws-cdk-lib constructs

# Install additional AWS libraries
pip install boto3 aws-cdk.aws-lambda-python-alpha
```

## Project Structure

```
infrastructure/
├── app.py                      # CDK app entry point
├── cdk.json                    # CDK configuration
├── requirements.txt            # Python dependencies
├── cdk.context.json           # Context values (gitignored)
└── stacks/
    ├── __init__.py
    ├── dynamodb_stack.py      # DynamoDB tables
    ├── s3_stack.py            # S3 buckets
    ├── lambda_stack.py        # Lambda functions
    ├── stepfunctions_stack.py # Step Functions
    ├── cognito_stack.py       # Cognito User Pool
    └── bedrock_stack.py       # Bedrock resources
```

## CDK App Entry Point

**infrastructure/app.py**:
```python
#!/usr/bin/env python3
import os
from aws_cdk import App, Environment
from stacks.dynamodb_stack import DynamoDBStack
from stacks.s3_stack import S3Stack
from stacks.lambda_stack import LambdaStack
from stacks.stepfunctions_stack import StepFunctionsStack
from stacks.cognito_stack import CognitoStack

app = App()

# Define environment
env = Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
)

# Create stacks
cognito_stack = CognitoStack(app, "OratioAuthStack", env=env)
dynamodb_stack = DynamoDBStack(app, "OratioDatabaseStack", env=env)
s3_stack = S3Stack(app, "OratioStorageStack", env=env)
lambda_stack = LambdaStack(
    app, 
    "OratioLambdaStack",
    dynamodb_tables=dynamodb_stack.tables,
    s3_buckets=s3_stack.buckets,
    env=env
)
stepfunctions_stack = StepFunctionsStack(
    app,
    "OratioWorkflowStack",
    lambda_functions=lambda_stack.functions,
    env=env
)

app.synth()
```

## Example Stack: DynamoDB

**infrastructure/stacks/dynamodb_stack.py**:
```python
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as dynamodb,
)
from constructs import Construct

class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Users table
        self.users_table = dynamodb.Table(
            self, "UsersTable",
            table_name="oratio-users",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )
        
        # Agents table
        self.agents_table = dynamodb.Table(
            self, "AgentsTable",
            table_name="oratio-agents",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="agentId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )
        
        # Add GSI for querying by agentId
        self.agents_table.add_global_secondary_index(
            index_name="agentId-index",
            partition_key=dynamodb.Attribute(
                name="agentId",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        # Sessions table
        self.sessions_table = dynamodb.Table(
            self, "SessionsTable",
            table_name="oratio-sessions",
            partition_key=dynamodb.Attribute(
                name="sessionId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )
        
        # Add GSI for querying by agentId and timestamp
        self.sessions_table.add_global_secondary_index(
            index_name="agentId-timestamp-index",
            partition_key=dynamodb.Attribute(
                name="agentId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        # API Keys table
        self.api_keys_table = dynamodb.Table(
            self, "ApiKeysTable",
            table_name="oratio-api-keys",
            partition_key=dynamodb.Attribute(
                name="apiKeyHash",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # Add GSI for querying by userId and agentId
        self.api_keys_table.add_global_secondary_index(
            index_name="userId-agentId-index",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="agentId",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        # Notifications table
        self.notifications_table = dynamodb.Table(
            self, "NotificationsTable",
            table_name="oratio-notifications",
            partition_key=dynamodb.Attribute(
                name="notificationId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp",
                type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # Add GSI for querying by userId and status
        self.notifications_table.add_global_secondary_index(
            index_name="userId-status-index",
            partition_key=dynamodb.Attribute(
                name="userId",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="status",
                type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
        
        # Export tables for use in other stacks
        self.tables = {
            "users": self.users_table,
            "agents": self.agents_table,
            "sessions": self.sessions_table,
            "api_keys": self.api_keys_table,
            "notifications": self.notifications_table,
        }
```

## Example Stack: S3 Buckets

**infrastructure/stacks/s3_stack.py**:
```python
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_iam as iam,
)
from constructs import Construct

class S3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Knowledge bases bucket
        self.kb_bucket = s3.Bucket(
            self, "KnowledgeBasesBucket",
            bucket_name="oratio-knowledge-bases",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    noncurrent_version_expiration=Duration.days(90)
                )
            ]
        )
        
        # Generated code bucket
        self.code_bucket = s3.Bucket(
            self, "GeneratedCodeBucket",
            bucket_name="oratio-generated-code",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # Recordings bucket
        self.recordings_bucket = s3.Bucket(
            self, "RecordingsBucket",
            bucket_name="oratio-recordings",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="TransitionToIA",
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER,
                            transition_after=Duration.days(90)
                        )
                    ]
                )
            ]
        )
        
        # Export buckets
        self.buckets = {
            "knowledge_bases": self.kb_bucket,
            "generated_code": self.code_bucket,
            "recordings": self.recordings_bucket,
        }
```

## Example Stack: Lambda Functions

**infrastructure/stacks/lambda_stack.py**:
```python
from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from aws_cdk.aws_lambda_python_alpha import PythonFunction
from constructs import Construct

class LambdaStack(Stack):
    def __init__(
        self, 
        scope: Construct, 
        construct_id: str,
        dynamodb_tables: dict,
        s3_buckets: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # KB Provisioner Lambda
        self.kb_provisioner = PythonFunction(
            self, "KBProvisioner",
            function_name="oratio-kb-provisioner",
            entry="./lambdas/kb_provisioner",
            runtime=lambda_.Runtime.PYTHON_3_11,
            index="handler.py",
            handler="lambda_handler",
            timeout=Duration.minutes(5),
            memory_size=512,
            environment={
                "AGENTS_TABLE": dynamodb_tables["agents"].table_name,
                "KB_BUCKET": s3_buckets["knowledge_bases"].bucket_name,
            }
        )
        
        # Grant permissions
        dynamodb_tables["agents"].grant_read_write_data(self.kb_provisioner)
        s3_buckets["knowledge_bases"].grant_read(self.kb_provisioner)
        
        # Grant Bedrock permissions
        self.kb_provisioner.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:CreateKnowledgeBase",
                    "bedrock:CreateDataSource",
                    "bedrock:StartIngestionJob",
                ],
                resources=["*"]
            )
        )
        
        # AgentCreator Invoker Lambda
        self.agentcreator_invoker = PythonFunction(
            self, "AgentCreatorInvoker",
            function_name="oratio-agentcreator-invoker",
            entry="./lambdas/agentcreator_invoker",
            runtime=lambda_.Runtime.PYTHON_3_11,
            index="handler.py",
            handler="lambda_handler",
            timeout=Duration.minutes(15),
            memory_size=1024,
            environment={
                "AGENTS_TABLE": dynamodb_tables["agents"].table_name,
            }
        )
        
        # Grant permissions
        dynamodb_tables["agents"].grant_read_write_data(self.agentcreator_invoker)
        
        # Grant AgentCore permissions
        self.agentcreator_invoker.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:InvokeAgent",
                ],
                resources=["*"]
            )
        )
        
        # AgentCore Deployer Lambda
        self.agentcore_deployer = PythonFunction(
            self, "AgentCoreDeployer",
            function_name="oratio-agentcore-deployer",
            entry="./lambdas/agentcore_deployer",
            runtime=lambda_.Runtime.PYTHON_3_11,
            index="handler.py",
            handler="lambda_handler",
            timeout=Duration.minutes(10),
            memory_size=1024,
            environment={
                "AGENTS_TABLE": dynamodb_tables["agents"].table_name,
                "CODE_BUCKET": s3_buckets["generated_code"].bucket_name,
            }
        )
        
        # Grant permissions
        dynamodb_tables["agents"].grant_read_write_data(self.agentcore_deployer)
        s3_buckets["generated_code"].grant_read(self.agentcore_deployer)
        
        # Grant AgentCore deployment permissions
        self.agentcore_deployer.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "bedrock:CreateAgent",
                    "bedrock:UpdateAgent",
                    "bedrock:CreateAgentAlias",
                ],
                resources=["*"]
            )
        )
        
        # Export functions
        self.functions = {
            "kb_provisioner": self.kb_provisioner,
            "agentcreator_invoker": self.agentcreator_invoker,
            "agentcore_deployer": self.agentcore_deployer,
        }
```

## Example Stack: Step Functions

**infrastructure/stacks/stepfunctions_stack.py**:
```python
from aws_cdk import (
    Stack,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
)
from constructs import Construct

class StepFunctionsStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lambda_functions: dict,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Define tasks
        kb_provisioner_task = tasks.LambdaInvoke(
            self, "KBProvisionerTask",
            lambda_function=lambda_functions["kb_provisioner"],
            output_path="$.Payload",
        )
        
        agentcreator_invoker_task = tasks.LambdaInvoke(
            self, "AgentCreatorInvokerTask",
            lambda_function=lambda_functions["agentcreator_invoker"],
            output_path="$.Payload",
        )
        
        wait_for_code = sfn.Wait(
            self, "WaitForCode",
            time=sfn.WaitTime.duration(Duration.seconds(30))
        )
        
        check_code_task = tasks.LambdaInvoke(
            self, "CheckCodeTask",
            lambda_function=lambda_functions["agentcore_deployer"],
            payload=sfn.TaskInput.from_object({
                "action": "check_code",
                "agentId": sfn.JsonPath.string_at("$.agentId")
            }),
            output_path="$.Payload",
        )
        
        deployer_task = tasks.LambdaInvoke(
            self, "DeployerTask",
            lambda_function=lambda_functions["agentcore_deployer"],
            output_path="$.Payload",
        )
        
        # Define workflow
        definition = kb_provisioner_task \
            .next(agentcreator_invoker_task) \
            .next(wait_for_code) \
            .next(check_code_task) \
            .next(sfn.Choice(self, "CodeReady?")
                .when(
                    sfn.Condition.boolean_equals("$.codeReady", True),
                    deployer_task
                )
                .otherwise(wait_for_code)
            )
        
        # Create state machine
        self.state_machine = sfn.StateMachine(
            self, "AgentCreationWorkflow",
            state_machine_name="oratio-agent-creation",
            definition=definition,
        )
```

## CDK Commands

```bash
# List all stacks
cdk list

# Synthesize CloudFormation template
cdk synth

# Show differences between deployed and local
cdk diff

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy OratioAuthStack

# Destroy all stacks
cdk destroy --all

# Bootstrap (first time only)
cdk bootstrap aws://ACCOUNT-NUMBER/REGION
```

## Best Practices

1. **Use Constructs**: Create reusable constructs for common patterns
2. **Environment Variables**: Use environment variables for configuration
3. **Cross-Stack References**: Pass resources between stacks via constructor parameters
4. **Removal Policies**: Use `RETAIN` for production data, `DESTROY` for dev
5. **Tagging**: Add tags to all resources for cost tracking and organization
6. **IAM Least Privilege**: Grant only necessary permissions
7. **Testing**: Write unit tests for CDK stacks using `aws-cdk.assertions`

## Environment Configuration

**cdk.json**:
```json
{
  "app": "python3 app.py",
  "watch": {
    "include": [
      "**"
    ],
    "exclude": [
      "README.md",
      "cdk*.json",
      "requirements*.txt",
      "source.bat",
      "**/__init__.py",
      "**/__pycache__",
      "tests"
    ]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target-partitions": [
      "aws",
      "aws-cn"
    ],
    "@aws-cdk-containers/ecs-service-extensions:enableDefaultLogDriver": true,
    "@aws-cdk/aws-ec2:uniqueImdsv2TemplateName": true,
    "@aws-cdk/aws-ecs:arnFormatIncludesClusterName": true,
    "@aws-cdk/aws-iam:minimizePolicies": true,
    "@aws-cdk/core:validateSnapshotRemovalPolicy": true,
    "@aws-cdk/aws-codepipeline:crossAccountKeyAliasStackSafeResourceName": true,
    "@aws-cdk/aws-s3:createDefaultLoggingPolicy": true,
    "@aws-cdk/aws-sns-subscriptions:restrictSqsDescryption": true,
    "@aws-cdk/aws-apigateway:disableCloudWatchRole": true,
    "@aws-cdk/core:enablePartitionLiterals": true,
    "@aws-cdk/aws-events:eventsTargetQueueSameAccount": true,
    "@aws-cdk/aws-iam:standardizedServicePrincipals": true,
    "@aws-cdk/aws-ecs:disableExplicitDeploymentControllerForCircuitBreaker": true,
    "@aws-cdk/aws-iam:importedRoleStackSafeDefaultPolicyName": true,
    "@aws-cdk/aws-s3:serverAccessLogsUseBucketPolicy": true,
    "@aws-cdk/aws-route53-patters:useCertificate": true,
    "@aws-cdk/customresources:installLatestAwsSdkDefault": false,
    "@aws-cdk/aws-rds:databaseProxyUniqueResourceName": true,
    "@aws-cdk/aws-codedeploy:removeAlarmsFromDeploymentGroup": true,
    "@aws-cdk/aws-apigateway:authorizerChangeDeploymentLogicalId": true,
    "@aws-cdk/aws-ec2:launchTemplateDefaultUserData": true,
    "@aws-cdk/aws-secretsmanager:useAttachedSecretResourcePolicyForSecretTargetAttachments": true,
    "@aws-cdk/aws-redshift:columnId": true,
    "@aws-cdk/aws-stepfunctions-tasks:enableEmrServicePolicyV2": true,
    "@aws-cdk/aws-ec2:restrictDefaultSecurityGroup": true,
    "@aws-cdk/aws-apigateway:requestValidatorUniqueId": true,
    "@aws-cdk/aws-kms:aliasNameRef": true,
    "@aws-cdk/aws-autoscaling:generateLaunchTemplateInsteadOfLaunchConfig": true,
    "@aws-cdk/core:includePrefixInUniqueNameGeneration": true,
    "@aws-cdk/aws-efs:denyAnonymousAccess": true,
    "@aws-cdk/aws-opensearchservice:enableOpensearchMultiAzWithStandby": true,
    "@aws-cdk/aws-lambda-nodejs:useLatestRuntimeVersion": true,
    "@aws-cdk/aws-efs:mountTargetOrderInsensitiveLogicalId": true,
    "@aws-cdk/aws-rds:auroraClusterChangeScopeOfInstanceParameterGroupWithEachParameters": true,
    "@aws-cdk/aws-appsync:useArnForSourceApiAssociationIdentifier": true,
    "@aws-cdk/aws-rds:preventRenderingDeprecatedCredentials": true,
    "@aws-cdk/aws-codepipeline-actions:useNewDefaultBranchForCodeCommitSource": true,
    "@aws-cdk/aws-cloudwatch-actions:changeLambdaPermissionLogicalIdForLambdaAction": true,
    "@aws-cdk/aws-codepipeline:crossAccountKeysDefaultValueToFalse": true,
    "@aws-cdk/aws-codepipeline:defaultPipelineTypeToV2": true,
    "@aws-cdk/aws-kms:reduceCrossAccountRegionPolicyScope": true,
    "@aws-cdk/aws-eks:nodegroupNameAttribute": true,
    "@aws-cdk/aws-ec2:ebsDefaultGp3Volume": true,
    "@aws-cdk/aws-ecs:removeDefaultDeploymentAlarm": true,
    "@aws-cdk/custom-resources:logApiResponseDataPropertyTrueDefault": false,
    "@aws-cdk/aws-s3:keepNotificationInImportedBucket": false
  }
}
```

## Resources

- **AWS CDK Python Documentation**: https://docs.aws.amazon.com/cdk/api/v2/python/
- **CDK Workshop**: https://cdkworkshop.com/
- **CDK Patterns**: https://cdkpatterns.com/
- **AWS Construct Library**: https://docs.aws.amazon.com/cdk/api/v2/python/modules.html
