#!/bin/bash
set -e

# Script to invalidate CloudFront cache for the Oratio frontend
# Usage: ./scripts/invalidate_cloudfront.sh

echo "🔍 Finding CloudFront distribution for frontend..."

# Get AWS region from environment or default to us-east-1
AWS_REGION="${AWS_REGION:-us-east-1}"

# Get the distribution ID for the frontend CloudFront
# Try multiple methods to find the distribution

# Method 1: Try CloudFormation outputs first (most reliable after deployment)
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
  --region "$AWS_REGION" \
  --stack-name OratioStack \
  --query "Stacks[0].Outputs[?OutputKey=='FrontendDistributionId'].OutputValue" \
  --output text 2>/dev/null || echo "")

# Method 2: Look for distribution with "frontend" in the origin domain name
if [ -z "$DISTRIBUTION_ID" ] || [ "$DISTRIBUTION_ID" == "None" ]; then
  echo "🔄 Trying CloudFront API..."
  DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[*].{Id:Id,Origins:Origins.Items[0].DomainName}" \
    --output json 2>/dev/null | jq -r '.[] | select(.Origins | contains("frontend")) | .Id' | head -1)
fi

# Method 3: Get the most recently modified distribution as last resort
if [ -z "$DISTRIBUTION_ID" ]; then
  echo "🔄 Getting most recent distribution..."
  DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items | sort_by(@, &LastModifiedTime) | [-1].Id" \
    --output text 2>/dev/null || echo "")
fi

if [ -z "$DISTRIBUTION_ID" ] || [ "$DISTRIBUTION_ID" == "None" ]; then
  echo "⚠️  Could not find CloudFront distribution"
  echo "ℹ️  Skipping cache invalidation (distribution may not exist yet)"
  exit 0
fi

echo "✅ Found distribution: $DISTRIBUTION_ID"
echo "🗑️  Creating invalidation for all paths..."

# Create invalidation
INVALIDATION_OUTPUT=$(aws cloudfront create-invalidation \
  --distribution-id "$DISTRIBUTION_ID" \
  --paths "/*" \
  --query 'Invalidation.{Id:Id,Status:Status,CreateTime:CreateTime}' \
  --output json)

INVALIDATION_ID=$(echo "$INVALIDATION_OUTPUT" | jq -r '.Id')
echo "✅ Invalidation created: $INVALIDATION_ID"
echo "⏳ Waiting for invalidation to complete..."

# Wait for invalidation to complete
aws cloudfront wait invalidation-completed \
  --distribution-id "$DISTRIBUTION_ID" \
  --id "$INVALIDATION_ID"

echo "✅ CloudFront cache invalidation completed!"
echo "🌐 Your frontend should now serve the latest version"

