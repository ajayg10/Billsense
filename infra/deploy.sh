#!/usr/bin/env bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
stack_name="${BILLSENSE_STACK:-billsense}"
region="${AWS_REGION:-us-east-1}"
command -v aws >/dev/null || { echo 'Install AWS CLI v2 first.'; exit 1; }
command -v sam >/dev/null || { echo 'Install AWS SAM CLI first.'; exit 1; }
aws sts get-caller-identity --query Account --output text >/dev/null
cd "$project_root/frontend"
npm ci
npm run build
cd "$project_root"
sam build --template-file infra/template.yaml --use-container
sam deploy --stack-name "$stack_name" --region "$region" --resolve-s3 --capabilities CAPABILITY_IAM --no-fail-on-empty-changeset
bucket_name="$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$region" --query "Stacks[0].Outputs[?OutputKey=='FrontendBucket'].OutputValue | [0]" --output text)"
distribution_id="$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$region" --query "Stacks[0].Outputs[?OutputKey=='DistributionId'].OutputValue | [0]" --output text)"
aws s3 sync frontend/dist/ "s3://$bucket_name/" --cache-control 'public,max-age=300' --region "$region"
aws cloudfront create-invalidation --distribution-id "$distribution_id" --paths '/*' --query Invalidation.Id --output text
aws cloudformation describe-stacks --stack-name "$stack_name" --region "$region" --query "Stacks[0].Outputs[?OutputKey=='WebsiteUrl'].OutputValue | [0]" --output text
