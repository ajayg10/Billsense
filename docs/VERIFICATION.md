# Verification status

## Completed in the build environment

- 29 backend/deployment tests passed, covering sample reconciliation, credits, labeled totals, Cost Explorer wide normalization, CUR optional fields, malformed data, mixed currencies, zero-prior comparison, duplicate warnings, upload inspection, AI-disabled behavior, malformed options, upload size limits, base64 multipart API Gateway/Mangum integration, generated rewrite validation, exact built-template deployment, and refusing changes to existing full hosting stacks.
- 5 real Chromium browser tests passed: sample report/evidence/filtering/checklist/CSV export; uploaded CSV and AI-disabled fallback; mobile layout/navigation; malformed cost error; hosting SPA responses returned to an API caller.
- React/TypeScript production build passed.
- Desktop and mobile screenshots captured and inspected. Included in this folder.
- Backend-only CloudFormation YAML parsed with three declared resources (HTTP API, Lambda and log group), and the Amplify appRoot/artifact path checks passed. This is offline validation, not an AWS deployment or full SAM semantic validation.

## Not yet verified externally

- AWS deployment, resource provisioning, public reachability, Amplify rewrite propagation, and cloud billing behavior: no configured AWS credentials in this workspace.
- Real Bedrock model invocation and output quality: no configured model access. AI-disabled fallback is tested.
- Acceptance of the coding agent's connection method by the hackathon organizers: builder must verify and capture genuine evidence.
- Formal accessibility audit and human user study.

## Known release constraints

- Browser Print / Save PDF uses print CSS and the user's browser dialog. It is not a server-generated PDF download. Export pagination/layout may vary by browser.
- Cost Explorer support is intentionally limited to the documented wide ISO-date subset. Convert other shapes to the supplied generic template.
- Service findings show the five largest positive contributors. Every service's rows remain available in the Evidence table.
- Reports clear on refresh; no login, server storage, account connection, or saved history.
- Two source files may have unequal or partial periods. The interface warns rather than assuming the comparison is normalized by duration.
- A vendor bundle-size warning is emitted during build; the build succeeds. Code splitting can be a later optimization.
- The dependency versions are locked to the environment used for this build. Re-evaluate dependency updates before an extended production launch.

## Design review captures

- `report-desktop.png`: report at a 1280-pixel desktop viewport.
- `report-mobile.png`: report at a 390-pixel mobile viewport, with no page-wide horizontal overflow.
