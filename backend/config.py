from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Oratio"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCOUNT_ID: str = ""

    # DynamoDB Tables
    USERS_TABLE: str = "oratio-users"
    AGENTS_TABLE: str = "oratio-agents"
    SESSIONS_TABLE: str = "oratio-sessions"
    API_KEYS_TABLE: str = "oratio-api-keys"
    NOTIFICATIONS_TABLE: str = "oratio-notifications"

    # S3 Buckets
    KB_BUCKET: str = "oratio-knowledge-bases"
    CODE_BUCKET: str = "oratio-generated-code"
    RECORDINGS_BUCKET: str = "oratio-recordings"

    # Cognito
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_CLIENT_ID: str = ""
    COGNITO_REGION: str = "us-east-1"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Step Functions
    AGENT_CREATION_STATE_MACHINE_ARN: str = ""

    # Bedrock
    BEDROCK_REGION: str = "us-east-1"
    AGENTCREATOR_AGENT_ID: str = ""
    AGENTCREATOR_AGENT_ALIAS_ID: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
