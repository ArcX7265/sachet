# Android capability and validation record

Recorded 2026-09-30. The companion lives in `apps/android`. This file describes implemented source behavior; Android build and device execution remain unverified because no Android SDK/device is configured in the build environment.

| Capability | Implemented boundary | Validation status |
| --- | --- | --- |
| Text share / paste | `ACTION_SEND` text/plain; editable review; 16,000-character submission cap; explicit consent | Source reviewed; device share sheet unverified |
| Screenshot extraction | Local bundled ML Kit Latin OCR; editable text; PNG/JPEG/WebP; byte/pixel limits; original image and original OCR block text excluded from upload | Source reviewed; ML Kit/device execution unverified |
| QR / UPI fields | Local QR decoding; strict `upi://pay` parser; recipient, stated name, amount, currency, purpose; no payment launch | Parser source and boundary cases included; provider/payment-device validation pending |
| Notification context | OS permission plus exact package allowlist; disabled initially; pause switch; local previews; no auto-upload | Source reviewed; permission, update, removal, OEM behavior unverified |
| Notification privacy | Best-effort obvious OTP/PIN masking; 50 previews; 24-hour expiry on capture/access; encrypted storage | Code reviewed; not a comprehensive secret detector or exact expiry scheduler |
| Server submission | Explicit review and consent; local-rule route; idempotent case/event keys; bounded WorkManager retries | Payloads checked against current API schema; actual Android network execution unverified |
| Multi-event cases | Open prior check and explicitly append context; choosing a separate notification starts a new case | Source reviewed |
| Assessment display | Server headline, next action, evidence quotes/offsets, clarification, processing state, limitations | Response fields checked against API engine |
| Credential storage | AES-GCM/Keystore; no-backup private files; no tokens/text in WorkManager inputs; no redirect following | Source reviewed; device Keystore and lifecycle behavior unverified |
| Deletion | Local erase, disconnect, cancellation, and epoch guard against restoring erased records | Source reviewed; in-flight request can already have reached server |
| Alerts | Reviewable server guidance inside the app; no unsolicited notification alerts or full-conversation monitoring | Deliberate current scope; backend controls concern revisions |
| Cloud/research consent | No cloud request or report contribution from companion | Users use the web app for separate contribution/review workflow |
| Live payment handoff | Disabled; fields inspected only | No payment capability claimed |

## Reproducible build configuration

Gradle 8.11.1 wrapper (official SHA-256 verified), AGP 8.9.2, Kotlin 2.1.20, API 35, min API 26, JVM target 17. The checked-in Gradle wrapper JAR hash and distribution checksum match the [official Gradle reference](https://gradle.org/release-checksums/). [Android's AGP 8.9 compatibility table](https://developer.android.com/build/releases/agp-8-9-0-release-notes) requires Gradle 8.11.1, SDK Build Tools 35.0.0, and JDK 17 as its baseline.

Use `apps/android/README.md` for setup and exact commands. Existing `InputBoundaryTest.kt` covers encoded duplicate payment parameters, unsupported payment inputs, changed payment digests, server origin restrictions, bounded stream reads, and notification credential masking. Do not report these Gradle tests as passed until run with the Android SDK.

Completed local checks: `PaymentRequest.kt` and `NotificationText.kt` compiled with the locally available Kotlin 2.3.0 compiler/JDK 21 and passed a standalone JVM smoke run (valid fields, ten malformed/unsupported payment inputs, changed recipient/amount digests, and three credential-masking examples). All four Android XML files parsed successfully, and the wrapper JAR digest matched the official value. These checks cover portable input logic and file integrity only; they do not compile Android classes, run the pinned Gradle/JUnit suite, or establish APK/device compatibility.

## Remaining device acceptance checks

1. Install debug build on emulator and one physical API 26+ device; confirm controls remain visible with keyboard, system bars, and large fonts.
2. Share text and each supported image MIME type; cancel image picking; try malformed/oversized inputs; review OCR edits and inspect the request to verify discarded text never appears in provenance.
3. Connect to the local API through emulator or USB loopback, then test HTTPS; assert redirects and unauthorized tokens fail without leaking credentials.
4. Disconnect networking, queue consented synthetic input, reconnect, and check one logical case/event despite retry. Change credentials while an upload is queued; confirm it cannot upload under a new identity.
5. Grant OS notification permission with an empty or disabled allowlist; confirm no preview. Add one synthetic test app, update/remove its notification, pause, revoke OS access, then erase. Confirm unselected apps and raw obvious credentials are not retained.
6. Delete a queued local record while work is running; confirm it is not restored. Separately delete a submitted server case in the web UI.
7. Review release manifest/network behavior and sign an artifact only after build, lint, unit, and device checks pass.

No measured live detection accuracy, real-time background SLA, recipient identity verification, bank integration, or platform distribution approval is implied by this source implementation.
