from aws_cdk import (
    Duration,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_s3 as s3,
    CfnOutput,
)
from constructs import Construct


class ApiCdnConstruct(Construct):
    """CloudFront in front of ALB to provide HTTPS default domain without buying DNS.

    - Origin: Application Load Balancer DNS
    - Behavior: No caching for API, forward all query strings and required headers
    - Outputs: CloudFrontDomain
    """

    def __init__(self, scope: Construct, construct_id: str, *, alb_dns_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Origin to ALB (HTTP)
        origin = origins.HttpOrigin(
            domain_name=alb_dns_name,
            protocol_policy=cloudfront.OriginProtocolPolicy.HTTP_ONLY,
        )

        # Disable caching for API; forward query strings and important headers
        cache_policy = cloudfront.CachePolicy(
            self,
            "ApiNoCachePolicy",
            cache_policy_name="oratio-api-no-cache",
            default_ttl=Duration.seconds(0),
            min_ttl=Duration.seconds(0),
            max_ttl=Duration.seconds(0),
            header_behavior=cloudfront.CacheHeaderBehavior.allow_list(
                "Authorization", "X-API-Key", "Origin"
            ),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
        )

        origin_request_policy = cloudfront.OriginRequestPolicy(
            self,
            "ApiOriginRequestPolicy",
            origin_request_policy_name="oratio-api-origin-req",
            header_behavior=cloudfront.OriginRequestHeaderBehavior.all(),
            query_string_behavior=cloudfront.OriginRequestQueryStringBehavior.all(),
            cookie_behavior=cloudfront.OriginRequestCookieBehavior.all(),
        )

        self.distribution = cloudfront.Distribution(
            self,
            "ApiDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origin,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cache_policy,
                origin_request_policy=origin_request_policy,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
            comment="Oratio API CDN",
        )

        self.domain_name = self.distribution.domain_name

        CfnOutput(
            self,
            "ApiCloudFrontDomain",
            value=self.domain_name,
            export_name="Oratio-ApiCloudFrontDomain",
        )


