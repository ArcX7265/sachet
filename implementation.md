# Sachet — Detailed Implementation Plan

**Document date:** 29 September 2026  
**Status:** Build specification; implementation and validation are pending.  
**Project:** IIT Delhi / RAKSHAM, Statement 2 — AI-driven scam pattern recognition.  
**Initial language:** English.  
**Model budget:** Free-tier Groq and/or Gemini APIs only. No Ollama dependency.  
**Delivery:** Mobile-friendly web application, analyst dashboard, and Android companion with first-version phone/payment integration.

## 1. Product objective and agreed constraints

Sachet assesses financial interactions as evidence becomes available. It connects requests to earlier claims, explains supported concerns, and helps the user decide what to verify before the next risky action. Separately, contributed reports support analyst review of unfamiliar workflow variations and tested improvements to detection.

Three capabilities define the product:

1. Evidence-linked understanding of a developing interaction.
2. Proportionate assessments and alerts, including useful clarification and control of repetition.
3. Reviewed discovery and validation of workflow variations across reports.

The team has the required development skills and ample development time. Work is ordered by dependencies and validation gates rather than an assumed eight-hour deadline. Published event submission requirements must be rechecked when preparing the final submission.

### Evaluation rubric and evidence obligations

The supplied judging rubric totals 100 points. The following mapping defines what the implementation and submission must demonstrate; it is not an estimate of the score Sachet will receive.

| Criterion | Weight | Sachet contribution | Required evidence | Main scoring risk |
| --- | ---: | --- | --- | --- |
| Problem fit & user understanding | 20 | Connect developing financial requests to the user's intended outcome and decision point | One observed user journey, input/coverage map, legitimate comparison, and short usability findings | A generic screenshot checker with no credible route to help before the action |
| Technical architecture & detection logic | 20 | Source-linked extraction, revisable case state, concern assessment, and controlled updates | Data-flow diagram, inspectable decision trace, baseline comparison, correction and failure demonstrations | Many components without evidence that they improve decisions |
| Solution value & differentiation | 15 | Contextual workflow assessment, proportionate intervention, and reviewed variations | Tests of the contribution hypotheses below, plus an accurate comparison with existing approaches | Familiar features described as novel; similarity clustering presented as proof of emergence |
| Feasibility & finale execution plan | 15 | Milestones, clear ownership, integration checkpoints, and bounded dependencies | Finale schedule, deliverable owners, tested setup, and contingency runbook | Promising every platform capability without verified access or a finishable execution plan |
| Safety, privacy & responsible AI | 15 | Evidence limitations, correction, contribution controls, data routing, and rollback | Working consent/deletion/provider-routing tests; legitimate-case and rejected-update examples | Policies written in the document but absent from the running product |
| Adoption, integration & scale | 10 | Android sharing, tested notification coverage, contextual payment checking, and an adapter API | Device/account capability matrix, submission-friction findings, quota/load measurements, and deployment assumptions | Assuming universal phone access, user adoption, or unlimited free inference capacity |
| Communication quality | 5 | One clear financial journey explaining the system and its limits | Self-contained presentation, readable evidence, visible simulated/test labels, and traceable results | Pitch complexity obscuring the user problem and actual contribution |

The first two criteria account for 40 points. Give the user decision and detection evidence substantial presentation space. Organize the pitch around what the user encounters, what Sachet observes, how its decision follows, and what the evaluation establishes.

Maintain a submission evidence register in `docs/rubric-evidence.md` with criterion, claim, artifact/test-run reference, owner, status, limitation, and intended slide. Status must distinguish `planned`, `implemented`, `tested`, and `measured`. A diagram proves a design exists; it does not prove accuracy, adoption, or successful integration.

### Intervention points and coverage contract

For every demonstration, identify the next action, the evidence available before that action, and the channel through which Sachet receives it.

| Entry point | Available evidence | When Sachet can help | Explicit limitation |
| --- | --- | --- | --- |
| User shares conversation material | Only the selected text/images and subsequent answers | After sharing, before the user's next action if analysis completes in time | Requires user participation; omitted history remains unknown |
| Android notification event | Fields actually exposed to the approved listener | When a relevant event arrives and processing completes | Inbound-only or truncated context, hidden content, device delays, and missing outgoing messages can limit assessment |
| User supplies payment QR/link | Parsed request details plus the associated case | Before an intentional handoff initiated through Sachet | Request details do not establish recipient identity; independent payments elsewhere are outside this handoff |
| Integrated merchant test checkout | Server-created order, supplied case context, and verified test events | Before checkout handoff; later events update status | Covers the integrated test flow; completion events cannot establish prevention of a payment already made |
| Continuing case update | New material with its provenance and available chronology | Before a subsequent requested action | A previous loss may already have occurred; describe preventing an additional action separately |

Record evidence-available time, event receipt, assessment completion, alert display, and action time when genuinely observable. Report unknown times as unknown. Replayed timestamps support a simulation result, not a measured real-world lead time. A timely-intervention claim requires that Sachet actually had the relevant evidence and delivered its response before the action.

### Testable contribution hypotheses

The proposed primary claim is: **Connecting the sequence and relationships of requests helps identify concerning workflows earlier while keeping unnecessary warnings controlled.** This is a hypothesis until measured.

| Hypothesis | Comparison | Evidence needed before claiming improvement |
| --- | --- | --- |
| Conversation context helps interpret a request | Latest-message assessment versus available-conversation assessment | Paired outcomes on the same independent journeys, including legitimate lookalikes |
| Sachet's structured state adds value | Direct available-conversation assessment versus structured case assessment | Improved timing, decision quality, revision consistency, or explanation fidelity with latency/cost reported |
| Selective clarification and case-level alerts reduce friction | The same detector with the intervention policy enabled and disabled | Questions, unnecessary repeated alerts, false warnings, and missed escalations reported together |
| Reviewed discoveries improve subsequent protection | Current bundle versus candidate bundle | Fresh examples independent of the discovery reports, including legitimate comparisons and workflow variation |

For earlier-detection comparisons, select thresholds or policy operating points using validation data and compare at a similar false-warning rate where feasible. Alternatively, compare false warnings at similar detection coverage. Report the trade-off if comparable operating points cannot be achieved. Do not claim simultaneous improvements from selectively chosen examples.

Broad capabilities such as conversational assessment, screenshots, or warnings are not an industry-first claim. The proposed contribution is the demonstrated combination and its measured behavior. A candidate unfamiliar to Sachet's library is not automatically a globally new scam or a growing real-world campaign.

### First-version commitments

| Area | Implementation commitment | Boundary to preserve |
| --- | --- | --- |
| User interface | Responsive web application for submission, evidence inspection, correction, and case updates | A browser alone does not provide ongoing access to other phone applications |
| Android companion | Share receiver, on-device image/QR processing, optional notification access, case updates, and payment handoff integration | Coverage depends on permissions, OS behavior, and what the source app exposes |
| Payments | User-supplied payment-request parsing, contextual assessment, supported handoff, and an actual gateway sandbox adapter | No claim of intercepting every transaction initiated independently in another app |
| Language | English interfaces, prompts, data slices, and evaluation | Other languages receive a support limitation; no untested multilingual claim |
| Inference | Interchangeable, evaluated Groq/Gemini adapters using free quotas | No paid fallback, quota circumvention, or untested model substitution |
| Discovery | Candidate grouping, evidence review, and versioned pattern proposals | Similarity alone does not establish fraud, campaign identity, or real-world emergence |
| Learning | Tested pattern/policy updates with review and rollback | User reports and dismissals do not automatically become training labels |

The initial phone target is Android. Continuous call-audio capture, iOS-wide monitoring, accessibility-based screen scraping, and autonomous operation of third-party payment apps are outside this implementation contract. Adding any of these requires a separate supported-access design.

### What counts as success

- A user can submit relevant material, understand a specific concern and its limits, and correct an interpretation.
- New evidence updates the same case without duplicate alerts or stale results overwriting newer assessments.
- The structured approach is compared fairly with direct assessment of the same available conversation.
- Discovery surfaces useful candidate variations with traceable evidence and manageable review effort.
- A reviewed update improves fresh-case behavior without unacceptable regressions.
- Phone and payment demonstrations clearly distinguish real platform integration, gateway test transactions, and replayed events.

No detection accuracy, avoided-loss figure, or improvement claim is established by this document.

## 2. System architecture

```text
Web submission                    Android companion
  text / screenshots                share / QR / selected notifications
          |                                    |
          +------ local extraction / minimization ------+
                                                       |
                                         Authenticated ingestion API
                                                       |
                                        Revisioned case event store
                                                       |
                                       Durable processing job queue
                                                       |
                            Extract statements and source evidence
                                                       |
                              Resolve references / update relations
                                                       |
                              Assess concerns and evidence limitations
                                                       |
                              Select explanation / question / warning
                                                       |
                                 Web result / Android result or alert

Separately authorized contribution
          |
Minimized report -> duplicate checks -> candidate grouping -> analyst review
                                                               |
                               Proposed update -> evaluation -> versioned release
```

### Proposed stack

Use one backend with separate modules and one worker process initially. Pin tested dependency versions in lockfiles during project setup; this document does not prescribe unverified version numbers.

| Component | Choice | Reason |
| --- | --- | --- |
| Web UI | React, TypeScript, Vite | Shared user and analyst interfaces with typed API contracts |
| Backend | Python, FastAPI, Pydantic | Typed requests, schema validation, evaluation integration |
| Database | PostgreSQL, SQLAlchemy, Alembic | Transactions, revision control, migrations, durable job records |
| Worker | Python worker with PostgreSQL job leases | Avoid introducing a second queue service before demand justifies it |
| Android | Kotlin, Jetpack Compose, Room, WorkManager | Native sharing, local state, and recoverable work scheduling |
| Android OCR/QR | ML Kit text recognition and barcode scanning | Process selected images on the device before cloud submission |
| Web OCR/QR | Browser-local OCR/QR modules selected after an input-quality spike | Limit raw image transfer; preserve text-to-image references |
| Embeddings | A small licensed sentence encoder on CPU; benchmark against TF-IDF | Avoid consuming generation quotas for report similarity |
| Generation | Groq and Gemini behind one internal adapter | Provider replacement without rewriting the pipeline |
| Tests | pytest, web component tests, Playwright, Android instrumentation | Cover decision correctness and integration failure paths |
| Local deployment | Docker Compose for API, worker, and PostgreSQL | Repeatable development and demonstration setup |

Local OCR, deterministic processing, and a small embedding encoder do not require Ollama or a local generative model. Check the selected encoder's license, artifact availability, memory use, and startup time before adoption. Start discovery with TF-IDF if the embedding dependency has not passed that check.

Sources: [FastAPI](https://fastapi.tiangolo.com/), [Sentence Transformers](https://www.sbert.net/), [ML Kit text recognition](https://developers.google.com/ml-kit/vision/text-recognition/v2/android), [Android WorkManager](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started).

## 3. Ten implementation steps

### Step 1 — Freeze the product contract and prove integration access

**Purpose:** Resolve input availability before building features around assumed access.

**Work**

1. Document the primary user: a person assessing a financial request before the next action. Document the secondary user: an analyst reviewing contributed reports.
2. Implement small technical probes for Android sharing, notification access, QR parsing, and the payment sandbox.
3. Record the actual target devices, OS versions, source applications, available notification fields, and background behavior.
4. Establish a provider account configuration that stays on free quotas. Obtain credentials through local environment configuration; never collect API keys in chat or embed them in clients.
5. Select several development workflows, such as investment withdrawal conditions, support impersonation involving access requests, and advance-fee requests. Include legitimate comparisons. Reserve other workflows for testing.
6. Create a capability matrix with states `verified`, `partial`, `unavailable`, and `requires_external_access`.

**Deliverables:** Product contract, capability matrix, device test notes, source-access register, threat-case taxonomy, and integration probe results.

**Acceptance gate:** At least one supported Android sharing path and one real gateway test integration work. Notification and live payment capabilities have observed evidence or an explicit access dependency. Replay is visibly labelled and cannot substitute silently for a failed real integration.

### Step 2 — Implement adaptive intake and phone/payment adapters

**Purpose:** Bring evidence into one case format while retaining provenance and uncertainty.

**Web intake**

- Accept pasted text and selected PNG/JPEG/WebP screenshots. Validate actual file content, dimensions, decompression limits, count, and size; reject unsupported types.
- Run local OCR where feasible, show extracted text, and retain bounding boxes and image references on the client. User-edited OCR remains marked as a correction.
- Distinguish desired outcome, requested action, and the sender's claimed justification. Extract these when supported instead of requiring a long form.
- Let the user select an existing case or create a new one. Do not merge unrelated cases based only on similar names or amounts.

**Android sharing and notifications**

- Register explicit share targets for supported text/image MIME types; preview content before submission.
- Use temporary URI access correctly and copy only what is required into private application storage.
- Make notification access optional, explained, and limited by an application allowlist and visible pause control.
- Start with controlled test notifications. For real-content mode, require the provider/data-handling gate described below.
- Preserve notification update/removal metadata. Notification updates are not necessarily new messages; notifications may omit outgoing messages or conversation history.
- Ignore Sachet's own notifications to prevent recursive ingestion. Do not treat app package identity as proof of the sender's identity.
- Use an encrypted/authenticated local storage design appropriate to the stored content. Store credentials using Android-protected storage.
- Schedule recoverable upload/processing work, and record delays. WorkManager and notification access do not guarantee immediate execution under every device condition.

Android supports receiving shared content and permission-based notification listening. Actual available content must be tested, including sensitive-content restrictions. See [sharing](https://developer.android.com/develop/ui/compose/sharing/receive?hl=en), [notification listener](https://developer.android.com/reference/android/service/notification/NotificationListenerService), and [Android 15 changes](https://developer.android.com/about/versions/15/behavior-changes-all).

**Payment requests and handoff**

- Parse user-selected QR/link data as untrusted structured input. Accept explicitly supported schemes; never automatically open arbitrary embedded URLs.
- Preserve amount, currency, stated payee, and purpose exactly as observed. Flag duplicate/conflicting query parameters, missing fields, and invalid values.
- A QR's display name is a claim. A valid URI is not evidence that its recipient is trustworthy.
- Bind the reviewed payment details to a request digest. If the recipient, amount, or purpose changes, invalidate the previous assessment before handoff.
- Require a deliberate user action to launch a supported payment flow. The model cannot choose or rewrite the destination.
- Implement the gateway adapter using test keys and a real provider test account. Verify server-side callbacks/signatures and match order, amount, currency, and status. Duplicate and reordered callbacks must be safe.
- Implement live-handoff support behind a disabled-by-default feature flag, enabling it only after applicable merchant/provider prerequisites and actual device testing are satisfied. Never mix test and live credentials or databases.
- An unverified app return is `status_unverified`, not payment success. Keep pending, authorized, captured/succeeded, failed, cancelled, and unknown states distinct as supported by the provider.
- UI language must make clear when a completed payment cannot be stopped. Gateway sandbox support for a particular payment method must be verified rather than assumed.

Google documents UPI intent integration and payment verification requirements; merchant prerequisites apply. Razorpay documents an actual test-mode integration. See [Google Pay overview](https://developers.google.com/pay/india/api/android/overview), [UPI integration](https://developers.google.com/pay/india/api/android/in-app-payments), and [gateway test integration](https://razorpay.com/docs/server-integration/python/test-app/).

**Acceptance gate:** Shared text/images and tested phone events become traceable case events. Duplicated submissions are safe. A gateway test transaction produces a verified backend event. A changed payment request cannot reuse an assessment of different details.

### Step 3 — Build the dataset, annotations, and evaluation harness

**Purpose:** Establish independent evidence for detection and user-response quality.

**Dataset construction**

1. Begin with 40–60 independently authored or selected base journeys for debugging. This is an engineering seed, not the final performance benchmark.
2. Expand using accessed, licensed research resources and independently reviewed cases. Audit sample quality before bulk import.
3. Include scams, legitimate lookalikes, unresolved interactions, consistent scams, legitimate changes of terms, incomplete histories, quoted threats, and extraction errors.
4. Record provenance, generation method where relevant, source family, template lineage, language, and permission/licensing status.
5. Separate the scenario's outcome from the concern justified by each observable conversation prefix.
6. Annotate supporting passages, requested actions, evidence limitations, and acceptable response ranges. Have two reviewers independently annotate a subset; retain disagreement and adjudication records.

**Resource handling**

- ICFD-31k is a candidate for English conversational and streaming experiments. It is synthetic and contains answer-bearing annotations alongside transcripts. Its data loader must allowlist observable transcript fields and exclude verdicts, final rationales, scenario/persona metadata, and other labels from inference inputs. Audit the loader with inspected examples. [Dataset card](https://github.com/SPELLAILab/ICFD-31k/blob/main/DATASET_CARD.md)
- Verify full corpus access before making it a training dependency. Its repository documents a separate hosted release. [Access instructions](https://github.com/SPELLAILab/ICFD-31k/blob/main/DATA_ACCESS.md)
- Record its defensive-use and commercial-use conditions in the resource register. [Data terms](https://github.com/SPELLAILab/ICFD-31k/blob/main/LICENSE-DATA.md)
- PsyScam can inform psychological-tactic annotation, subject to access and reuse review. Its public repository provides only part of the dataset. [Repository](https://github.com/KiteFlyKid/PsyScam)
- Reports are not automatically raw dialogues. Synthetic timestamps do not establish real campaign timing. English-only evaluation must use an audited English slice rather than assume every resource matches the release language.

**Splits and experiments**

- Split base journeys before augmentation. Keep every prefix, image variant, paraphrase, translation, and known related template with its parent split.
- Maintain development, validation, regression, and untouched test sets with distinct purposes.
- Hold out workflow families for a separate unfamiliar-workflow experiment. Document remaining template/source overlap.
- Reserve a separate report-stream experiment for discovery; distinguish authentic from simulated collection times.
- After a test set influences a design change, label it as development/regression material and reserve fresh cases for subsequent independent assessment.

**Baselines**

1. Small deterministic ruleset.
2. Model assessment of the latest available message.
3. Model assessment of the available conversation.
4. Sachet with structured case history.
5. Optional lightweight trained classifier if sufficient permitted data and compute exist.

Use identical observable evidence at each evaluation point. Model identity, prompts, sampling settings, token budgets, and test manifests must be recorded.

**Acceptance gate:** A repeatable evaluation command runs the baselines; inputs contain no answer fields or later conversation content; reviewed annotations and split manifests exist. All reported counts distinguish independent journeys from derived examples.

The baseline report must explicitly address the contribution hypotheses in Section 1. Freeze the comparison protocol and validation-selected operating points before inspecting untouched test outcomes. If the structured pipeline does not outperform direct assessment on the intended benefit, simplify the implementation and describe any remaining traceability benefit accurately.

### Step 4 — Extract statements with evidence references

**Purpose:** Convert varied language into inspectable claims without prematurely deciding fraud.

**Work**

- Define a versioned schema for participants, claimed affiliation, promised outcomes, requested actions, amounts, conditions, deadlines, and unresolved references.
- Preserve assertion mode: direct request, quotation, reported speech, negation, hypothetical, or unclear.
- Allow unfamiliar actions to remain unclassified with a source-linked description. Do not force them into a familiar scam category.
- Request structured output from the selected provider. Treat all source text as data; extraction has no browsing, shell, payment, or messaging tools.
- Validate JSON, allowed fields/enums, referenced sources, text spans, amount formats, and maximum output size.
- Exact quotation matching verifies existence, not semantic correctness. Evaluate the interpretation against reviewed annotations.
- Prefer one bounded extraction call per new material bundle. Allow at most one bounded repair attempt for malformed output; otherwise return an explicit extraction failure.
- A model's self-reported confidence is not a calibrated probability. Record concrete limitations such as uncertain speaker, unreadable amount, or missing reference.
- Redaction occurs before model submission. Preserve a local/source mapping so placeholders can be related to displayed evidence without sending unnecessary identifiers.

**Critical examples:** `send your OTP`, `never send your OTP`, and `they asked me to send my OTP` must produce different assertion roles. Similar checks apply to quoted payment instructions and conditional statements.

**Acceptance gate:** Extraction quality is reported by critical field and assertion mode. Unsupported fields cannot pass schema validation as established facts. Provider errors and content refusals remain failures or limitations rather than benign classifications.

### Step 5 — Maintain a revisioned, revisable case history

**Purpose:** Connect evidence across events while allowing corrections and partial chronology.

**Work**

- Maintain append-only source events plus derived statements, relations, and assessments. User-visible current state is a projection of this history.
- Use separate `received_at`, optional `observed_at`, and ordering-confidence fields. User ordering is recorded as user input.
- Start with evidence-supported relations: `refers_to`, `conditions_on`, `supersedes`, `possibly_conflicts_with`, and `same_transaction_candidate`.
- A contradiction requires evidence that statements concern the same object, scope, and transaction. It remains an observation for Step 6 rather than a fraud verdict.
- Keep explicit and inferred relations distinct. Store supporting and conflicting evidence plus unresolved alternatives.
- Deduplicate exact replays using idempotency keys. Use overlap/metadata checks for screenshot and notification duplicates; do not merge uncertain near-duplicates silently.
- Corrections create new events and invalidate dependent statements, relations, and assessments. Recompute from the earliest affected dependency, falling back to a full case rebuild if required.
- Include source statements when constructing model context; summaries are derived aids. Mark omitted context rather than silently truncating important evidence.

**Concurrency invariant:** Each processing job reads a case revision and processing bundle. It may publish as current only if the revision is still current. Otherwise its result is retained as historical/stale and a newer job remains responsible for the current view.

**Acceptance gate:** Replays, duplicate events, out-of-order input, corrections, and simultaneous jobs produce consistent state. An older job cannot overwrite a newer assessment. A correction removes or updates dependent concerns.

### Step 6 — Assess concerns and select a response

**Purpose:** Turn supported evidence into a proportionate decision with inspectable limits.

**Assessment record**

- Requested action and relevant decision point.
- Specific concern hypotheses, with supporting and opposing evidence.
- Missing or ambiguous information.
- Evidence dependencies shared across signals.
- Response recommendation and the processing/policy version.

**Decision design**

- Compare the baseline approaches before selecting the first active detection bundle. A model-assisted concern proposer is allowed only through the same evidence schema and evaluation gates.
- Keep unfamiliarity separate from suspiciousness and evidence strength.
- Start with categorical findings and documented evidence requirements. Do not display a numerical fraud probability without an appropriate calibration study.
- Rule matches contribute concerns. They do not automatically establish fraudulent intent or authenticated identity.
- Do not sum multiple labels extracted from one passage as independent confirmations.
- Ask a clarification only when alternative answers could change the response and the user can reasonably know the answer. Prefer reviewed question templates initially.
- A supported warning can be shown before optional clarification. User reassurance does not erase unrelated evidence.

**Response fields**

| Field | Example values |
| --- | --- |
| Processing status | `complete`, `partial`, `unavailable` |
| Evidence sufficiency | `sufficient_for_stated_concern`, `limited`, `unresolved` |
| Response | `explain`, `clarify`, `warn` |
| Concern | Specific requested-action hypothesis or empty when none is established |
| Next action | A reviewed verification step tied to the concern |

These dimensions are independent. Partial evidence may support a narrow warning. An empty concern is not verified safety.

**Acceptance gate:** The active bundle is benchmarked against simpler alternatives; failure cases are recorded. Uncertainty, model failure, and novelty cannot silently become `safe`. Explanation claims use the evidence and policy that actually produced the decision.

### Step 7 — Build the user experience and repetition policy

**Purpose:** Help the user understand the concern, inspect its basis, and take a useful next step.

**Screens**

1. Submit/share and select a case.
2. Assessment: one specific concern, one primary next action, visible limitations.
3. Expandable evidence and partial timeline.
4. Targeted clarification/correction.
5. Add an update and see why the assessment changed.
6. Payment-request preview and supported handoff.
7. Contribution, privacy, pause, and deletion controls.

**Behavior**

- Distinguish claims from verified facts in everyday language. Show source excerpts and the relationship being inferred.
- Let users correct particular fields or relationships, rather than only providing a generic disagreement button.
- Avoid blanket safe badges and unverified allegations about people or organizations.
- False-positive handling must allow a user to inspect evidence, correct the interpretation, and choose an appropriate verification or continuation path. A single weak signal cannot automatically block a transaction or produce a public accusation.
- False-negative handling must explain coverage limits, offer later updates and a missed-concern report, and route already-acted users to verified response guidance. A user report triggers review and does not automatically establish an outcome label. Monitor missed supported concerns separately from cases with no observable evidence.
- Verification actions must identify what to check. Do not automatically recommend contacting the number provided in the suspicious message as independent verification.
- A user who already acted can select an appropriate response path. Publish incident-response links/instructions only after verifying official sources; automatic reporting is not implemented here.
- Maintain one alert record per case/concern. Repeated evidence updates it quietly. A new action, material increase in support, or significant correction can justify a new alert.
- Evaluate alert changes with the policy; a cooldown is never the sole reason to suppress a newly justified concern.
- Android alerts are opt-in and summarize minimally on the lock screen. A notification stream assessment and a user-requested check have separate interruption metrics.
- Preserve the previous assessment when showing a revised result, with a concise explanation of the change.

**Acceptance gate:** Scenario users can explain the concern, the uncertainty, and the next verification task. Legitimate-case decisions, question burden, and unnecessary warnings are measured alongside scam cases. Error and quota states cannot be confused with successful analysis.

### Step 8 — Discover candidate workflow variations

**Purpose:** Help analysts identify useful patterns beyond the current reviewed library.

**Work**

- Include separately authorized contributions with provenance and review status: suspicious, unresolved, and legitimate comparison reports.
- Minimize report content and preserve enough source references to inspect proposed groupings.
- Identify exact and near duplicates; report apparent incident independence with limitations. Multiple submissions do not automatically create multiple corroborating incidents.
- Build two similarity baselines: original-text similarity and structured-workflow similarity. Benchmark a lightweight encoder against TF-IDF.
- Retrieve candidate neighbors, then group only when evidence supports shared actions/relations. Keep unmatched cases available for review.
- Show the nearest existing reviewed pattern and the specific proposed difference. Retain unfamiliar actions discarded by normalization as review material.
- Separate shared tactics, shared workflow, and evidence of linked incidents. Do not label a group a campaign without supporting linkage.
- Include examples that weaken the proposed grouping, not only its most convincing members.

**Review card:** Description, supporting cases, conflicting examples, proposed variation, duplicate/independence notes, collection period, evidence quality, and review history.

**Review states:** `candidate`, `needs_evidence`, `existing_pattern`, `rejected`, `accepted_for_evaluation`. Acceptance does not deploy a rule.

**Acceptance gate:** Evaluate related-case grouping, incorrect merges, useful candidates, missed candidates, and analyst effort on a held-out report stream. Label simulated timing. A rise in submissions is not automatically a rise in real-world prevalence.

### Step 9 — Evaluate, release, and roll back updates

**Purpose:** Convert useful discoveries into justified improvements without reinforcing errors.

**Work**

1. Write an update proposal with required evidence, intended benefit, legitimate lookalikes, expected failure modes, and source lineage.
2. Diagnose whether the failure originates in OCR, extraction, relationships, assessment, or presentation. Fix the originating component.
3. Implement patterns as declarative, schema-validated data. Never execute model-generated code or arbitrary rule expressions.
4. Compare current and candidate bundles on the same regression and fresh evaluation cases. Inspect changed decisions, overlapping patterns, and repeated-source evidence.
5. Review latency, extra questions, unresolved outcomes, false warnings, and detection timing together. Record the trade-off explicitly.
6. Pin the complete bundle: extractor schema/prompt/model, relationship logic, assessment policy, pattern library, and explanation templates.
7. Activate atomically. In-flight jobs retain their starting bundle. Reassessment under a new bundle is an explicit event.
8. Support rollback to a compatible bundle and replay affected cases when derived state has changed.

**Feedback handling:** User acceptance, dismissal, no reported loss, analyst opinion, and externally supported outcome remain distinct evidence types. None silently replaces the ground-truth label.

**Acceptance gate:** Demonstrate at least one accepted update and one rejected candidate or regression. Fresh cases are independent of the discovery examples. A rollback restores compatible processing and leaves an audit record without exposing deleted personal material.

### Step 10 — Integrate, evaluate, and prepare the demonstration

**Purpose:** Establish detection, user, and adaptation value in one operating system.

**Integration order**

1. Text ingestion, evaluation baseline, and one complete assessment path.
2. Revision handling, corrections, and failure states.
3. Android sharing, local OCR/QR, and tested notification access.
4. Contextual payment preview, sandbox verification, and supported handoff readiness.
5. Contribution and analyst discovery loop.
6. Tested update activation, rollback, and deployment hardening.

**Value gates**

| Gate | Evidence required |
| --- | --- |
| Detection value | Fair comparison with direct conversation assessment; documented benefit or a justified simplification |
| User value | Users understand supported concerns and limitations and identify an appropriate next action |
| Adaptation value | Reviewed changes improve fresh-case behavior without unacceptable regressions |
| Integration value | Tested phone signals and verified sandbox payment events reach the same case engine |

**Demonstration sequence**

- Begin with a submitted interaction and show exactly what is observable.
- Identify the user's intended outcome, the next action, the arrival channel, and whether the response reaches the user before that action.
- Add a financial request and reveal the evidence supporting the assessment.
- Show a legitimate comparison that receives an appropriate response.
- Correct a mistaken interpretation and show dependent state change.
- Process a later event without duplicating an unchanged warning.
- Show payment-request checking and a gateway test transaction separately from any live-capable handoff.
- Review a candidate pattern and its limitations; compare current and candidate detection on fresh cases.
- Reject a harmful update or roll back a demonstrated regression.
- Show quota exhaustion or connectivity failure with an honest unavailable state.

Prepared demonstrations supplement the untouched evaluation results. Synthetic content, simulated streams, and provider test transactions must be visible in the presentation. No real transfers are required to prove the sandbox integration.

**Mandatory evidence of restraint:** Include a difficult legitimate lookalike, an initial interpretation that is corrected, and a proposed update rejected for causing a documented regression. These must exercise the actual assessment/correction/evaluation paths. Explain both the concern and why the system limits or changes its response. Prepared failure examples do not replace the independent evaluation report.

**Presentation package:** Use one complete user journey as the main narrative. Show one architecture view, the relevant baseline results, a reviewed update comparison, and concise coverage/privacy limitations. Keep detailed schemas and component descriptions in supporting material. Transfer every material claim to the rubric evidence register, and ensure evidence needed by reviewers is present in the submitted document rather than available only through an external link. Recheck official page/slide limits before export.

The user-supplied "Build for Trust" and "Final Check Before You Submit" pages add mandatory content requirements, recorded in Section 13. Show the safeguards in both the pitch and the architectural overview. The pitch is limited to 10 slides, the architecture overview to 3 pages/slides, and the submission must be one clear PDF. Follow the content and packaging checks in Section 13 when preparing the artifact.

**Acceptance gate:** Reproducible startup, passing required tests, recorded capability matrix, evaluation report with denominators and limitations, and a demonstration that does not depend on hidden precomputed answers. Label any cached replay as a replay.

## 4. Core contracts and persistence

### Primary entities

| Entity | Essential fields |
| --- | --- |
| User / session | Identity, role, revocation state, consent settings |
| Case | Owner, revision, status, language, created/updated times, retention deadline |
| Source event | Event ID, case ID, source type, received/observed times, provenance, content digest, classification |
| Source artifact | Local/private reference, validated MIME type, retention, OCR blocks and coordinates |
| Statement | Source span, actor, assertion mode, action/claim fields, schema version, uncertainties |
| Relation | Statement references, type, explicit/inferred state, supporting/opposing evidence, validity revision |
| Assessment | Case revision, bundle version, concerns, limitations, response, next action, processing status |
| Alert | Case/concern identity, evidence fingerprint, last shown revision, acknowledged state |
| Payment request | Original parsed fields, canonical digest, assessment binding, mode, handoff status |
| Gateway event | Provider/test mode, event ID, verified signature status, amount/order matching, payment status |
| Contribution | Consent version, minimized report, source lineage, withdrawal state |
| Candidate / pattern | Similar cases, distinction from library, evidence limits, review state, version |
| Processing job | Revision, bundle, lease, attempt count, provider, status, redacted diagnostics |
| Evaluation run | Dataset manifest, split, model/configuration, outputs, metrics, limitations |

Use foreign keys, transaction boundaries, and ownership checks. Evidence references are typed IDs rather than arbitrary model-generated URLs.

### Illustrative source event

```json
{
  "event_id": "evt_example_12",
  "case_id": "case_example_1",
  "source_type": "user_shared_text",
  "received_at": "2026-09-29T10:00:00Z",
  "observed_at": null,
  "speaker_ref": "contact_1",
  "text": "Send INR 2000 before we release your withdrawal.",
  "language": "en",
  "data_class": "synthetic_demo",
  "provenance": {"provided_by": "user", "chronology": "unknown"}
}
```

### Illustrative assessment

```json
{
  "case_revision": 3,
  "bundle_version": "candidate-v1",
  "processing_status": "complete",
  "response": "warn",
  "concerns": [{
    "id": "concern_1",
    "description": "Additional payment is a stated condition for accessing claimed funds.",
    "evidence_refs": ["statement_12"],
    "limitations": ["Sender identity and claimed funds are unverified."]
  }],
  "clarification": null,
  "next_action_id": "verify_with_independent_channel"
}
```

Examples specify shapes, not expected model performance or a universal rule that every such request warrants a warning. Dates and IDs are illustrative.

### API surface

| Endpoint | Purpose |
| --- | --- |
| `POST /v1/cases` | Create an owned case |
| `POST /v1/cases/{id}/events` | Ingest events with an idempotency key; return accepted revision/job |
| `GET /v1/cases/{id}` | Current state and processing status |
| `GET /v1/cases/{id}/assessments` | Revisioned assessment history |
| `POST /v1/cases/{id}/corrections` | Add a correction and trigger dependent recomputation |
| `POST /v1/cases/{id}/answers` | Answer a specific clarification with provenance |
| `POST /v1/cases/{id}/contributions` | Record separate contribution consent |
| `DELETE /v1/cases/{id}` | Delete source/derived data and withdraw associated contributions |
| `POST /v1/payment-requests` | Validate and bind supplied payment details to a case |
| `POST /v1/payment-requests/{id}/handoff` | Check current binding and produce supported handoff instructions |
| `POST /v1/payments/test-orders` | Create a sandbox gateway order with server-controlled fields |
| `POST /v1/webhooks/payments/{provider}` | Verify and ingest provider events; no user session required, signature mandatory |
| `GET /v1/analyst/candidates` | Authorized review queue |
| `POST /v1/analyst/candidates/{id}/reviews` | Record review and explanation |
| `POST /v1/analyst/updates/{id}/evaluate` | Schedule evaluation of a proposed bundle |
| `POST /v1/admin/bundles/{id}/activate` | Authorized atomic activation after recorded review |
| `POST /v1/admin/bundles/{id}/rollback` | Restore a compatible approved bundle |

Require authentication and object-level authorization everywhere except signature-authenticated webhooks and minimal health endpoints. Enforce CSRF protection for cookie-based browser sessions. Android credentials must be revocable. Use separate analyst/admin roles; development fixtures must not disable authorization in a deployed build.

## 5. Free-provider operation and data routing

### Adapter contract

Each adapter exposes structured extraction and, if selected by evaluation, concern assessment. It returns parsed output, usage, model identity, latency, finish/refusal status, and failure category. Validate output through the same internal schemas regardless of provider.

Provider/model selection is a benchmark result, not a hard-coded assumption. Record actual free availability and account quotas during setup. Model changes require compatibility and evaluation checks.

### Quota handling

- Enforce request and token budgets centrally across API workers, background discovery, and evaluation jobs.
- Give interactive cases priority over background work without creating unbounded waits.
- Count retries and structured-output repairs against the same budget.
- Respect rate-limit responses and retry timing; use bounded exponential backoff and a circuit breaker.
- Cache only with keys including owner/case scope, sanitized input digest, model, prompt, schema, and bundle version. Delete associated entries when the source is deleted. Never share sensitive caches across users.
- Reprocess changed evidence and required context; do not repeatedly submit the entire history without measuring cost.
- A fallback must be both quality-approved and permitted for the data class. Exhausted approved options yield `assessment_unavailable`.
- Never rotate accounts/keys to evade organization or project limits. Never silently enter a paid tier.

Groq and Gemini limits are account/model dependent. Use current account settings, not copied fixed quotas. Sources: [Groq limits](https://console.groq.com/docs/rate-limits), [Gemini limits](https://ai.google.dev/gemini-api/docs/rate-limits).

### Data routing policy

| Data class | Default cloud policy |
| --- | --- |
| Synthetic demonstration | Approved free provider after normal security checks |
| Public, permitted, non-sensitive research material | Approved provider consistent with source terms |
| Real private financial conversation | Disabled until a documented data-handling route is configured and consent captured |
| Credentials, OTPs, PINs, full financial identifiers | Exclude from cloud payload; retain only the fact that such information was requested when needed |

Groq documents data controls, including zero-data-retention settings; availability/configuration must be verified in the actual account. Configure suitable controls before enabling private-data mode. Gemini unpaid-service terms require particular care with personal or sensitive material; private-data jobs must not silently fall back there. Redaction is risk reduction and does not automatically establish anonymity. Sources: [Groq data controls](https://console.groq.com/docs/your-data), [Gemini terms](https://ai.google.dev/gemini-api/terms).

No local generation fallback is part of the plan. During cloud outages, local parsing and stored evidence remain available while new model assessment is explicitly unavailable.

## 6. Security, retention, and user control

- Keep API keys and gateway secrets on the backend. Store local development secrets outside Git; provide names only in `.env.example`.
- Use TLS for device/backend communication and private authenticated storage for any retained artifacts.
- Treat screenshots, transcripts, QR codes, model outputs, and contributed reports as untrusted data.
- Escape rendered text, forbid arbitrary HTML/script rendering, and prevent model-generated external links from becoming trusted verification routes.
- Disable model tools for extraction and concern assessment. User-submitted instructions cannot change policies or activate updates.
- Validate request size, upload dimensions, supported encodings, structured output bounds, and job resource budgets.
- Avoid raw transcripts, payment identifiers, or model outputs in routine logs. Restrict full diagnostic traces to explicitly permitted cases and their retention window.
- Apply user/role authorization to every query and mutation, including evidence retrieval, candidate cards, and exported reports.
- Maintain case-local stable placeholders for entities. Cross-case entity linkage requires a separately justified design; it is not obtained by exposing private identifiers to analysts.

### Initial retention defaults

These are proposed product defaults to implement and display, not claims about statutory retention requirements.

| Material | Proposed default |
| --- | --- |
| Raw screenshots | Client-local during active review; backend upload opt-in, delete after processing or within 24 hours |
| Private case text and derived records | Seven days, with explicit user extension and immediate user deletion |
| Opted-in minimized reports | Thirty days, then renew consent or delete; no indefinite default |
| Content-free operational logs | Seven days |
| Synthetic evaluation fixtures | Retain with versioned provenance |

Deletion must cover database rows, blobs, jobs, caches, embeddings, and report memberships. Mark affected candidate groups for recomputation. If a pattern's supporting evidence is withdrawn, review whether the remaining evidence justifies its continued status. Keep a non-content audit tombstone; do not preserve personal text inside supposedly immutable version history. Document backup expiry and never promise immediate deletion from backups or external providers when it cannot be ensured.

## 7. Metrics and release gates

### Metric definitions

| Metric | Definition / caution |
| --- | --- |
| Concern detection | Recall on reviewer-eligible prefixes/cases with observable support |
| Timely detection | Detection after a justified point and before the relevant action, when the timing is known |
| False warning rate | Legitimate journeys with at least one unwarranted warning divided by eligible legitimate journeys |
| Repeated alerts | Unnecessary additional alerts per case after a concern was already shown |
| Missed escalation | Material new supported concerns that did not produce an appropriate update |
| Coverage | Completed useful assessments, unresolved cases, and unavailable cases reported separately |
| Clarification value | Decision changes attributable to answers versus added questions and user effort |
| Extraction quality | Critical fields, negation, speaker attribution, and supporting-span accuracy |
| Explanation fidelity | Claims supported by the evidence and actual decision path |
| Discovery usefulness | Useful reviewed candidates, incorrect merges, missed patterns, and review effort |
| Update impact | Paired changes in outcomes on fresh and regression cases |
| Performance | Queue delay and end-to-end latency at median and tail, token usage, quota errors, failure rate |

Report denominators, base-case counts, data sources, and uncertainty intervals where appropriate. Balanced evaluation prevalence does not establish real-world alert precision. Do not count future-labelled early messages as detectable failures before supporting evidence exists.

### Engineering release gates

- No known authentication/ownership failure in the required test suite.
- No stale assessment can overwrite a newer revision.
- No unverified gateway response is represented as confirmed success.
- No answer-bearing annotation reaches a detection input in tested data loaders.
- Every displayed evidence reference resolves to an available permitted source or an explicit deletion state.
- Provider failures, refusals, and exhausted quotas remain visible unavailable/partial states.
- No pattern update activates without recorded evaluation and an authorized decision.
- Any remaining quality limitations are disclosed with the affected capabilities.
- False-positive and false-negative response paths are both exercised, including the user who has already acted.
- User, analyst, and release-admin authority are enforced in the interface and API; model output alone cannot authorize a high-impact action.
- English robustness/bias slices are reported with their sample sizes and limitations; insufficient evidence cannot become a fairness claim.

Set quantitative detection and latency targets after initial baseline measurement and before tuning the candidate for acceptance. Record the targets and rationale. Do not invent a 95% or 99% target and then select examples to meet it. Free quotas and Android background scheduling may limit notification timeliness; measure this explicitly.

## 8. Required test matrix

| Test | Expected behavior |
| --- | --- |
| Same upload submitted twice | One logical event; safe repeated response |
| New evidence arrives during analysis | Old result cannot become current |
| User corrects speaker or amount | Dependent relationships and assessment recompute |
| Screenshot order is uncertain | Partial chronology remains visible |
| Two transactions share an amount | No unsupported merge |
| Threat appears in a quoted warning | Correct assertion role; no invented direct request |
| Consistent scam / changing legitimate terms | Decisions depend on complete evidence, not contradiction alone |
| Prompt injection in submitted text | No policy override, tool execution, or update activation |
| Malformed model JSON / refusal / timeout | Bounded repair or explicit failure |
| API quota exhausted | Queue/fallback policy respected; no paid escalation |
| Notification permission revoked | Collection stops; coverage status updates |
| Sachet creates its own notification | No recursive ingestion |
| Device disconnected or background-limited | Delay is recorded; no claim of timely protection |
| QR/link contains conflicting fields | Reject or request clarification; no silent destination choice |
| Payment details change after assessment | Assessment binding invalidates |
| Forged/replayed gateway callback | Reject forgery; process legitimate duplicate idempotently |
| Pending callback follows captured event | Preserve provider-valid state progression |
| Repeated report / coordinated false reports | No automatic corroboration or rule deployment |
| Candidate harms legitimate cases | Reject or revise update with recorded reason |
| Bundle changes mid-job | Job remains tied to its original bundle |
| User deletes a contributed case | Derived data and memberships are removed/recomputed |
| Non-English material | Explicit support limitation; no untested quality claim |
| Weak isolated signal | No automatic fraud block or public accusation; proportionate explanation or clarification |
| Missed concern followed by new evidence | Allow an update/report, reassess the case, and retain the earlier assessment's limitations |
| High-impact action requested by model or unauthorized user | Reject action; require the defined authorized human workflow |
| Meaning-preserving English spelling/name variation | Inspect unjustified changes in concern, response, and question burden |
| Analyst requests another user's unconsented raw evidence | Deny access; expose only the authorized contribution |

## 9. Suggested repository layout

```text
sachet/
  apps/
    web/                    # User UI and analyst routes
    android/                # Share receiver, local OCR/QR, notifications, handoff
  services/
    api/
      app/
        auth/
        ingestion/
        extraction/
        case_tracking/
        assessment/
        responses/
        payments/
        discovery/
        updates/
        providers/
        privacy/
        persistence/
    worker/
  contracts/                # Versioned JSON schemas and generated client types
  policies/                 # Declarative patterns, questions, response templates
  evaluation/
    manifests/
    annotations/
    baselines/
    runners/
    reports/
  tests/
    unit/
    integration/
    end_to_end/
    adversarial/
  infra/
    compose.yaml
  docs/
    capability-matrix.md
    data-register.md
    model-benchmark.md
    decision-log.md
    demo-runbook.md
  .env.example
  README.md
  implementation.md
```

Do not commit secrets, private reports, raw user uploads, downloaded restricted datasets, or identifiable evaluation traces. Commit small synthetic fixtures and dataset manifests when permitted.

### Configuration categories

Document provider/model identifiers, free quota budgets, timeouts, repair limits, permitted data classes, active bundle, retention windows, database access, Android API endpoint, gateway test credentials, webhook verification secret, and live-handoff flag. Keep account-specific values out of source control.

## 10. Build tracking and completion checklist

| Milestone | Required artifacts | Depends on |
| --- | --- | --- |
| M0 — Access and contracts | Capability matrix, schemas, provider/data policies | None |
| M1 — Baseline evidence | Audited data loader, annotated seed set, baseline report | M0 |
| M2 — Working case engine | Ingestion, extraction, state, assessment, correction tests | M0–M1 |
| M3 — User and phone path | Responsive UI, Android sharing, tested notification coverage | M2 |
| M4 — Payment integration | Request binding, actual sandbox adapter, verified events, handoff readiness | M0, M2–M3 |
| M5 — Discovery | Contribution controls, grouping comparisons, analyst cards | M1–M3 |
| M6 — Controlled updates | Evaluation gates, activation, rollback, fresh-case results | M5 |
| M7 — Release evidence | Full test report, usability findings, runbook, reproducible deployment | M2–M6 |

Assign owners for data/evaluation, case/detection backend, web experience, Android/payment integration, and discovery/update review according to the actual team. These are workstreams, not an assumed team size. Use contract fixtures so modules can be developed independently without changing schemas informally.

### Accountable responsibilities

Map each role below to an actual team member in `docs/decision-log.md` before the finale and show the assignment in the execution-plan slide. One person may hold several roles. The roles specify responsibilities without inventing team size or member names.

| Role | Accountable deliverable | Acceptance responsibility |
| --- | --- | --- |
| Integration lead | End-to-end vertical slice, shared contracts, revision handling, deployment | A case completes across client, backend, worker, and persistence with correct error states |
| Detection/evaluation lead | Data manifests, annotations, baseline runs, case assessment, metrics | No input leakage; fair comparison; clear failure analysis and claim limits |
| Client/integration lead | User flow, Android sharing/notifications, payment request and sandbox integration | Tested device coverage, intelligible responses, request binding, verified test status |
| Discovery/review lead | Candidate groups, analyst review, update evaluation, activation/rollback | Useful candidates with provenance; accepted/rejected changes supported by evidence |
| Submission lead | Rubric evidence register, finale checkpoints, demonstration and PDF | Every claim is traceable; simulated capabilities are labelled; submission is self-contained |

These are accountable functions rather than isolated silos. Use a second reviewer for evaluation labels, changed decisions, and releases where available; record any independence limitation when the same person must implement and review.

### Finale execution plan

The supplied final-submission checklist explicitly asks what can be demonstrated in 48 hours. The schedule below answers that requirement. Confirm current organizer rules on pre-existing work and event logistics before execution. Ample preparation time does not remove the need for a clear finale plan.

**Before the finale:** Verify whether pre-existing code, prepared datasets, and external services are permitted; disclose them as required. Prepare only allowed assets. Confirm account access, test keys, target devices, free quotas, evaluation manifests, and role assignments. The schedule assumes permitted foundations are available. If the rules require a clean build, re-scope the promised finale deliverable before submission rather than assume every full-product capability can be rebuilt in 48 hours.

The full-product milestones above remain the implementation objective. The finale should demonstrate a complete assessment journey and one reviewed update cycle, with phone/payment capabilities included according to verified access.

| Finale window | Primary responsibility | Deliverable and checkpoint |
| --- | --- | --- |
| Hours 0–4 | Integration + evaluation leads | Verify setup and allowed starting state; freeze contracts, evaluation protocol, and promised coverage; run baseline smoke checks |
| Hours 4–12 | Integration + detection leads | Complete or validate submission -> extraction -> case -> assessment -> response; test corrections and unavailable states |
| Hours 12–20 | Client/integration lead | Connect tested Android sharing and available notification signals; bind payment details; verify a gateway sandbox event end to end |
| Hours 20–28 | Discovery/review lead | Connect contributed reports, evidence-backed candidate review, and a candidate update; demonstrate rejection criteria |
| Hours 28–36 | All technical leads | Integrate the complete flow; run device, quota, concurrency, privacy, and deletion checks; conduct short user scenario sessions |
| Hours 36–42 | Evaluation + submission leads | Freeze the candidate release; run the untouched evaluation; record outcomes and limitations; assemble the evidence register and submission |
| Hours 42–48 | Integration + submission leads | Rehearse on target devices, verify reproducible startup and contingency paths, finalize artifacts; limit changes to critical defects |

At each checkpoint, record completed capabilities, blocked dependencies, open defects, and the next owner. A late critical fix requires rerunning affected checks; describe any evaluation set that influenced the fix as no longer untouched. Additional feature work must not displace completion of the core decision flow and evidence package.

### Contingencies and honest demonstration behavior

| Problem | Planned response | Effect on claims / completion status |
| --- | --- | --- |
| Free API throttling or outage | Queue within configured limits; use a tested, data-compatible provider if available; show unavailable state otherwise | A clearly labelled stored replay may explain behavior but cannot count as a successful live inference run |
| Notification fields unavailable or delayed | Continue through Android sharing and document device/app coverage | Do not claim continuous monitoring or timely notification protection for the unsupported path |
| Gateway account or sandbox prerequisite missing | Preserve request parsing and assessment; show a labelled contract simulator while resolving access | Simulator does not satisfy the real sandbox integration gate; keep that deliverable blocked/partial |
| Live payment prerequisites unmet | Use verified gateway test mode and document handoff readiness separately | No live-money or universal payment-app integration claim |
| Structured pipeline adds errors or little benefit | Use the better-evaluated assessment path and retain only justified traceability features | Update the differentiation claim to match the result |
| Candidate update harms legitimate cases | Reject or roll back and retain the current approved bundle | Demonstrate the review control; do not describe the candidate as an improvement |
| Private-data route not configured | Use synthetic/permitted non-sensitive test material while completing the provider gate | No claim of private financial-data readiness |
| Submission/demo scope exceeds available time | Protect the complete user assessment and reviewed update cycle; mark ancillary capabilities by observed status | Do not label partial or simulated integrations as complete |

### Adoption and scale evidence

- Observe whether users can recognize when to share material, submit relevant context, and understand a next action; report task friction and abandonment in the tested sample.
- Measure the complete phone-input-to-assessment path, including device scheduling and queue delays rather than only model latency.
- Report sustainable tested throughput under the actual free quotas, including competing evaluation/discovery work. Treat those quotas as prototype capacity, not evidence of deployment at scale.
- Describe the future partner-input interface separately from actual partner access. An API contract establishes an integration design; only an exercised integration establishes access and behavior.
- Keep the current zero-paid-API requirement. Any future capacity plan requiring paid infrastructure or a different data agreement is a future dependency, not part of the completed prototype.

### Completion checklist

- [ ] All supported inputs and permissions have device/account evidence.
- [ ] Selected model/provider passes the common evaluation and data-policy gates.
- [ ] Free quotas are configured and failure paths tested.
- [ ] Dataset access, provenance, split integrity, and permitted use are documented.
- [ ] Core concern detection is compared with simpler baselines.
- [ ] Corrections, asynchronous revisions, and dependency invalidation work.
- [ ] English assessment and explanation quality are measured.
- [ ] Phone coverage limitations and alert behavior are visible.
- [ ] Payment integration uses verified server events and safe request binding.
- [ ] Discovery usefulness is evaluated independently of single-case detection.
- [ ] Accepted/rejected updates and rollback are demonstrated.
- [ ] Privacy, deletion, access control, and secret handling are verified.
- [ ] User tests include legitimate, ambiguous, and already-acted cases.
- [ ] Demo material clearly identifies synthetic, replayed, and gateway-test content.
- [ ] Final submission contains only claims supported by recorded results.
- [ ] All seven rubric criteria map to concrete artifacts in the evidence register.
- [ ] The intervention point, input coverage, and observed response timing are explicit in the main journey.
- [ ] Differentiation hypotheses have fair comparisons or are labelled unproven.
- [ ] Finale responsibilities are assigned to actual members and checkpoints have contingency owners.
- [ ] Legitimate lookalike, corrected interpretation, and rejected update are demonstrated through working paths.
- [ ] Adoption and free-quota scale limits are reported without unsupported deployment claims.
- [ ] All five Build for Trust questions have visible answers in both pitch and architecture content.
- [ ] False positives, false negatives, bias, action authority, and human escalation have explicit evidence or proof plans.
- [ ] The five final-submission checks in Section 13 can be answered without opening external links.
- [ ] One PDF contains a pitch of at most 10 slides and an architecture overview of at most 3 pages/slides under the confirmed packaging interpretation.

## 11. Decisions resolved and external dependencies

**Resolved:** English first; skilled team; no artificial eight-hour constraint; free Groq/Gemini inference; no Ollama; web user/analyst interfaces; Android sharing plus optional notifications; contextual payment-request checking; gateway sandbox integration; reviewed discovery and versioned updates.

**To determine through engineering evidence:** Exact free model, provider quotas, target-device coverage, OCR module quality, gateway test capabilities, supported live-handoff prerequisites, embedding model, deployment host, and quantitative release targets.

These are implementation checkpoints, not invitations to reopen the entire design. Ask the user when account access, unavailable provider prerequisites, or a material product trade-off requires their decision. Resolve routine technical choices by benchmarking and document the result.

## 12. Source maintenance

Documentation links in this plan were consulted during planning. Provider quotas, account settings, platform rules, and SDK behavior may change. Recheck the relevant primary documentation at dependency selection and before any live deployment. Keep a dated capability record instead of presenting documentation alone as proof that an integration works on the target device/account.

Additional reference: [Google Play SMS/call-log permissions](https://support.google.com/googleplay/android-developer/answer/10208820?hl=en-GB). Notification sharing does not imply permission to read SMS databases or record calls.

## 13. Mandatory submission content: trust and final checks

### Source and submission format

This section records the organizer guidance supplied by the user as images titled **Build for Trust** and **Final Check Before You Submit**. These requirements supplement the seven-category scoring rubric. They define content to include in the eventual presentation; no slide deck or PDF has been generated by this implementation document.

- Submit **one clear PDF** addressing **one challenge statement**. Sachet addresses scam pattern recognition.
- The **pitch deck has a maximum of 10 slides**. Include the title/cover in that count unless the organizers explicitly provide an exception.
- The **architectural overview has a maximum of 3 pages or 3 slides**.
- Explain assumptions, validation, and what can be demonstrated in **48 hours**.
- Make safeguards visible in **both the pitch and the architecture**.
- A reviewer must be able to find the primary user, harmful moment, and exact threat pattern in under a minute.

Plan the pitch and architecture as two clearly identified components inside one PDF. The supplied page gives separate component maxima; it does not explicitly settle whether the architecture must be additional pages or can be embedded in the pitch. Resolve any remaining packaging ambiguity with the organizing team before final export, as their guidance requests. Until then, author reusable architecture views and retain the ability to embed them without expanding the 10-slide pitch. Do not assume an extra appendix is exempt from a limit.

Preserve required AI/model/dataset/third-party attribution from the earlier event guidance in visible submission content or an explicitly permitted appendix. The submitted PDF must carry the evidence needed for review; speaker notes, external demos, and repository links are supplementary.

### Build for Trust requirement map

| Organizer question | Sachet answer to show | Pitch location | Architecture location | Supporting implementation evidence |
| --- | --- | --- | --- | --- |
| What data do you need? | List each input, its purpose, collection point, consent/authorization, and exclusions; separate local processing from cloud transmission | P4 and P7 | A1 and A3 | Data register, provider-routing policy, permission controls, actual outbound payload inspection |
| What happens when the system is wrong? | Explain both false alarms and missed concerns; show correction, uncertainty, later updates, and response after an action; no automatic blocking or accusation from one weak signal | P6 and P8 | A2 and A3 | Legitimate lookalike, corrected interpretation, missed-concern case, failure-state and alert-policy tests |
| Who can act on the result? | Identify user choices, analyst review, release authority, and escalation before high-impact actions | P3 and P6 | A3 | Role permissions, review/release records, unauthorized-action tests |
| How will users understand the result? | Show a specific concern, supporting evidence, uncertainty, and a practical next action; a score alone is insufficient | P3 and P6 | A2 output and A3 response policy | Actual assessment screen, explanation-fidelity checks, comprehension findings |
| How will the product resist misuse? | Address adaptation, adversarial content, report manipulation, privacy misuse, and unauthorized evidence access | P7 and P8 | A3 | Injection tests, duplicate/report checks, source lineage, access/deletion tests, controlled update evaluation |

Every cell names required content, not an assertion that its implementation has passed. Use the evidence-register status to distinguish a design commitment from a measured result.

### Data necessity and exclusions

| Input | Why it is needed | Authorization and handling | Exclusions / limitations |
| --- | --- | --- | --- |
| Selected conversation text or screenshots | Establish what was claimed or requested and connect it to prior context | User-initiated sharing; local extraction/minimization; disclose any permitted cloud processing | No default upload of complete phone history or all chats; images can omit context |
| Selected notification fields | Update a case when a supported source exposes new evidence | Optional notification access, source allowlist, visible pause, tested field availability | No blanket claim of full conversation, hidden content, or outgoing-message access |
| User's intended outcome and answers | Resolve a specific ambiguity that changes the assessment | Ask only as needed; retain as user-provided evidence | Answers do not authenticate the sender or prove the interaction legitimate |
| Payment QR/link fields | Relate stated payee, amount, and purpose to the conversation before handoff | Deliberate user submission; local validation; request digest bound to assessment | No UPI PIN, OTP, banking password, card CVV, or autonomous payment authorization |
| Gateway test order/status events | Verify what occurred in our integrated test checkout | Test account, server validation, signature and order matching | No visibility into unrelated payment apps or proof of prevention from a post-payment event |
| Minimized contributed report | Compare workflows and review possible updates | Separate contribution choice, reviewed access, retention and withdrawal controls | No automatic reuse of private checks, unnecessary recipient identifiers, or unreviewed training labels |

Also exclude continuous microphone/call capture, unrelated contacts, location history, and biometric data from the initial collection design. A screenshot can incidentally contain sensitive information: inspect/minimize before submission and enforce the provider gate rather than claiming that the interface can never receive sensitive material.

### Errors, bias, and action authority

**False positive:** Explain the particular concern, permit targeted correction, preserve a legitimate continuation/verification path, and record whether the changed interpretation resolves the concern. Do not permanently mark a person or account as fraudulent from a weak assessment.

**False negative:** State that no detected concern is not an authentication or guarantee. Let users add evidence and report a suspected miss. Reassess when new information arrives, offer a separately verified already-acted response path, and send eligible misses for review. Do not erase earlier output or silently replace an uncertain label with a confirmed scam label.

**Bias and robustness:** Within the English release, compare outcomes across formal/informal language, spelling errors, OCR quality, verbosity, and reviewed Indian-English variations. Use meaning-preserving changes to names or superficial wording to probe reliance on irrelevant cues. Report detection, false warnings, unresolved cases, and question burden by sufficiently populated slices. Do not collect unnecessary sensitive demographics to create a fairness dashboard, and do not equate English-only support with absence of bias. Publish thin-sample limitations.

| Actor | Allowed action | Boundary / escalation |
| --- | --- | --- |
| User | Inspect/correct evidence, answer or skip a question, add updates, independently verify, and deliberately choose a supported handoff | Sachet does not enter credentials or authorize transfers; integrity checks on malformed/changed payment details are distinct from a fraud verdict |
| Analyst | Review authorized minimized reports, inspect supporting evidence, reject/group candidates, and propose an update | No unrestricted access to private raw cases, account freezing, automatic reporting, or public blacklisting |
| Release admin / designated reviewer | Review evaluation and activate/roll back an approved compatible bundle | Record evidence and authorization before changing consumer detection; use a second reviewer where available |
| Model / automated worker | Extract bounded information, propose supported concerns/groupings, and execute predefined processing jobs | No autonomous financial action, public accusation, external report, or deployment of a generated rule |
| External bank/provider/official channel | Perform actions within its own verified process when the user initiates the appropriate route | Sachet must not imply authority or integration that it does not have |

High-impact actions require the appropriate human and institutional authority. Our model output does not supply that authority. The prototype provides evidence and supported navigation; it does not silently submit an accusation or take control of a financial account.

### Scam-pattern technical cues

| Cue from organizer guidance | Required Sachet representation |
| --- | --- |
| Scam workflow | Show the ordered/partially ordered claims, requested actions, and conditions supported by the submitted evidence; include gaps |
| Available metadata or behavioural signals | Name concrete observed fields such as available timestamps, source channel, repetition, changed payment conditions, and the user's stated goal; distinguish them from inferred intent |
| Timely action | Mark the intended harmful action and actual evidence/response availability; show unknown timing explicitly |
| Alert fatigue | Demonstrate one developing case, deduplication, selective questions, and an update only when materially justified; measure missed escalations as well |
| Transaction privacy | Show local payment parsing, minimized cloud payloads, credential exclusion, consent, retention, and limited analyst access |

Voice-cloning and deepfake guidance belongs to other tracks. Sachet's submission must stay focused on scam patterns; a phone integration does not imply a voice-cloning detector or call-audio forensic capability.

### Proposed pitch content: P1–P10

These are content slots within the 10-slide maximum, including the opening slide. Keep one main idea per slide and use visible labels for proposed, implemented, measured, simulated, and test-mode content where relevant. Dense implementation detail stays in the architecture component or allowed supporting material.

| Slide | Subject | Required content / evidence |
| --- | --- | --- |
| P1 | Sachet: user and harmful moment | Name the primary user, financial decision, and exact threat pattern; identify Statement 2 and the project/team |
| P2 | A developing scam interaction | Evidence-backed journey, what the user wants, what changes, what Sachet can observe, and where a warning could help |
| P3 | Product experience | Input -> assessment -> evidence -> correction/verification -> optional supported handoff; show the user choice and limitation |
| P4 | Detection approach and required signals | Observable inputs, why each matters, source-linked relationships, and how concerns are assessed; distinguish rules/models from unsupported assumptions |
| P5 | System architecture | One readable system/data-flow view with on-device, backend, external-provider, and analyst boundaries and actual outputs |
| P6 | Decisions when evidence is uncertain | False-positive/false-negative handling, understandable messages, correction, human authority, and repeated-alert behavior |
| P7 | Privacy and misuse controls | Consent, collection exclusions, cloud routing, retention/deletion, evidence access, adversarial input and report controls |
| P8 | Validation and proof plan | Assumptions, data provenance, baseline comparisons, legitimate/ambiguous cases, bias slices, metrics, and observed limitations; label unmeasured targets |
| P9 | Differentiation, adoption, and integration | Evidence for the contribution, comparison with existing approaches, actual Android/payment coverage, user friction, quota capacity, and deployment dependencies |
| P10 | 48-hour execution and demonstration | Actual role owners, time checkpoints, minimum complete flow, contingency behavior, and the reviewed update demonstration |

If a dedicated cover is used, it occupies P1; preserve the primary-user/threat answer prominently within P1–P2. Do not add an eleventh pitch slide by treating a cover, conclusion, or references page as automatically exempt.

### Architecture overview: A1–A3

| View | Required diagram/content | Safeguards visible in the view |
| --- | --- | --- |
| A1 — System and data boundaries | User/Android/web inputs, local processing, authenticated backend, storage/worker, external model APIs, payment provider, analyst path, and outputs; label what crosses each boundary | Consent point, minimization, authorized sources, credential exclusion, storage ownership, retention, and provider data gate |
| A2 — Detection and evidence lifecycle | Source events -> extraction -> relations -> concern assessment -> response, with revision/correction dependencies, payment-request binding, and assessment status | Partial evidence, unknown chronology, source traceability, stale-job protection, unsupported-language/error states, and verified versus unverified payment status |
| A3 — Human review and safe operation | User action choices, analyst candidate review, evaluation/release/rollback, feedback, access controls, and failure/escalation paths | Human gates before high-impact changes, no automatic accusation from weak evidence, bias/false-negative checks, adversarial input controls, quota failure, deletion propagation, and alert repetition policy |

Use readable diagrams with named components and labelled arrows. Identify data owners and trust boundaries explicitly; a list of framework logos is not an architectural overview. If these views are embedded in the pitch under the organizer's packaging interpretation, consolidate the corresponding content into the pitch while retaining the ten-slide ceiling. Additional architecture pages, if accepted, remain within their own three-page ceiling and the same PDF.

### Final reviewer check

| Organizer check | Submission pass condition | Reviewer locator |
| --- | --- | --- |
| 01 — The problem | A reader can identify the primary user, harmful moment, and exact threat pattern in under one minute | P1–P2 |
| 02 — The product | Input-to-assessment-to-action/verification/evidence-record flow is explicit and includes the user's role | P3, P6 |
| 03 — The architecture | A legible diagram names components, data boundaries, and outputs; safeguards appear in the architecture | P5, A1–A3 |
| 04 — The proof plan | Assumptions, validation, baseline comparisons, and a credible 48-hour demonstration are stated | P8, P10 |
| 05 — The safeguards | Privacy, false positives, false negatives, bias, explanation, human review, and misuse risks have concrete responses | P6–P8, A3 |

Before export, have a reviewer locate these answers without explanation from the team. Fix missing or ambiguous answers in the document itself. Validate the combined PDF for slide/page counts, legible text and diagrams, correct ordering, visible sources/disclosures, and consistent capability labels. Inspect the exported PDF rather than assuming the editable source renders correctly. This is an artifact-release check; it does not replace software evaluation.
