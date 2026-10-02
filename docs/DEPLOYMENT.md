# Deploy BillSense to AWS

The provided stack hosts both the app and API on AWS. Deploy it using your own authorized AWS account. This workspace does not contain configured AWS credentials, so the project is not deployed yet.

## Prerequisites

- AWS CLI v2 authenticated using a short-lived profile / IAM Identity Center where possible.
- AWS SAM CLI, Docker (for the provided reproducible Lambda build), Node.js 22+.
- Permissions for CloudFormation, IAM roles, Lambda, API Gateway, S3, CloudFront and CloudWatch.
- Account concurrency quota permitting two reserved Lambda executions. If a new account cannot reserve that amount, adjust `ReservedConcurrentExecutions` after checking its quota.

## Deploy with AI disabled first

From the repository root on Bash (WSL or Git Bash on Windows):

```bash
export AWS_PROFILE=your-authorized-profile
export AWS_REGION=us-east-1
bash infra/deploy.sh
```

The script verifies account access, builds the frontend, packages the backend with SAM, creates the stack, uploads frontend assets, invalidates CloudFront, and prints the site URL. Review your account and region before running. CloudFront propagation can take several minutes.

Windows users without Bash can run the same npm/SAM commands manually and upload `frontend/dist/` to the bucket named in CloudFormation outputs.

The static bucket is private and only CloudFront may read it. A viewer-request function rewrites frontend navigation to `index.html`. `/api/*` has a separate behavior with caching disabled and no SPA fallback. API content is never uploaded to the static bucket. The API Gateway endpoint remains publicly reachable; CORS is not access control.

## Verify the actual deployment

- Open the CloudFront URL in a private browser window.
- Try sample bill and confirm USD 370.50 net cost.
- Upload `samples/current.csv`, inspect evidence, and export CSV.
- Open `/report` directly or refresh: the app should explain that reports clear on refresh.
- Check `/api/v1/health` and confirm valid JSON.
- Check malformed multipart uploads receive JSON errors, not index.html.
- Check mobile layout and keep the app reachable throughout judging.
- Confirm API caching is disabled and application logs do not contain billing content.

## Enable Bedrock separately

Choose a regional model with Converse support and access enabled in your account. Pass its model ID and exact model ARN into the SAM parameters along with `AIEnabled=true`:

```bash
sam deploy --stack-name billsense --region us-east-1 --resolve-s3 \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides AIEnabled=true BedrockModelId=YOUR_MODEL_ID BedrockModelArn=YOUR_MODEL_ARN
```

Do not paste AWS keys into the frontend. The template grants `bedrock:InvokeModel` only to the specified ARN. Cross-region inference profiles may require additional specific model/profile permissions and supported region configuration; the provided policy is for a regional model. Verify access with an opted-in upload. Provider denial, invalid output, and timeouts fall back to the calculated report.

AI output uses validated JSON rather than assuming every model supports native structured outputs. Model text is escaped and cannot supply displayed totals or arbitrary links. Semantic accuracy still needs evaluation with the chosen model before enabling AI for users.

## Cost controls

- AI disabled by default; no model charges for ordinary reports.
- API throttling: 2 requests/second, burst 5; Lambda reserved concurrency 2.
- Lambda memory 512 MB, timeout 28 seconds; model output capped at 650 tokens.
- CloudWatch logs expire after 7 days.
- Set an AWS Budget and notifications in your account. These controls reduce exposure but do not establish a hard spending cap.
- No NAT gateway, always-on compute, or database.

## Cleanup after judging

Retain the live app until evaluation is complete. When you intentionally want to remove it, empty the **specific BillSense frontend bucket** shown in stack outputs, then delete the stack with SAM/CloudFormation. Do not delete unrelated buckets or resources. CloudFront disable/delete may take time. Check for retained deployment artifacts in the SAM-managed bucket and remaining charges.
