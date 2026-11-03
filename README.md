# BillSense

[![CI](https://github.com/ajayg10/Billsense/actions/workflows/ci.yml/badge.svg)](https://github.com/ajayg10/Billsense/actions/workflows/ci.yml)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-AWS%20Amplify-teal)](https://main.d3opjehhlaksce.amplifyapp.com)
[![AWS Architecture](https://img.shields.io/badge/Architecture-Serverless%20%7C%20FastAPI%20%7C%20Bedrock-orange)](https://github.com/ajayg10/Billsense)

A working React + FastAPI application for understanding small AWS billing CSV exports. Monetary calculations use Python Decimal. Every finding links to source records.

[🌐 **Try the Live App on AWS Amplify**](https://main.d3opjehhlaksce.amplifyapp.com)

## Included

- **Multi-Scenario Real-World Catalog**: Instant 1-click loading for realistic billing scenarios:
  - *Student Starter Project* ($370.50 baseline across EC2, RDS, and S3).
  - *NAT Gateway & Cross-AZ Data Transfer Spike* ($642.80 with +138% network spike).
  - *Orphaned Storage & Idle RDS* ($512.40 with unattached gp3 EBS volumes and Multi-AZ DB).
- **Automated AWS Budget CloudFormation Generator**: Turnkey `AWS::Budgets::Budget` YAML template & 1-line AWS CLI deploy command to set up proactive spend alarms at 80% and 100% thresholds.
- **Interactive Cloud Savings Simulator**: What-If architectural projection for Graviton (ARM64) migration, non-production off-hours scheduling, and S3 Intelligent-Tiering.
- **Cost Spike Indicators**: Visual anomaly badges on services with significant period-over-period spend jumps.
- **Multiple Audit Export Formats**: Structured JSON audit export (`billsense-audit.json`), CSV report (`billsense-report.csv`), Copy Markdown Summary, and browser Print / Save PDF.
- **Searchable Source Evidence**: Traceable record drawer linking every calculated finding back to exact CSV line items.
- **Investigation Checklist & AWS CLI Snippets**: Read-only CLI commands and documentation links to inspect idle resources safely.
- **Zero-Trust Privacy Architecture**: Stateless backend, ephemeral memory processing, no database, no bill storage, and zero AWS credentials required.
- **Optional Amazon Bedrock Explanations**: Anonymized categories and finding IDs with strict temperature guardrails and deterministic fallback.

## Run locally

Prerequisites: Python 3.11+ and Node.js 22+.

Terminal 1, from the project root:

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell instead:
# .venv\Scripts\Activate.ps1
pip install -r backend/requirements-dev.txt
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Terminal 2, from the project root:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. Vite forwards `/api` requests to port 8000. The app works fully with AI disabled. Configuration uses environment variables; `.env.example` is a reference, not automatically loaded by the Python app. With environment-file support installed, Uvicorn can load one explicitly; otherwise export variables in your shell.

## Verify

```bash
# With the Python virtual environment activated:
cd backend
python -m pytest -q

# From frontend, with both servers running:
npm run build
npx playwright install chromium
npm run test:e2e
```

`backend/requirements-lock.txt` captures the complete tested Python environment. The production SAM package uses `backend/requirements.txt`; development tools are separate. `frontend/package-lock.json` is committed. The test configuration supports a packaged Linux Chromium fallback via `BILLSENSE_PACKAGED_BROWSER=1` when ordinary Playwright downloads are unavailable.

## CSV support

1. Generic long format: required service and cost, currency column or explicit user input, optional ISO date/region/charge type.
2. Cost Explorer wide subset: service rows and ISO date/month columns. This is not a universal adapter for every Cost Explorer export orientation.
3. Legacy CUR subset: `lineItem/ProductCode`, `lineItem/UnblendedCost`, `lineItem/CurrencyCode`, and optional usage date/region/type.

UTF-8 CSV only; 1 MiB across uploaded files, 10,000 normalized records, 100 columns, and 512 characters per cell. Large normalized responses are rejected to stay below Lambda response limits. No PDF, Excel, Parquet, or full CUR 2.0 support. Download a template in the app or use `samples/template.csv`.

## Calculation rules

Net total = all signed costs. Positive charges = positive line items. Negative adjustments = negative line items. Percent shares use positive charges, not net costs. Mixed currencies and incompatible bases are rejected. Explicit total labels are excluded; duplicate-looking records are retained and flagged. Missing daily data is not fabricated. Comparison uses the supplied exports without assuming equal duration or full coverage.

Evidence record numbers count parsed CSV records, including the header, not physical text lines. Monthly-wide records retain their original source column.

## Architecture

React on Amplify Hosting → same-origin `/api` reverse-proxy rewrite → API Gateway → Lambda/Mangum → FastAPI parser/calculator. Optional consented explanation requests call Bedrock. SAM deploys only the backend. No database and no user accounts.

The UI uses custom CSS tokens and accessible Radix dialog primitives, React Router, Recharts, and Lucide. It deliberately avoids adding Tailwind, TanStack Query, or shadcn tooling for this first small stateless release; the API client and UI remain straightforward to extend.

The repository-root `amplify.yml` builds `frontend/` and publishes its `dist/`. Set `AMPLIFY_MONOREPO_APP_ROOT=frontend` in Amplify. Run `infra/deploy.sh` to deploy the backend and generate ordered API/SPA rewrite rules. Configure those rules in Amplify separately.

See [AWS deployment](docs/DEPLOYMENT.md), [verification status](docs/VERIFICATION.md), and [hackathon checklist](docs/HACKATHON.md).

## Privacy and limitations

Uploads are transmitted to the backend and processed transiently. Reports live only in tab memory; refreshing clears them. No raw bill storage or application logging. Explicitly requested AI explanations send neutralized service categories, verified shares, and finding IDs—not raw CSVs or resource/account identifiers. Cloud infrastructure can retain operational request metadata.

Costs do not establish resource idleness or safe deletion. AI explanations are possibilities, never verified causes or savings. App does not connect to or change a user's AWS resources.
