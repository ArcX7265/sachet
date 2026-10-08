# Sachet Android companion

Native Kotlin source for reviewing financial requests, selected notification previews, and payment QR fields with Sachet. The interface uses a minimal white layout with Check, Inbox, and Settings screens.

## Build status

The source, Gradle wrapper, manifest, resource files, and input boundary unit tests are included. **An APK has not been built or tested on a device in this workspace:** the Android SDK and emulator/device are unavailable. Source checks are not a substitute for an Android build. See `../../docs/android-capabilities.md` for precise capability and validation limits.

## Build on a configured Android workstation

1. Open this directory in Android Studio, or install Android SDK Platform 35 and Build Tools 35.0.0 with command-line tools. Use JDK 17 (the documented Android Gradle Plugin baseline) or a compatible JDK.
2. Set `ANDROID_HOME` to the SDK directory, or create a local, uncommitted `local.properties` containing `sdk.dir=C:/path/to/Android/Sdk`.
3. Run from this directory in PowerShell:

   ```powershell
   .\gradlew.bat :app:testDebugUnitTest :app:lintDebug :app:assembleDebug
   ```

   On macOS/Linux use `sh ./gradlew :app:testDebugUnitTest :app:lintDebug :app:assembleDebug`.
4. The debug APK is produced at `app/build/outputs/apk/debug/app-debug.apk`. Install it on an Android 8.0/API 26 or newer test device with `adb install -r app/build/outputs/apk/debug/app-debug.apk`.

The pinned toolchain is Android Gradle Plugin 8.9.2, Gradle 8.11.1, Kotlin 2.1.20, compile/target API 35, and Java bytecode 17. Dependency downloads require Google Maven, Maven Central, Gradle Plugin Portal, and the Gradle distribution host. Use the checked-in wrapper rather than a global Gradle installation.

The wrapper JAR SHA-256 is `2db75c40782f5e8ba1fc278a5574bab070adccb2d21ca5a6e5ed840888448046`; the distribution checksum is pinned in `gradle/wrapper/gradle-wrapper.properties`. Both match [Gradle's official checksum reference](https://gradle.org/release-checksums/). Compatibility is documented in the [AGP 8.9 release notes](https://developer.android.com/build/releases/agp-8-9-0-release-notes).

## Connect and demonstrate

1. Start the Sachet API using the root project's setup instructions. For an Android emulator the debug default server is `http://10.0.2.2:8000`.
2. For a USB device, run `adb reverse tcp:8000 tcp:8000` and use `http://127.0.0.1:8000` in a debug build. Other hosts require HTTPS with a trusted certificate; release builds require HTTPS everywhere.
3. In Settings, save the server origin and a provisioned user token. When the backend explicitly enables demo mode, **Create a demo session on this server** creates a synthetic-data demo connection.
4. Open Check and load the labelled example. Select the synthetic demonstration checkbox, review the content, grant submission consent, and submit. Inbox shows queue state and the server assessment, evidence quotes, limitations, and clarification.
5. Use **Add more context to this case** to demonstrate a request developing across multiple events. Share plain text from another app or select a screenshot; image OCR and QR decoding happen on the phone before review.
6. Optional notification previews require both Android's notification-access permission and an explicit package allowlist in Settings. Previews are local until the user opens one, reviews it, and submits it. Test with synthetic messages only. Pause and erase controls are in the app.

## Input and privacy boundaries

- No bank credentials, payment execution, call recording, accessibility service, SMS database permission, or payment-app interception is implemented.
- UPI parsing accepts `upi://pay` with one recipient, optional positive decimal amount, and INR. Duplicate parameters, controls, fragments, invalid recipients, and unsupported schemes are rejected. Parsed names are unverified claims. Live payment handoff is disabled.
- Text and pending uploads are encrypted with AES-GCM and an Android Keystore key in the app's no-backup directory. WorkManager stores only a record identifier. Server tokens are never written to logs or followed across HTTP redirects.
- Screenshot input is limited to PNG/JPEG/WebP, 10 MB, and 16 megapixels. On-device ML Kit extracts text and QR values. Only the reviewed text plus extraction coordinates/references are sent; original OCR block text and image bytes are not uploaded. Image orientation and OCR errors require review.
- Notification previews are limited to selected packages, deduplicated by notification key/content, best-effort credential-redacted, and kept for up to 24 hours with a 50-entry cap. Expiry is enforced on access/capture, not by an exact background timer. Notification previews cannot reconstruct full conversations or authenticate senders.
- Explicit submissions use WorkManager with network constraints and capped retries. They call the server's `local` detector route; this means processing on your configured server, not fully on-device scam detection. The Android app never requests a cloud model or contributes reports for research.
- Erasing local data cancels pending work and changes a connection epoch, preventing old workers from restoring deleted records. A request already transmitted may have reached the server; remove submitted cases through the web app separately.

## Validation still required

Run the build, unit tests, Android lint, and device smoke checks before distributing an APK. Verify share-sheet handling, API authentication and retries, OCR review, notification allowlist/pause/revocation, reboot and background delivery, duplicate notification updates, source removal, deletion during an upload, and release HTTPS behavior. Repeat notification tests on target vendors because their delivery and permission behavior vary. No Play Store approval, notification delivery guarantee, or detection accuracy is claimed.
