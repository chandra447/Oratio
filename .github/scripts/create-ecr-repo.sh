#!/bin/bash
# Create ECR repository if it doesn't exist
# Usage: ./create-ecr-repo.sh <repo-name> <region>

set -e

REPO_NAME=$1
REGION=${2:-us-east-1}

if [ -z "$REPO_NAME" ]; then
  echo "Error: Repository name is required"
  echo "Usage: $0 <repo-name> [region]"
  exit 1
fi

echo "Checking if ECR repository '$REPO_NAME' exists in $REGION..."

if aws ecr describe-repositories --repository-names "$REPO_NAME" --region "$REGION" >/dev/null 2>&1; then
  echo "✅ Repository '$REPO_NAME' already exists"
else
  echo "Creating ECR repository '$REPO_NAME'..."
  aws ecr create-repository \
    --repository-name "$REPO_NAME" \
    --region "$REGION" \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256
  echo "✅ Created repository '$REPO_NAME'"
fi

# Get repository URI
REPO_URI=$(aws ecr describe-repositories \
  --repository-names "$REPO_NAME" \
  --region "$REGION" \
  --query 'repositories[0].repositoryUri' \
  --output text)

echo "Repository URI: $REPO_URI"

