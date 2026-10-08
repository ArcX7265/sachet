# Sachet implementation and verification

Recorded 30 September 2026. The delivered project is `C:/Users/ADARSH/Desktop/sachet`.

## Working local application

- React/TypeScript responsive web interface with a white, minimal design, case history and analyst/release roles.
- FastAPI with durable SQLite storage, owned sessions, revisions, corrections, idempotency and stale-result protection.
- English pattern baseline with exact evidence excerpts, explicit limitations, case-level alert updates and clarification.
- Optional Groq/Gemini adapters with schema/quotation validation, redaction, bounded requests, daily request limits and unavailable states. No automatic provider fallback.
- Browser-local screenshot OCR and QR modules with user review before submitting extracted text.
- Strict UPI-request preview bound to the exact request and current case assessment. Live handoff stays disabled.
- Real Razorpay test-order adapter, signed webhook verification, request replay handling and an honest uncertain-order state.
- Contribution consent with exact preview. Optional user-authored workflow descriptions enable review of unfamiliar wording; preview digests prevent sharing changed material without renewed review.
- Analyst candidate review, related-report leads using category/word overlap, declarative pattern proposals, synthetic regression evaluation, administrator activation and rollback.
- Local deletion/retention and withdrawal of contributions and dependent updates.
- Android Kotlin companion source for sharing, local OCR/QR, notification previews, consented uploads and assessment display.

## Verification performed

| Check | Result and scope |
| --- | --- |
| Python API/provider/evaluation tests | 52 automated tests passed, including narrative preview/consent, ownership, stale jobs, corrections, alert repetition/escalation, malformed signatures, forged callbacks, payment bindings, update gates and deletion |
| Web TypeScript | Passed |
| Web production bundle | Passed |
| Engineering replay | 40 AI-authored base journeys, 65 prefixes. Report in `evaluation/reports/engineering-results.md`; initial failing run retained separately |
| Browser interaction | Dashboard, synthetic case creation, added message, evidence-linked warning and contribution preview observed against the running API. Browser connection later became unavailable; final narrative and release behavior verified through API tests/build, not a completed second browser pass |
| Docker configuration | Compose configuration validates; containers were not built/run |
| Android | Portable parser/notification logic compiled and smoke-tested; XML and official Gradle wrapper checksums checked. Full Android build/device validation remains pending |

The Python suite emits a Starlette/httpx deprecation warning. It does not prevent the current tests from passing.

## Material limitations

The local detector is a limited deterministic baseline. Synthetic engineering success does not establish real-world accuracy, early interception, avoided losses, fairness, global novelty or superiority over direct conversation assessment. The application does not determine whether a scammer used AI. Similar reports are review leads, not verified campaigns.

Live Groq/Gemini quality and account quota validation require local API configuration. Private financial content is blocked from the free cloud route. The real Razorpay test-account flow requires test credentials and a reachable signed webhook. Unit tests use fake HTTP provider responses and cannot substitute for those account checks.

An Android SDK and device/emulator were not available, so no APK or Android lint/instrumentation result is claimed. Browser OCR/QR code is included, but image-quality and device coverage studies remain unmeasured.

The current API processes requests synchronously in a single local application. PostgreSQL migrations, durable distributed processing leases, production identity, TLS deployment, operational load testing and independent model/data evaluation from the full specification remain further deployment work. Demo role creation is local-only and must not be exposed publicly.

## Launch

Run `npm run setup` once, then `npm run dev` from the project directory. Open `http://127.0.0.1:5173`. `npm test`, `npm run evaluate` and `npm run build` reproduce the available checks. See the README, `.env.example`, and `docs/demo-runbook.md`.
