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
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
)
from constructs import Construct
import os


class EcsFrontendConstruct(Construct):
    """ECS Fargate + ALB + CloudFront for Next.js frontend."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        backend_api_url: str,
        image_uri: str | None = None,
        domain_name: str | None = None,
        hosted_zone_name: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        stack = Stack.of(self)

        vpc = ec2.Vpc(self, "FrontendVpc", nat_gateways=1)
        cluster = ecs.Cluster(self, "FrontendCluster", vpc=vpc)

        resolved_image_uri = image_uri or os.getenv("FRONTEND_IMAGE_URI")
        if not resolved_image_uri:
            raise ValueError(
                "FRONTEND_IMAGE_URI not provided. Pass image_uri or set env FRONTEND_IMAGE_URI during CDK deploy."
            )

        certificate = None
        zone = None
        if domain_name and hosted_zone_name:
            zone = route53.HostedZone.from_lookup(self, "FrontendZone", domain_name=hosted_zone_name)
            certificate = acm.DnsValidatedCertificate(
                self,
                "FrontendCert",
                hosted_zone=zone,
                domain_name=domain_name,
                region=stack.region,
            )

        svc = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "FrontendService",
            cluster=cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=2,
            public_load_balancer=True,
            certificate=certificate,
            redirect_http=True if certificate else False,
            protocol=elbv2.ApplicationProtocol.HTTPS if certificate else elbv2.ApplicationProtocol.HTTP,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry(resolved_image_uri),
                container_port=3000,
                environment={
                    "NEXT_PUBLIC_API_URL": backend_api_url,
                },
            ),
        )

        self.load_balancer = svc.load_balancer

        cloudfront_cache_policy = cloudfront.CachePolicy(
            self,
            "FrontendCachePolicy",
            cache_policy_name="oratio-frontend-cache",
            default_ttl=Duration.seconds(0),
            min_ttl=Duration.seconds(0),
            max_ttl=Duration.days(1),
            cookie_behavior=cloudfront.CacheCookieBehavior.all(),
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list("Authorization", "Cookie"),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
        )

        distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    domain_name=svc.load_balancer.load_balancer_dns_name,
                    protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
                ),
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cloudfront_cache_policy,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
        )

        self.cloudfront_domain = distribution.domain_name

        CfnOutput(self, "FrontendAlbDns", value=svc.load_balancer.load_balancer_dns_name)
        CfnOutput(self, "FrontendCloudFrontDomain", value=self.cloudfront_domain)

        if domain_name and zone and certificate:
            route53.ARecord(
                self,
                "FrontendAlias",
                zone=zone,
                record_name=domain_name.split(".")[0],
                target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(svc.load_balancer)),
                ttl=Duration.minutes(5),
            )


