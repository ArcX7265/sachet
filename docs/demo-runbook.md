# Sachet local demonstration

All sample interactions described here are synthetic. The local rule engine is an engineering baseline. A warning explains a supported concern; it does not authenticate the sender or establish a verified fraud outcome.

## Start

From the project root, run `npm run setup` once and `npm run dev`. Open `http://127.0.0.1:5173`. The API reference is at `http://127.0.0.1:8000/docs`. Keep the terminal running. Demonstration role selection is intended for the local loopback workspace.

## Follow a developing interaction

1. Open the sample **An unexpected withdrawal fee**.
2. Read the initial source material and the limited-context assessment.
3. Add the next prepared message. Inspect the additional payment condition and the exact supporting excerpt.
4. Open the timeline to show how the supplied evidence changes. Amounts and sender claims remain unverified.
5. Add the same request again. The case can record additional evidence while the unchanged concern remains a single alert record.
6. Add a materially different demand, such as a request for an OTP. Inspect the newly supported concern.

## Demonstrate restraint and correction

1. Use **A routine invoice payment** as a legitimate comparison. Do not describe the result as verified safe.
2. Create a separate synthetic case containing `Send me your OTP to complete the refund.`
3. Correct the event to `Never send your OTP to anyone. We will not ask for it.` using the correction control.
4. Verify that the prior source remains marked as superseded, the assessment is recomputed, and its former warning is no longer active.
5. Inspect historical assessments to explain why the result changed.

## Payment-request preview

1. With an assessed case open, paste `upi://pay?pa=example%40bank&pn=Example&am=2000.00&cu=INR&tn=Verification` into payment checking. This is a synthetic identifier, not a destination to pay.
2. Inspect the claimed recipient, amount and limitations beside the case concern.
3. Add new case evidence and show that the old payment binding must be reviewed again.
4. Keep live handoff disabled. A preview does not transfer money or monitor unrelated payment apps.

The Razorpay test-order adapter requires your configured test account and webhook secret. Signed gateway callbacks are tested with fake provider responses in the engineering suite. No real provider transaction should be claimed until separately run and verified in that account. The order concerns the configured test merchant, not the arbitrary UPI recipient from the preview.

## Reviewed workflow update

1. Create a synthetic case with an unfamiliar phrasing: `To get the release code, first transfer a processing deposit of INR 1200.`
2. Preview the minimized report and separately consent to its contribution.
3. Switch to the analyst demonstration role. Review the report, related reports, available evidence and limits of any suggested similarity.
4. Record `accepted_for_evaluation` with a reason. This does not activate an update.
5. Propose a literal pattern with distinct term groups such as `release code`, `processing deposit`, and `first|before`. Enter a specific description and verification action.
6. Run the engineering evaluation. Inspect changed decisions and regressions; a passing result is limited to that small published fixture collection.
7. Switch to the release administrator role to activate an eligible proposal. Reassess the case explicitly to apply it.
8. Roll back to the baseline bundle and reassess again. Existing historical assessments retain their recorded version.
9. Demonstrate a rejected proposal by using an overbroad pattern such as `pay`. Its legitimate-case regressions must prevent activation.

## Failure and control paths

- Select an unconfigured cloud provider only for a synthetic case. The result must state **Assessment unavailable**, without a fabricated success or automatic fallback.
- Check that private cases cannot use the free cloud route.
- Withdraw a contribution and verify it no longer appears to the analyst.
- Delete only a disposable synthetic case and verify its source, assessments, payment previews and contribution are removed from the active database.
- Run `npm test` for ownership, revision, deletion, payment authenticity and release-gate checks.

## Claims the demonstration supports

It can establish that the implemented UI/API flows execute, quote supplied evidence, preserve revisions, apply local patterns and enforce the tested control paths. It does not establish deployment accuracy, user adoption, novelty in the global scam landscape, avoided losses, full phone coverage or independently measured learning improvements.
