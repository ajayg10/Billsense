# BillSense

A working React + FastAPI application for understanding small AWS billing CSV exports. Monetary calculations use Python Decimal. Every finding links to source records.

## Included

- Responsive landing page, upload and column-mapping workflow, and billing workspace.
- One-click synthetic demo with two periods; current net total **USD 370.50**, previous **USD 220.70**, change **USD 149.80**.
- Credits/adjustments, service and regional totals, daily chart when dates exist, comparisons, and data-quality notices.
- Searchable, sortable, paginated source evidence and finding drawers.
- Investigation checklist with official AWS documentation.
- CSV export and browser Print / Save PDF.
- Optional Amazon Bedrock explanations with explicit opt-in and deterministic fallback.
- AWS SAM infrastructure for Lambda, API Gateway, private S3, and CloudFront.

## Run locally

Prerequisites: Python 3.12+ and Node.js 22+.

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

React → same-origin `/api` → API Gateway → Lambda/Mangum → FastAPI parser/calculator. Optional consented explanation requests call Bedrock. S3/CloudFront serve static assets. No database and no user accounts.

The UI uses custom CSS tokens and accessible Radix dialog primitives, React Router, Recharts, and Lucide. It deliberately avoids adding Tailwind, TanStack Query, or shadcn tooling for this first small stateless release; the API client and UI remain straightforward to extend.

See [AWS deployment](docs/DEPLOYMENT.md), [verification status](docs/VERIFICATION.md), and [hackathon checklist](docs/HACKATHON.md).

## Privacy and limitations

Uploads are transmitted to the backend and processed transiently. Reports live only in tab memory; refreshing clears them. No raw bill storage or application logging. Explicitly requested AI explanations send neutralized service categories, verified shares, and finding IDs—not raw CSVs or resource/account identifiers. Cloud infrastructure can retain operational request metadata.

Costs do not establish resource idleness or safe deletion. AI explanations are possibilities, never verified causes or savings. App does not connect to or change a user's AWS resources.

No AWS deployment or real Bedrock invocation is implied by the source code. Check the verification document for what was actually tested.
