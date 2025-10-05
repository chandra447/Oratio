from aws_cdk import RemovalPolicy, Duration, aws_s3 as s3
from constructs import Construct


class StorageConstruct(Construct):
    """S3 buckets for Oratio platform"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Knowledge bases bucket
        self.kb_bucket = s3.Bucket(
            self,
            "KnowledgeBasesBucket",
            bucket_name="oratio-knowledge-bases",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions", noncurrent_version_expiration=Duration.days(90)
                )
            ],
        )

        # Generated code bucket
        self.code_bucket = s3.Bucket(
            self,
            "GeneratedCodeBucket",
            bucket_name="oratio-generated-code",
            versioned=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
        )

        # Recordings bucket
        self.recordings_bucket = s3.Bucket(
            self,
            "RecordingsBucket",
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
                            transition_after=Duration.days(30),
                        ),
                        s3.Transition(
                            storage_class=s3.StorageClass.GLACIER, transition_after=Duration.days(90)
                        ),
                    ],
                )
            ],
        )
