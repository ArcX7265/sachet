# Implementation decisions

## 29 September 2026 — Resume interrupted build

The original project directory contained `implementation.md`, `readme.md`, and a Python virtual environment. Partial files from interrupted agents were outside that repository. Work resumes against the agreed Statement 2 product scope and white, minimal visual design.

The implementation is being assembled in the chat's writable directory, then copied into the agreed `Desktop/sachet` repository. Staging is a build location; the delivered project remains `Desktop/sachet`.

### Local execution

The first running server uses durable SQLite so the full browser workflow can run without installing a database server. This replaces the plan's PostgreSQL requirement for the local prototype. PostgreSQL migration, distributed job leases and multi-worker quota enforcement remain deployment work; they must not be implied by a successful single-process demo.

### Detector availability

The app can exercise an inspectable local English rules baseline without credentials. It labels this engine and its limitations. Groq and Gemini adapters are optional cloud paths with explicit unavailable states; they require a configured key, selected compatible model and permitted data. No paid or Ollama fallback is added.

The local baseline is an engineering implementation, not evidence that AI-enabled scams can reliably be detected in the wild. The absence of an identified concern does not verify safety. The product detects concerning workflows; it does not infer whether the sender used AI.

### External integration gates

Android source and device/API wiring can be implemented without claiming device validation. A physical device or emulator and Android SDK are required for the acceptance gate. A payment request preview and a verified gateway test transaction are separate capabilities; gateway credentials are required for the latter. Independent payments made in other apps are outside the demonstrated coverage.

### Human authority

Contribution consent, analyst review, evaluation and release activation are distinct steps. Local demonstration roles are intentionally switchable for a demo on loopback. They are not an identity system for a public deployment. Production authentication and an operational privacy review remain release prerequisites.

### Evaluation

The included 40 journeys are synthetic engineering fixtures. Developers see them and may use them to correct implementation defects. The report preserves unresolved failures and cannot be presented as an independent academic benchmark.

## Team responsibilities

Actual human team names were not supplied. Assign integration, client/Android, detection/evaluation, discovery/release and submission owners before the finale, using the responsibilities in `implementation.md`.
