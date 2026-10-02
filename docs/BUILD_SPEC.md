# BillSense — complete website build prompt

Copy this entire prompt into your coding agent in the project workspace.

---

You are a senior full-stack engineer, product designer, and AWS architect. Build **BillSense**, a polished, working web application that helps students and beginner developers understand AWS billing CSVs.

Implement the actual application, not just a plan, landing page, or UI prototype. Inspect the existing repository and its instructions first. Reuse compatible existing work. Make reasonable implementation decisions autonomously, and ask questions only for missing credentials, deployment authorization, or genuinely blocking product ambiguity. Do not claim a command, test, deployment, integration, or user study succeeded unless you verified it.

## 1. Product goal and scope

The product promise is: **“Understand your AWS bill. See the evidence. Know what to check next.”**

Target users are students, hackathon participants, and beginner developers who find AWS billing exports confusing. The primary journey is:

**Try a sample or upload a CSV → confirm the detected format → view a calculated report → inspect evidence → follow an investigation checklist → export the report.**

The distinguishing feature is evidence: every numerical finding must link to the exact source records and calculation supporting it. AI explains verified results; Python calculates all financial values.

Prioritize a complete, reliable hackathon release. Deliver all core requirements before stretch features. Do not introduce login, payments, AWS account linking, automatic infrastructure changes, multi-agent orchestration, a vector database, or a general-purpose chatbot in the initial release.

This app is an independent educational tool. Do not suggest AWS endorsement. Do not invent testimonials, adoption metrics, savings, compliance certifications, or live integrations.

## 2. Technology stack

Use this stack unless an existing repository presents a concrete compatibility issue:

- Frontend: React, TypeScript with strict checking, Vite, Tailwind CSS, accessible shadcn/ui components, Lucide icons, React Router, Recharts, and TanStack Query for server requests.
- Backend: Python 3.12, FastAPI, Pydantic v2, Uvicorn, python-multipart, and Python's CSV parser and Decimal arithmetic. Avoid a heavyweight dataframe dependency unless needed for a demonstrated requirement.
- AI: Amazon Bedrock through boto3, behind an explanation-provider interface. Model and region are environment variables. Verify the selected model's availability and API support before integrating it; do not assume all models support native structured output.
- Backend hosting: AWS Lambda with Mangum behind API Gateway HTTP API.
- Frontend hosting: private S3 bucket behind CloudFront with Origin Access Control and HTTPS.
- Infrastructure as code: AWS SAM/CloudFormation with documented build, deployment, and teardown commands.
- Observability: CloudWatch operational logs with bounded retention and no billing content.
- Testing: pytest for parsing and calculation behavior; Playwright for critical browser journeys; frontend type checking and a production build.
- Dependency management: pinned compatible packages and committed lockfiles. Verify current official installation instructions rather than combining incompatible library versions.

Use a stateless backend initially. Keep the current report in browser memory. Raw uploads, reports, and user identifiers must not be stored in a database, analytics system, or browser localStorage. UI preferences such as theme may use localStorage. Clearly state that refreshing the page clears the report.

## 3. Visual identity

Design a calm, polished financial analysis workspace with excellent readability.

- Light theme first: off-white page background, white panels, dark slate text, teal primary actions, amber investigation notices, and red only for errors or clearly labeled spending increases.
- Suggested tokens: background #F8FAFC, surface #FFFFFF, text #0F172A, muted text #475569, border #E2E8F0, primary #0F766E. Verify contrast in actual use.
- Use Inter or a high-quality system sans-serif stack. Use tabular numerals for amounts and percentages.
- Desktop content width around 1280px, 8px spacing scale, comfortable whitespace, 12–16px card corners, subtle borders and restrained shadows.
- Use real charts and data tables as the main visuals. Avoid stock photography, excessive gradients, decorative dashboards, and unnecessary motion.
- Responsive layouts for 360px phones through large desktops. Tables may scroll inside their own containers without making the entire page overflow.
- Visible keyboard focus, semantic headings, associated form labels, accessible dialogs, and reduced-motion support. Never rely on color alone. Provide chart summaries and an accessible tabular alternative.

Use specific, reassuring microcopy. Examples: “Choose a CSV,” “Show supporting rows,” “This export does not include daily dates,” and “Your calculated report is ready. AI explanations are temporarily unavailable.”

## 4. Screens and user experience

### A. Landing page at `/`

Header: original BillSense wordmark, How it works anchor, Supported formats anchor, and Try demo button.

Hero:
- Headline: “Your AWS bill, explained.”
- Supporting text: “Find your biggest charges, inspect the numbers behind them, and understand what to check next.”
- Primary action: “Try sample bill.”
- Secondary action: “Upload my CSV.”
- Short trust copy: “No AWS credentials required. No sign-up.”

Show an honest preview using the same synthetic sample data as the demo, labeled “Sample data.” Include three concise value cards: Understand charges, Verify every finding, and Plan your next checks.

Explain the three-step process and supported formats. Add a short FAQ covering credentials, AI data handling, export limitations, and the fact that the tool cannot determine whether infrastructure is safe to delete.

Footer: How calculations work, Privacy, and source-code link only if a real repository URL exists.

### B. Upload and mapping at `/analyze`

- Drag-and-drop area with keyboard-accessible file picker.
- State supported CSV types, a 1 MiB combined file limit, and a 10,000 normalized-record limit across the analysis. Enforce limits server-side as well as in the browser.
- Optional second file for comparison; show distinct Current period and Previous period inputs.
- Only accept uncompressed CSV. Explain that full large CUR exports, Excel files, and PDFs are outside this release's supported inputs.
- Display filename, size, format detection, currency, cost basis, detected period, and a small preview.
- For generic exports, allow explicit column mapping. Require confirmation when currency, date interpretation, cost basis, or period labels are ambiguous.
- Never silently assume USD, convert currencies, or interpret an ambiguous date such as 01/02/2026 without clarification.
- Identify total/summary records and explain their exclusion when their role is recognized. If their meaning is uncertain, ask for confirmation rather than double-counting them.
- Show meaningful validation errors with record references. Never silently discard malformed monetary values.
- Provide a downloadable supported template and a sample bill option.
- Explicit permission control: “Use AI to explain anonymized spending totals.” Default it off for private uploads. The deterministic report is fully usable without it.
- Show real processing stages, not fake progress percentages.

### C. Results at `/report`

Use a top toolbar with filename, period, currency, cost basis, Sample data badge when applicable, New analysis, Download CSV, and Print / Save PDF.

On desktop use compact section navigation; on mobile use a horizontal tab list or accessible dropdown. Sections: Overview, Findings, Evidence, and Next steps. Preserve filters while switching sections.

Overview:
- Cards for net cost, positive charges, credits/negative adjustments, and largest positive cost contributor.
- Comparison card only when suitable comparison data exists.
- Sorted horizontal bar chart for service costs; handle negative values explicitly.
- Daily trend only when daily data actually exists. Do not invent day-level values from monthly totals.
- Region breakdown only when region information exists.
- Concise explanatory summary with separate “Calculated” and “AI explanation” labels.
- Data-quality notice summarizing exclusions, assumptions, unknown regions, and unsupported detail.

Findings:
- Cards ordered by financial magnitude and usefulness.
- Each card includes title, factual statement, amount, period, evidence button, and relevant next check.
- Label statements as “Observed in your data” or “Possible explanation.” Use “Needs investigation” instead of calling every increase an anomaly.
- Empty state when there are no meaningful findings.

Evidence:
- Searchable, sortable, paginated normalized-record table.
- Columns for source file, CSV record number, service, date or period, region when present, cost, currency, and charge type when known.
- “Show supporting rows” opens a drawer on desktop and a full-width accessible panel on mobile, filtered to the relevant records.
- Show the calculation and included cost basis. Clarify source record numbering for quoted multiline CSV cells; do not mislabel logical record numbers as physical line numbers.
- “Show all records” clears the finding filter.

Next steps:
- Prioritized investigation cards tied to findings.
- Each includes why it is suggested, what to inspect, what the file cannot establish, and an official AWS documentation link.
- Checklist completion is session-only. It does not imply resources changed or savings occurred.

### D. Supporting pages

Implement concise `/privacy` and `/methodology` pages, an accessible 404 page, loading states, and a recoverable global error boundary.

Privacy copy must reflect the actual system: CSVs are transmitted to the backend, processed transiently, and not intentionally persisted. If opted in, a sanitized aggregate summary is sent to Bedrock. Do not claim processing is entirely on-device or make unsupported provider retention promises.

## 5. CSV support and normalization

Implement adapters with realistic fixtures and document exact supported shapes:

1. Generic long-form CSV with required service and cost columns, plus optional date, region, currency, and charge type. Let users supply a currency and period when absent.
2. AWS Cost Explorer CSV: support explicitly tested service-by-period layouts, including the common wide layout. Normalize wide cells into records and preserve source cell references. Detect total columns/records so they are not added to detail a second time. Do not claim universal Cost Explorer compatibility.
3. Small legacy CUR-style CSV subset with fields such as `lineItem/ProductCode`, `lineItem/UnblendedCost`, `lineItem/UsageStartDate`, and `lineItem/CurrencyCode`; optional region and line-item type. Missing optional fields must not crash parsing. Clearly state that CUR 2.0/Parquet and arbitrary export layouts are unsupported unless separately implemented and tested.

Core internal normalized record:
- record_id
- source_file_id
- source_record_number
- source_column_name for wide-format values
- service
- amount_decimal as a string
- currency
- period_start and period_end when known
- granularity: daily, monthly, or unspecified
- region, optional
- charge_type, optional
- cost_basis

Treat explicit exported cost fields as costs. Do not mistake usage quantities for money. Do not add amortized and unblended costs together. Reject comparisons with incompatible cost bases.

Use Decimal for financial calculations. Preserve underlying precision and round only for display. Serialize money as decimal strings. The frontend may convert values for chart placement but must not become the authoritative calculator.

Handle UTF-8 BOM, quoted commas, blank lines, whitespace, duplicate headers, malformed numbers, empty files, missing columns, and negative costs. Detect supported delimiter variants only when unambiguous. Duplicate-looking records may be legitimate; warn rather than automatically deleting them. Do not combine repeated uploads silently.

Reject mixed-currency analysis with an actionable explanation in the first release. Never combine currencies without an exchange-rate policy. Preserve credits and refunds; if the export does not classify them, call them “negative adjustments,” not definitely refunds.

## 6. Deterministic analysis rules

Implement and test:

- Net total = sum of all included signed costs.
- Positive charges = sum of positive values.
- Negative adjustments = sum of negative values, displayed consistently with its sign.
- Net total must reconcile with positive charges plus negative adjustments.
- Service totals and region totals must reconcile to net total; use an Unknown region bucket where applicable.
- Share of positive charges uses positive line-item costs as its denominator and must be labeled accordingly. Do not divide by a near-zero net total to produce misleading percentages.
- Previous/current comparison uses matching currency and basis, explicit period labels, and clearly labeled partial or unequal periods.
- Absolute change = current minus previous. Percentage change is shown only when the previous amount is positive; otherwise label new spend or percentage unavailable.
- Rank contributors to change by service. Allow both increases and reductions.
- Do not interpolate missing days or assume absent records prove zero usage. State data coverage limitations.
- Optional daily spike detection requires sufficient daily history and a transparent, documented rule. Otherwise omit it.

Do not create a cloud “health score,” claim unused resources, promise savings, infer exact resource IDs from aggregate data, or forecast future bills in the core release.

Create stable finding IDs and evidence references. Every calculated claim must be reproducible from the normalized data. Backend responses include parser warnings, data coverage, cost basis, and schema version.

## 7. AI explanations

AI is optional and may improve language and prioritization, but cannot change totals, evidence, or calculations.

- Send only allowlisted aggregate service/region categories, verified metrics, finding IDs, and neutral context.
- Do not send full CSVs, filenames, account IDs, resource IDs, tags, arbitrary raw descriptions, or other identifying fields.
- Treat all CSV-derived strings as untrusted data, never as instructions. Map unknown free-form categories to neutral labels for the model if necessary.
- Ask the model for concise explanations referencing existing finding IDs and approved next-step IDs. Keep numeric displays sourced from backend metrics.
- Use native structured output only when the configured model/API supports it. Validate every response using Pydantic regardless.
- Reject unsupported finding references and claims. Use deterministic templates if validation, credentials, model access, timeout, throttling, or network calls fail.
- Display the active mode honestly: AI explanation, Calculated summary, or AI temporarily unavailable.
- Maintain a small curated catalog of next steps and official AWS links. The model can select IDs but must not generate arbitrary URLs, destructive commands, or unverified configuration advice.
- Make calls bounded in time, input size, output tokens, and retries. Disable automatic retries on validation failures. Do not invoke the model on every filter change or page render.

Model output is rendered as escaped text or sanitized restricted Markdown. Never inject HTML from the model or CSV.

## 8. API and state design

Use versioned endpoints and consistent typed error responses:

- `GET /api/v1/health`: minimal service status; no credentials or environment details.
- `GET /api/v1/samples`: sample metadata.
- `GET /api/v1/samples/{sample_id}`: sample input or calculated report from the same pipeline used for uploads.
- `POST /api/v1/inspect`: bounded multipart input; detected format, preview, mapping requirements, and validation warnings.
- `POST /api/v1/analyze`: bounded multipart file(s), validated mapping and comparison options; deterministic report and normalized evidence.
- `POST /api/v1/explain`: bounded normalized input and explicit opt-in; revalidate and recompute aggregates server-side before generating explanations. Do not trust client-supplied totals as verified metrics.

Use Pydantic models for request options, normalized records, metrics, findings, evidence references, and explanations. Derive frontend types from OpenAPI or maintain a checked contract. Document endpoints using FastAPI OpenAPI.

No server report registry or process-memory persistence. A fresh Lambda invocation must handle every endpoint correctly. Browser session state contains the current report; a direct visit or refresh at `/report` offers sample or upload actions.

Cap response sizes and field lengths so the chosen record limits remain within the deployment's real request/response limits, including multipart/base64 overhead. Reject oversized requests and normalized expansions early. Use errors such as INVALID_CSV, MISSING_COLUMNS, AMBIGUOUS_FORMAT, MIXED_CURRENCY, INCOMPATIBLE_COMPARISON, FILE_TOO_LARGE, and AI_UNAVAILABLE with actionable messages.

## 9. Export behavior

- Download an analysis CSV containing service totals, currency, cost basis, period, and explicit sample-data labeling when applicable.
- Escape spreadsheet formula injection in untrusted text fields beginning with dangerous formula characters. Preserve numeric columns as numeric output.
- Provide print CSS and a Print / Save PDF action using the browser print dialog. Label this honestly; do not pretend a server PDF download exists.
- Print view contains summary, methodology, findings, evidence references, and next steps. Hide navigation, upload controls, and interactive-only elements.
- Verify printed layout for page breaks, clipped charts, and readable tables.

## 10. Demo data

Create a clearly synthetic, small dataset covering two comparable full periods with EC2, S3, RDS, Lambda, and data transfer categories where appropriate. Include a visible cost increase, a negative adjustment, and a documented expected reconciliation.

The sample must use the real parser and calculator. No hardcoded dashboard totals that diverge from downloadable sample inputs. Provide a one-click demo that works without Bedrock credentials. Label all screenshots, metrics, and demo explanations appropriately.

Also include development fixtures for monthly-only data, missing regions, zero prior cost, negative net cost, total rows, malformed input, and mixed currencies.

## 11. Security, privacy, and operating cost

- Never request AWS access keys from users or embed credentials in frontend code.
- Use deployment IAM roles with least privilege. Backend permissions should cover operational logging and only the model access actually needed.
- Keep .env files and credentials out of git; provide .env.example with placeholders.
- Bound bytes while reading uploads, field sizes, record counts, normalized expansions, JSON payloads, and AI inputs.
- Configure request throttling and conservative Lambda concurrency appropriate to account quotas. Clearly distinguish request-rate/concurrency limits from a hard spending cap.
- Add an AI_ENABLED kill switch and documented token/output limits. Budget alerts are notifications, not guaranteed automatic shutdown.
- Use HTTPS, precise CORS origins when cross-origin requests are necessary, safe error messages, and suitable security headers. CORS is not authentication or abuse protection.
- Set sensitive API responses to no-store. Do not cache uploaded reports in CloudFront or service workers.
- Operational logs contain request IDs, duration, parser type, and error codes only. Never log raw uploads, prompts, model responses, or report contents.
- No account linking, executable uploaded content, arbitrary outbound URL fetching, or resource deletion.
- Keep the stack small: no NAT Gateway, always-on database, Kubernetes, or infrastructure introduced only to make the architecture look elaborate.

## 12. AWS deployment

Provide reproducible infrastructure for:

1. S3 private static frontend bucket with public access blocked.
2. CloudFront distribution with Origin Access Control.
3. API Gateway HTTP API connected to the Lambda/Mangum FastAPI app.
4. Lambda role and bounded CloudWatch log retention.
5. Configurable Bedrock region/model access and an AI-disabled deployment mode.

Prefer same-origin API requests through a CloudFront `/api/*` behavior with caching disabled and correct method/header/body forwarding. Preserve API error status codes. SPA route fallback must apply only to frontend navigation; never turn API 404/500 errors into index.html responses.

Document infrastructure outputs, packaging, environment variables, local startup, deployment, smoke tests, and teardown. Verify multipart uploads end to end through API Gateway and Mangum, including binary/base64 handling. Make API timeouts and SDK timeouts compatible.

Use a CloudFront domain initially; a custom domain is optional. Do not assume DNS or account permissions exist. Prepare all deployment artifacts locally and use authorized AWS access only. If access is missing, give the exact next command or setting instead of claiming the app is deployed.

Keep the app reachable during hackathon evaluation; document later cleanup rather than removing it immediately after submission. Do not promise a zero-cost deployment or that promotional credits cover every service.

## 13. Repository and developer experience

Use a clear monorepo:

- `frontend/` — pages, reusable UI, feature components, API client, types, tests.
- `backend/app/` — API routes, schemas, CSV adapters, deterministic analytics, explanation providers, settings.
- `backend/tests/` — meaningful parser, financial, API, and failure-path tests.
- `infra/` — SAM/CloudFormation templates and deployment documentation.
- `samples/` — synthetic CSVs and expected calculations.
- `docs/` — methodology, architecture, demo script, deployment, and submission checklist.
- Root README, environment examples, lockfiles, and convenience commands.

Separate parsing, normalization, calculations, AI, and HTTP concerns. Keep financial functions pure and testable. Avoid giant components, broad exception swallowing, decorative abstraction, and TODO placeholders in the core workflow.

Document at least AWS_REGION, BEDROCK_MODEL_ID, AI_ENABLED, allowed frontend origins where applicable, and request/token limits. Never put secrets in VITE-prefixed variables.

## 14. Acceptance criteria and verification

The release is complete when:

1. A new visitor can open the public app and reach a real sample report without login.
2. Supported uploads produce accurate totals and explicit warnings.
3. Sample metrics reconcile exactly to the sample's expected Decimal calculations.
4. Every numerical finding opens the correct evidence and calculation.
5. Credits, total records, monthly-only data, incompatible periods, and mixed currencies are handled honestly.
6. No chart implies a finer time granularity than the data provides.
7. AI-disabled and AI-failure modes still deliver the full deterministic report.
8. Malformed, empty, oversized, and unsupported files produce useful errors.
9. A complete browser test covers sample → report → evidence → export; another covers upload → mapping → report.
10. Layout works at mobile and desktop sizes with keyboard navigation and readable print output.
11. The frontend type check and production build pass, and critical backend tests pass.
12. The deployed frontend and API pass real smoke tests, including multipart upload and refresh routing, if deployment access is available.

Test financial edge cases and real integration risks. Do not spend time writing low-value tests for static decorative components.

## 15. Hackathon presentation materials

Produce a factual README and short submission guide describing the user problem, implemented features, architecture, calculation method, AI's role, limitations, and how to try the app.

Include a 90-second demo outline: confusing CSV → report → evidence → next checks → technical explanation. Suggest a small user test measuring time to identify the largest cost contributor. Leave actual feedback and measurement fields empty until collected.

Provide a checklist for live AWS URL, selected category/lane, current rules review, and genuine coding-agent connection evidence. The builder must capture real screenshots/logs of the agent connected to AWS through the accepted workflow. Do not fabricate evidence, assume a particular connection method qualifies without checking, or publish secrets. Product Bedrock integration is separate from the coding-agent connection requirement.

Document all limitations openly: supported CSV formats, no live account visibility, no verified idle-resource detection, no automatic remediation, and AI availability.

## 16. Execution order and final handoff

Build in this order:

1. Repository inspection, setup, schema, deterministic parser/calculator, synthetic fixtures.
2. Complete sample journey with a polished responsive report.
3. Upload, mapping, validation, and evidence views.
4. Comparison, investigation checklist, and exports.
5. Optional Bedrock explanations with robust fallback.
6. AWS infrastructure, authorized deployment, critical tests, UI review, and documentation.

If time is short, protect the parser, accurate calculations, evidence, demo access, deployment, and submission evidence. Stretch features such as dark mode, daily spike detection, and advanced chart interactions come afterward. Do not start broad extra features while core paths are incomplete.

Start implementing now. Keep progress updates short and concrete. At handoff, report what works, what was tested, any remaining blockers, startup commands, real deployment URLs if verified, and the exact next action the builder must take. Do not describe unimplemented features as complete.

---

Reference documentation for the implementer (verify current details when building):

- Mangum/FastAPI integration: https://mangum.fastapiexpert.com/adapter/
- API Gateway HTTP API quotas: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html
- Lambda quotas: https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html
- Bedrock structured output support: https://docs.aws.amazon.com/bedrock/latest/userguide/structured-output.html
- Hackathon rules: https://builder.aws.com/build/hackathons/e83e84e5-4f4c-383b-bbe9-4a15ac195d55/zero-to-shipped?tab=rules
