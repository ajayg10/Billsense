#!/usr/bin/env bash
# Deploy only the backend. Amplify builds/publishes frontend from GitHub.
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
stack_name="${BILLSENSE_STACK:-billsense-backend}"
region="${AWS_REGION:-${AWS_DEFAULT_REGION:-us-east-1}}"
ai_enabled="${AI_ENABLED:-false}"
model_id="${BEDROCK_MODEL_ID:-}"
model_arn="${BEDROCK_MODEL_ARN:-}"
allowed_origins="${ALLOWED_ORIGINS:-https://example.invalid}"
for dependency in aws sam python3; do
  command -v "$dependency" >/dev/null || { echo "Install $dependency first." >&2; exit 1; }
done
if [[ "$ai_enabled" != false && "$ai_enabled" != true ]]; then
  echo 'AI_ENABLED must be true or false.' >&2; exit 1
fi
if [[ "$ai_enabled" == true && ( -z "$model_id" || -z "$model_arn" ) ]]; then
  echo 'Set BEDROCK_MODEL_ID and BEDROCK_MODEL_ARN when enabling AI.' >&2; exit 1
fi
aws sts get-caller-identity --query Account --output text >/dev/null
# Do not turn a previously deployed full stack into a backend-only stack by accident.
stack_inventory="$(aws cloudformation list-stacks --region "$region" --query "StackSummaries[?StackStatus!='DELETE_COMPLETE'].StackName" --output json)"
stack_exists="$(python3 -c 'import json,sys; print("yes" if sys.argv[1] in json.load(sys.stdin) else "no")' "$stack_name" <<< "$stack_inventory")"
if [[ "$stack_exists" == yes ]]; then
  resources="$(aws cloudformation list-stack-resources --stack-name "$stack_name" --region "$region" --query 'StackResourceSummaries[].ResourceType' --output json)"
  if python3 -c 'import json,sys; sys.exit(0 if any(t in ("AWS::S3::Bucket", "AWS::CloudFront::Distribution") for t in json.load(sys.stdin)) else 1)' <<< "$resources"; then
    echo 'This stack owns S3/CloudFront hosting. Choose a new BILLSENSE_STACK name; existing hosting will not be removed.' >&2
    exit 1
  fi
fi
cd "$project_root"
build_options=(--template-file infra/template.yaml --build-dir .aws-sam/backend)
if [[ "${SAM_USE_CONTAINER:-true}" == true ]]; then
  command -v docker >/dev/null || { echo 'Docker is required, or set SAM_USE_CONTAINER=false with local Python 3.12.' >&2; exit 1; }
  build_options+=(--use-container)
fi
sam build "${build_options[@]}"
sam deploy --template-file .aws-sam/backend/template.yaml --stack-name "$stack_name" \
  --region "$region" --resolve-s3 --capabilities CAPABILITY_IAM --confirm-changeset \
  --no-fail-on-empty-changeset \
  --parameter-overrides "AIEnabled=$ai_enabled" "BedrockModelId=$model_id" \
  "BedrockModelArn=$model_arn" "AllowedOrigins=$allowed_origins"
api_url="$(aws cloudformation describe-stacks --stack-name "$stack_name" --region "$region" --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue | [0]" --output text)"
# Stage the generated file before replacing any earlier valid output.
rewrite_temp="$(mktemp)"
trap 'rm -f "$rewrite_temp"' EXIT
python3 infra/amplify-rewrites.py "$api_url" > "$rewrite_temp"
mv "$rewrite_temp" infra/amplify-rewrites.generated.json
printf '\nBackend API: %s\nHealth check: %s/api/v1/health\n' "$api_url" "$api_url"
printf 'Amplify rewrite rules: infra/amplify-rewrites.generated.json\n'
printf 'Deploy frontend through Amplify, then verify sample AND CSV upload.\n'
