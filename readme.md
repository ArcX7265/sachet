# Sachet

**Financial scam awareness through conversation context and evidence.**

Sachet is a planned financial-safety product that follows how a suspicious interaction develops, connects requested actions to earlier claims, and explains what a user should verify before taking the next action. Reviewed contributions also help analysts identify unfamiliar workflow variations and evaluate improvements to detection.

The project is being developed for **RAKSHAM at IIT Delhi**, addressing **Statement 2: AI-driven scam pattern recognition**.

> **Current status:** Planning and specification. This repository contains the implementation plan and this README. Application code, runnable services, model benchmarks, and verified integrations have not yet been added. Capabilities described below are planned unless explicitly identified otherwise.

The detailed engineering specification is in [implementation.md](./implementation.md). It defines the contracts, acceptance gates, risk controls, evaluation requirements, and submission mapping that guide development.

## Contents

- [The problem](#the-problem)
- [Product approach](#product-approach)
- [Intended users](#intended-users)
- [Planned capabilities](#planned-capabilities)
- [User and analyst workflows](#user-and-analyst-workflows)
- [Phone and payment integration](#phone-and-payment-integration)
- [Architecture](#architecture)
- [Technology choices](#technology-choices)
- [Models and free API operation](#models-and-free-api-operation)
- [Data and evaluation](#data-and-evaluation)
- [Trust and user control](#trust-and-user-control)
- [Development setup](#development-setup)
- [Implementation roadmap](#implementation-roadmap)
- [Demonstration and submission](#demonstration-and-submission)
- [Contributing and repository hygiene](#contributing-and-repository-hygiene)
- [Limitations and open dependencies](#limitations-and-open-dependencies)
- [License and references](#license-and-references)

## The problem

A financial scam can develop across several messages, changing conditions, and requests for payment or access. An isolated message may not contain enough evidence to interpret the request. At the same time, urgency, fees, and identity checks can appear in legitimate interactions, making overly broad warnings disruptive.

Sachet focuses on these questions:

- What does the user want to achieve?
- What action are they being asked to take?
- How does that request relate to earlier statements?
- What evidence supports a concern, and what remains unknown?
- What useful response can reach the user before the next action?

The product must also handle changed wording, incomplete context, legitimate lookalikes, and new combinations of tactics. These are evaluation challenges rather than assumed capabilities.

## Product approach

The proposed approach has three connected parts:

1. **Understand the developing interaction.** Extract claims and requested actions, attach supporting evidence, and maintain revisable relationships between them.
2. **Help the user make a decision.** Explain a specific concern, ask a focused question when useful, and suggest an appropriate verification step. Avoid presenting uncertainty as verified safety.
3. **Improve through reviewed evidence.** Group eligible contributed reports, show candidate workflow variations to an analyst, and test proposed updates before activation.

The main hypothesis is that context and relationships can improve assessment beyond looking at individual messages. A separate experiment will determine whether Sachet's structured case history improves on a model reading the available conversation directly.

### Illustrative interaction

| Submitted evidence | Proposed interpretation |
| --- | --- |
| “Your withdrawal will be processed without any further payment.” | A claim about withdrawal conditions |
| “Send INR 2,000 as a verification deposit before we release it.” | A new payment condition that may conflict with the earlier claim |
| User confirms both messages concern the same withdrawal | Additional user-provided evidence linking the requests |

An assessment could explain the changed condition and show both excerpts. It must preserve the uncertainty about the sender's identity and the claimed funds. A fee or changed statement alone does not establish fraudulent intent.

This is a design example, not an output from an implemented detector.

## Intended users

| User | Intended task |
| --- | --- |
| Individual assessing a financial request | Share selected material, inspect a concern, correct an interpretation, and decide what to verify |
| Fraud analyst or reviewer | Inspect authorized contributions, assess candidate patterns, and propose detection improvements |
| Designated release reviewer | Review evaluation evidence and activate or roll back an approved detection bundle |

A participating payment provider is a possible integration stakeholder. A described API or sandbox demonstration does not establish a live partner relationship.

## Planned capabilities

| Capability | Intended behavior | Status |
| --- | --- | --- |
| Adaptive intake | Accept selected text/images and request missing context only when it matters | Planned |
| Evidence extraction | Record statements, amounts, requested actions, and source references | Planned |
| Case history | Connect related evidence, retain uncertainty, and support corrections | Planned |
| Concern assessment | Produce a specific, supported concern and an appropriate response | Planned; approach to be benchmarked |
| Clarification | Ask a reviewed question when its answer could change the assessment | Planned |
| Case-level alerts | Avoid repeated interruptions for unchanged evidence while recognizing material changes | Planned |
| Android sharing | Receive user-selected content through supported share actions | Planned; device validation required |
| Notification access | Process available events from user-selected sources with permission | Planned; coverage validation required |
| Payment-request checking | Relate QR/link details to the conversation before an intentional handoff | Planned |
| Gateway sandbox | Verify actual test-mode order and payment events | Planned; provider account required |
| Workflow discovery | Present candidate variations with supporting and conflicting evidence | Planned |
| Controlled updates | Evaluate, activate, and roll back versioned detection changes | Planned |

**Initial language:** English. Support for other languages is outside the first validated release.

## User and analyst workflows

### User assessment

1. Share or paste a conversation, screenshot, or financial request.
2. Review extracted information and correct important mistakes.
3. Receive an assessment with source evidence and limitations.
4. Answer a focused question if it could resolve a relevant ambiguity.
5. Choose a verification step or deliberately continue through a supported payment flow.
6. Add new evidence to the same case and see why the assessment changes.

The planned assessment separates processing status, evidence limitations, concern, and recommended response. An unavailable model must not produce an apparently successful assessment with no concerns.

### Analyst review and adaptation

1. Receive separately authorized, minimized contributions with provenance.
2. Identify duplicates and retrieve related interactions.
3. Inspect a candidate workflow, its closest reviewed pattern, and the proposed difference.
4. Review counterexamples and uncertain incident independence.
5. Reject the candidate, request more evidence, or accept it for evaluation.
6. Test a proposed change on regression cases and independent fresh examples.
7. Activate an approved version or retain the current one; support rollback.

A pattern unfamiliar to Sachet's library is not automatically a new global scam. Similarity also does not prove that incidents belong to one campaign.

## Phone and payment integration

The first version includes implementation of supported phone/payment paths, with actual coverage recorded in a capability matrix.

### Android companion

The Android application will complement the mobile-friendly web interface through:

- Explicit sharing of selected text and images.
- Local text recognition and QR parsing before any permitted cloud request.
- Optional notification access with source selection and a visible pause control.
- Local case updates, correction, and supported payment handoff.

Notification events can be incomplete, delayed, updated, or hidden. They do not guarantee access to outgoing messages or complete conversation history. Continuous call recording, universal screen monitoring, and iOS-wide access are outside the current design. See the official [sharing](https://developer.android.com/develop/ui/compose/sharing/receive?hl=en) and [notification-listener](https://developer.android.com/reference/android/service/notification/NotificationListenerService) documentation.

### Payment-request assessment

Sachet will parse a deliberately supplied payment QR or link, preserve the stated amount and recipient, and relate the request to the case. It will reject malformed or conflicting fields rather than silently choose a destination.

The reviewed request will be bound to its assessment. Changes to the recipient or amount require reassessment before a supported handoff. A model cannot authorize a payment or rewrite its destination.

### Gateway and payment status

The plan includes a real gateway test integration with server-side signature, order, amount, and status checks. Replayed or reordered callbacks must not corrupt payment state. An unverified application return is not confirmed payment success.

Live handoff remains disabled until the applicable provider prerequisites and device tests are satisfied. The integration covers requests handled through the supported flow; it does not intercept payments initiated independently in every banking or payment app. Refer to [Google Pay integration requirements](https://developers.google.com/pay/india/api/android/overview) and [Razorpay test integration](https://razorpay.com/docs/server-integration/python/test-app/).

## Architecture

The initial architecture uses one modular backend and a separate worker, with shared contracts for the web and Android clients.

```text
Mobile-friendly web             Android companion
  selected text/images            sharing / QR / permitted notifications
           |                                  |
           +------- minimized case events ----+
                              |
                    Authenticated ingestion
                              |
                  PostgreSQL case/event store
                              |
                      Durable job worker
                              |
        Evidence extraction -> Case history -> Concern assessment
                              |
               Explanation / clarification / warning
                              |
                   User interface and updates

Separate contribution choice
          |
Minimized reports -> Candidate grouping -> Analyst review
                                              |
                        Evaluation -> Versioned update / rejection
```

The payment adapter connects reviewed requests to supported handoff and verified gateway events. The model-provider adapter controls inference requests, data eligibility, usage, and failure handling.

### Core engineering rules

- Every derived statement or relationship refers to supporting evidence.
- Claims, inferred relationships, and verified external events retain different statuses.
- Source events carry identifiers; duplicate processing is safe.
- Assessments belong to a case revision and a processing-bundle version.
- An older job cannot overwrite a newer assessment.
- Corrections invalidate affected dependencies before recomputation.
- Shared source evidence is not counted repeatedly as independent confirmation.
- Pattern updates are reviewed and evaluated before activation.

Full schemas and the planned API surface are specified in [implementation.md](./implementation.md#4-core-contracts-and-persistence).

## Technology choices

These are planned choices. Dependency versions and exact model identifiers will be pinned after compatibility and quality checks.

| Layer | Planned technology |
| --- | --- |
| Web interface | React, TypeScript, Vite |
| Backend and contracts | Python, FastAPI, Pydantic |
| Persistence | PostgreSQL, SQLAlchemy, Alembic |
| Background jobs | Python worker using PostgreSQL job leases |
| Android | Kotlin, Jetpack Compose, Room, WorkManager |
| Android OCR/QR | ML Kit text recognition and barcode scanning |
| Web OCR/QR | Browser-local modules selected through an input-quality test |
| Model inference | Free-tier Groq and Gemini adapters |
| Report similarity | TF-IDF baseline; an evaluated licensed CPU sentence encoder if beneficial |
| Automated checks | pytest, web component tests, Playwright, Android instrumentation |
| Local service setup | Docker Compose once infrastructure files exist |

Local OCR and similarity processing do not require Ollama or a local generative model.

## Models and free API operation

**Paid model APIs and Ollama are outside the agreed implementation scope.** Groq and Gemini are candidates; the primary model has not yet been selected.

Selection will use the same English extraction and assessment cases, measuring evidence fidelity, false warnings, unresolved cases, latency, and token use. A fallback model must pass the relevant evaluation and be permitted for the data it would receive.

The provider layer will:

- Enforce request/token budgets shared across interactive and background work.
- Cache unchanged results within the correct user/case scope.
- Use bounded retries and account for repair attempts.
- Respect provider rate limits without rotating accounts or keys to bypass them.
- Prefer new evidence plus required context over unnecessary repeated full-history submissions.
- Return an explicit unavailable state when approved options are exhausted.

Exact free quotas must be read from the accounts used for the project. Prototype throughput must be measured within those limits. A zero model-API budget does not establish unlimited capacity or guarantee free hosting. See [Groq limits](https://console.groq.com/docs/rate-limits) and [Gemini limits](https://ai.google.dev/gemini-api/docs/rate-limits).

Real private financial conversations are disabled for cloud processing until a documented data-handling route is configured and consent is captured. Provider fallback must not silently change that policy. Redaction alone does not prove anonymity. Relevant controls and terms are documented by [Groq](https://console.groq.com/docs/your-data) and [Gemini](https://ai.google.dev/gemini-api/terms).

## Data and evaluation

### Data strategy

Begin with a reviewed engineering seed of 40–60 independent journeys to expose design failures. Expand evaluation using accessed, permitted resources and independently reviewed examples. This seed size is not evidence of reliable real-world accuracy.

Candidate resources include:

| Resource | Intended role | Constraint |
| --- | --- | --- |
| [ICFD-31k](https://github.com/SPELLAILab/ICFD-31k) | English conversational and streaming experiments | Synthetic; confirm full access and terms; remove verdicts, rationales, and generation metadata from inference inputs |
| [PsyScam](https://github.com/KiteFlyKid/PsyScam) | Inform annotation of psychological tactics | Public release is partial; review access and reuse conditions |
| Independently reviewed project cases | Legitimate lookalikes, ambiguity, corrections, unfamiliar workflows | Record authorship/provenance and distinguish fabricated outcomes from observable evidence |

ICFD data conditions are separate from its code license. Resource access or research suitability must not be presented as unrestricted deployment permission. See its [dataset card](https://github.com/SPELLAILab/ICFD-31k/blob/main/DATASET_CARD.md) and [data terms](https://github.com/SPELLAILab/ICFD-31k/blob/main/LICENSE-DATA.md).

### Evaluation discipline

- Separate development, validation, regression, and untouched test sets.
- Keep all prefixes, translations, paraphrases, images, and known related templates with their base journey.
- Evaluate only the evidence available at the current point in a conversation.
- Include consistent scams, legitimate changes of terms, quoted requests, uncertain chronology, and missing context.
- Hold out workflow families and independently test the discovery stream.
- Record reviewer disagreement rather than force false precision about the first justified warning.
- Mark a previously untouched set as development material if its results influence changes.

### Comparisons

Compare a small ruleset, latest-message model assessment, direct available-conversation assessment, and the structured Sachet pipeline. Use comparable inputs and validation-selected operating points. Report trade-offs when equivalent operating points cannot be achieved.

### Metrics

| Area | What to measure |
| --- | --- |
| Detection | Supported concern detection and timing relative to a known action |
| False warnings | Legitimate journeys receiving an unwarranted warning |
| Coverage | Useful completed assessments, unresolved cases, and unavailable cases separately |
| Friction | Questions, unnecessary repeat alerts, abandonment, and submission effort |
| Evidence quality | Speaker/amount/action extraction, source accuracy, and faithful explanations |
| Discovery | Useful candidates, incorrect merges, missed patterns, and review effort |
| Updates | Changed decisions on independent fresh cases and regression cases |
| Operations | Queue delay, end-to-end latency, token usage, failures, and quota exhaustion |

Report independent case counts, source limitations, and uncertainty. No achieved accuracy, loss-prevention result, or model superiority is currently claimed.

## Trust and user control

Trust controls are part of the planned implementation and evaluation, not badges of readiness.

### Data minimization and consent

Collect only selected material and permitted source events needed for the current task. Private checking and contribution to analyst discovery require distinct choices. Avoid collecting unrelated contacts, location history, biometrics, complete phone history, or continuous call audio.

Credentials such as OTPs, PINs, passwords, and card CVVs must be excluded from cloud payloads. The fact that someone requested a credential may still be relevant evidence.

### When the assessment is wrong

- **False positive:** Explain the concern, allow targeted correction, and preserve an appropriate verification or continuation path. A weak signal cannot automatically justify blocking a transaction or making a public accusation.
- **False negative:** State coverage limits, allow later evidence and a missed-concern report, and offer separately verified guidance when the user has already acted.
- **Processing failure:** Show unavailable or partial status. Missing model output cannot be interpreted as no risk.

### Authority and misuse resistance

Users control their own actions. Analysts review authorized contributions. Designated reviewers control evaluated releases. A model cannot transfer money, enter credentials, publish accusations, submit external reports, or deploy generated rules.

Treat messages, images, QR codes, reports, and model responses as untrusted input. Planned checks cover prompt injection, duplicate/manipulated reports, unauthorized evidence access, malformed uploads, and forged payment callbacks.

### Bias and comprehension

Test English spelling, informal phrasing, OCR quality, verbosity, and reviewed Indian-English variations. Examine unjustified sensitivity to superficial name or wording changes. Report sample limitations and test whether users can explain both the concern and the uncertainty.

### Retention and deletion

Proposed defaults are seven days for private cases, thirty days for opted-in minimized reports, and seven days for content-free operational logs. Raw screenshots remain client-local during review where possible; optional backend copies are deleted after processing or within 24 hours.

These defaults are not implemented yet and are not statutory-retention claims. Deletion must cover derived records, caches, embeddings, and contribution memberships, with backup/provider limitations documented. See [the full privacy design](./implementation.md#6-security-retention-and-user-control).

## Development setup

### What exists today

```text
sachet/
  implementation.md       # Detailed engineering and submission specification
  readme.md               # Project overview and contributor orientation
```

There is currently no runnable application, dependency manifest, Compose file, APK, or evaluation runner. Installation and startup commands will be added when those artifacts exist and have been tested. No API key is needed to read the current documents.

### Planned prerequisites

- Node.js and the selected package manager for the web client.
- Python and the selected environment/package tooling for the backend.
- PostgreSQL, or the documented container setup once added.
- Android Studio and a physical Android device for integration coverage tests.
- At least one eligible free Groq or Gemini account.
- A gateway test account and keys for the sandbox payment milestone.

Exact versions, model identifiers, and account capabilities are implementation checkpoints.

### Configuration to introduce with the code

| Category | Configuration to document |
| --- | --- |
| Providers | API keys, approved model IDs, quotas, timeouts, retry limits, and eligible data classes |
| Backend | Database connection, session settings, worker scheduling, and active processing bundle |
| Clients | Backend endpoint, device pairing/session configuration, and source permissions |
| Payments | Test-mode keys, callback verification, and a disabled-by-default live-handoff setting |
| Data handling | Retention windows, artifact storage, contribution controls, and logging policy |

These are configuration categories, not currently supported environment variables. Publish a tested `.env.example` alongside the code. Keep real credentials on the backend and outside version control.

### Target repository structure

The following directories are planned and have not yet been created:

```text
sachet/
  apps/
    web/                  # User interface and analyst routes
    android/              # Sharing, local OCR/QR, notifications, handoff
  services/
    api/                  # Auth, ingestion, case engine, payments, discovery
    worker/               # Durable processing and evaluation jobs
  contracts/              # Versioned schemas and generated client types
  policies/               # Patterns, questions, response templates
  evaluation/             # Manifests, annotations, baselines, runners, reports
  tests/                  # Unit, integration, end-to-end, adversarial checks
  infra/                  # Repeatable service setup
  docs/                   # Capability, data, model, decision, and demo records
  .env.example
  implementation.md
  readme.md
```

## Implementation roadmap

| Milestone | Deliverable | Current status |
| --- | --- | --- |
| M0 | Access probes, capability matrix, shared contracts, provider/data policies | Pending |
| M1 | Audited loader, reviewed cases, baseline comparison | Pending |
| M2 | Working case engine with corrections, revisions, and assessment | Pending |
| M3 | Responsive UI and tested Android sharing/notification paths | Pending |
| M4 | Payment-request binding, verified gateway test events, handoff readiness | Pending |
| M5 | Contribution controls, candidate discovery, analyst review | Pending |
| M6 | Evaluated activation, rejected updates, rollback | Pending |
| M7 | Full evaluation, usability findings, reproducible deployment, demo runbook | Pending |

The implementation plan defines ten detailed steps beneath these milestones. There is no artificial eight-hour development constraint. The submission must still explain a credible 48-hour finale execution plan, using only preparation permitted by the organizers.

Before accepting the complete system, establish:

1. **Detection value:** A fair comparison supports the selected architecture or leads to simplification.
2. **User value:** People understand the evidence and can identify an appropriate next action.
3. **Adaptation value:** Reviewed updates improve fresh-case behavior without unacceptable regressions.
4. **Integration value:** Actual tested phone paths and verified sandbox events reach the common case engine.

## Demonstration and submission

The proposed demonstration follows one complete interaction and includes:

- A supported concern with visible source evidence.
- A difficult legitimate lookalike.
- An incomplete case and a useful clarification.
- A corrected interpretation and transparent reassessment.
- A new event handled without unnecessary repeated alerts.
- Contextual payment checking and an actual gateway test event.
- A candidate update assessed on fresh cases, including a rejection or rollback.
- Honest behavior during API quota exhaustion or connectivity failure.

Label synthetic content, replayed streams, test payments, and measured results accurately. A stored replay cannot count as a successful live inference run.

### Required submission format

The supplied organizer guidance requires **one clear PDF** containing a pitch of at most **10 slides** and an architectural overview of at most **3 pages or slides**. Confirm whether the architecture must be separate or embedded before final export. Preserve required attribution and disclosures within the permitted format.

The submission must make these answers easy to find:

| Required area | What the reviewer should understand |
| --- | --- |
| Problem | Primary user, harmful moment, and exact threat pattern |
| Product | The path from input to assessment, action, verification, or evidence record |
| Architecture | Components, data boundaries, outputs, and safeguards |
| Proof plan | Assumptions, validation, and the 48-hour demonstration |
| Trust | Necessary data, consent, error handling, authority, explanation, bias, and misuse resistance |

The detailed pitch/architecture mapping and weighted rubric are maintained in [implementation.md](./implementation.md#13-mandatory-submission-content-trust-and-final-checks). A pitch deck and PDF have not yet been generated.

## Contributing and repository hygiene

Start with the implementation plan and agree on the contract for the component being changed. Record important decisions and evidence limitations instead of silently expanding scope.

For each implementation change:

1. Identify the user behavior and milestone it serves.
2. Preserve source lineage, ownership checks, revision handling, and provider/data policy.
3. Add meaningful tests for the changed behavior and concrete failure paths.
4. Record evaluation impact when detection, extraction, grouping, or response policy changes.
5. Update setup instructions and capability status when a feature becomes runnable and verified.

Do not commit API keys, gateway secrets, private uploads, identifiable reports, restricted dataset contents, or sensitive inference traces. Small permitted synthetic fixtures and dataset manifests can be versioned.

Do not use fabricated metrics, speculative partner access, or a successful prepared demo as evidence of general accuracy. Report security issues privately through a maintainer-provided channel once one is established; avoid publishing sensitive evidence in repository issues.

## Limitations and open dependencies

- Model quality and the benefit of structured case tracking remain unmeasured.
- Private-cloud data processing requires a configured, documented route and user consent.
- Notification visibility and timing vary by device and source application.
- User sharing depends on the user providing relevant material before the next action.
- Payment integration is limited to supported flows and verified provider access.
- Discovery requires useful contributions and cannot infer prevalence from raw report counts alone.
- Dataset availability, licenses, label quality, and source overlap require verification.
- Free API limits constrain throughput; no paid or Ollama fallback is assumed.
- Hosting, exact package/model versions, gateway account capabilities, and quantitative release thresholds remain to be selected or measured.

Routine technical choices will be resolved through implementation and evaluation. Account access, unsupported integrations, or material product changes require a recorded decision.

## License and references

No repository license has been selected or included yet. Do not assume a license for Sachet from the licenses of its dependencies or research resources. Record third-party notices and permitted dataset/model use before distribution.

Primary project documentation:

- [Detailed implementation plan](./implementation.md)

External technical and research references are linked next to the relevant discussion above. Recheck provider terms, platform behavior, and account limits when implementing each integration. Documentation describes a supported interface; the project's capability matrix must record what was actually tested.
