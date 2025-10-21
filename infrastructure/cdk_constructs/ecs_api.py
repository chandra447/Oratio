from aws_cdk import (
    Duration,
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as elbv2,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_iam as iam,
    aws_ssm as ssm,
)
from constructs import Construct
import os


class EcsApiConstruct(Construct):
    """ECS Fargate + ALB service for FastAPI backend.

    - Uses a pre-built ECR image (provided via BACKEND_IMAGE_URI or constructor)
    - Injects Cognito config from SSM Parameter Store as container secrets
    - Exposes service via Application Load Balancer (HTTP by default, optional HTTPS)
    - Attaches permissive IAM policies as requested (consider scoping down later)
    - Outputs the base URL for frontend to consume as `NEXT_PUBLIC_API_URL`
    """

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str | None = None,
        hosted_zone_name: str | None = None,
        image_uri: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        stack = Stack.of(self)

        # VPC and ECS Cluster
        vpc = ec2.Vpc(self, "ApiVpc", nat_gateways=1)
        cluster = ecs.Cluster(self, "ApiCluster", vpc=vpc)

        # Resolve backend image URI from CI-provided env or parameter
        resolved_image_uri = image_uri or os.getenv("BACKEND_IMAGE_URI")
        if not resolved_image_uri:
            raise ValueError(
                "BACKEND_IMAGE_URI not provided. Pass image_uri to EcsApiConstruct or set env BACKEND_IMAGE_URI during CDK deploy."
            )

        # Optional custom domain + certificate
        certificate = None
        zone = None
        if domain_name and hosted_zone_name:
            zone = route53.HostedZone.from_lookup(self, "ApiZone", domain_name=hosted_zone_name)
            certificate = acm.DnsValidatedCertificate(
                self,
                "ApiCert",
                hosted_zone=zone,
                domain_name=domain_name,
                region=stack.region,
            )

        # Fargate service behind ALB (ARM64/Graviton for cost savings)
        svc = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FastApiService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            public_load_balancer=True,
            certificate=certificate,
            redirect_http=True if certificate else False,
            protocol=elbv2.ApplicationProtocol.HTTPS if certificate else elbv2.ApplicationProtocol.HTTP,
            runtime_platform=ecs.RuntimePlatform(
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=ecs.CpuArchitecture.ARM64,
            ),
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(resolved_image_uri),
                container_port=8000,
                environment={
                    "AWS_REGION": stack.region,
                    "API_V1_PREFIX": "/api/v1",
                    # Allow CORS from any origin for now (tighten in production)
                    "CORS_ORIGINS": '["*"]',
                },
                secrets={
                    "COGNITO_CLIENT_ID": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_string_parameter_name(
                            self, "CognitoClientIdParam", "/oratio/cognito/client_id"
                        )
                    ),
                    "COGNITO_USER_POOL_ID": ecs.Secret.from_ssm_parameter(
                        ssm.StringParameter.from_string_parameter_name(
                            self, "CognitoUserPoolIdParam", "/oratio/cognito/user_pool_id"
                        )
                    ),
                },
            ),
        )

        # Expose ALB to other constructs
        self.load_balancer = svc.load_balancer

        # Health check - FastAPI chat health endpoint
        svc.target_group.configure_health_check(path="/api/v1/chat/health", healthy_http_codes="200")

        # Grant ECR pull permissions to Task Execution Role
        # This allows ECS to pull the Docker image from ECR
        execution_role = svc.task_definition.execution_role
        execution_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ecr:GetAuthorizationToken",
                    "ecr:BatchCheckLayerAvailability",
                    "ecr:GetDownloadUrlForLayer",
                    "ecr:BatchGetImage",
                ],
                resources=["*"],
            )
        )

        # Requested wide IAM access for the Task Role (scope down for prod)
        task_role = svc.task_definition.task_role
        task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMReadOnlyAccess"))
        task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"))
        task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"))
        task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess"))
        task_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AWSStepFunctionsFullAccess"))
        task_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["bedrock:*", "bedrock-agentcore:*", "s3vectors:*"],
                resources=["*"],
            )
        )

        alb_dns = svc.load_balancer.load_balancer_dns_name

        CfnOutput(self, "ApiAlbDns", value=alb_dns, export_name="Oratio-ApiAlbDns")
        CfnOutput(
            self,
            "ApiBaseUrl",
            value=(f"https://{domain_name}" if certificate else f"http://{alb_dns}"),
            export_name="Oratio-ApiBaseUrl",
        )

        # Optional Route53 record if custom domain provided
        if domain_name and zone and certificate:
            route53.ARecord(
                self,
                "ApiAlias",
                zone=zone,
                record_name=domain_name.split(".")[0],
                target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(svc.load_balancer)),
                # Note: Alias records don't support custom TTL - AWS manages it automatically
            )


