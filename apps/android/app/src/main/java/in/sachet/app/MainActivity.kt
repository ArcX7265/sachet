package `in`.sachet.app

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.graphics.BitmapFactory
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Bundle
import android.provider.Settings
import android.text.InputFilter
import android.text.InputType
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.*
import androidx.work.WorkManager
import com.google.android.gms.tasks.Tasks
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import com.google.mlkit.vision.text.TextRecognition
import com.google.mlkit.vision.text.latin.TextRecognizerOptions
import org.json.JSONArray
import org.json.JSONObject
import java.time.Instant
import java.util.UUID
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class MainActivity : Activity() {
    private lateinit var store: SecureStore
    private lateinit var container: LinearLayout
    private val executor = Executors.newSingleThreadExecutor()
    private var selectedTab = "Check"
    private var draft = ""
    private var draftOriginal = ""
    private var source = "share"
    private var sourceTime = Instant.now().toString()
    private var provenance = JSONObject()
    private var paymentRaw = ""
    private var activeCase = ""
    private var textInput: EditText? = null
    private var paymentInput: EditText? = null
    private var imageBusy = false
    private var imageGeneration = 0
    private val green = Color.rgb(22, 105, 75)
    private val ink = Color.rgb(28, 35, 31)
    private val muted = Color.rgb(99, 110, 105)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_SECURE)
        store = SecureStore(this)
        if (!acceptShare(intent)) render()
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        if (!acceptShare(intent)) render()
    }

    override fun onDestroy() { executor.shutdown(); super.onDestroy() }

    private fun acceptShare(incoming: Intent): Boolean {
        if (incoming.action != Intent.ACTION_SEND) return false
        imageGeneration++ // Ignore an older OCR result after a new share arrives.
        imageBusy = false
        activeCase = ""
        draft = ""
        draftOriginal = ""
        paymentRaw = ""
        provenance = JSONObject().put("entry", "android_share").put("sender_identity_verified", false)
        sourceTime = Instant.now().toString()
        source = "share"
        selectedTab = "Check"
        if (incoming.type == "text/plain") {
            draft = incoming.getCharSequenceExtra(Intent.EXTRA_TEXT)?.toString().orEmpty().take(16000)
            draftOriginal = draft
            provenance.put("input_may_be_truncated", incoming.getCharSequenceExtra(Intent.EXTRA_TEXT)?.length?.let { it > 16000 } ?: false)
            if (draft.trim().startsWith("upi://")) { paymentRaw = draft.trim(); draft = "" }
            render()
            return true
        }
        if (incoming.type in setOf("image/png", "image/jpeg", "image/webp")) {
            @Suppress("DEPRECATION") val uri = incoming.getParcelableExtra<Uri>(Intent.EXTRA_STREAM)
            render()
            if (uri == null) toast("No shared image was supplied.") else extractImage(uri)
            return true
        }
        render()
        toast("Share plain text or a PNG, JPEG, or WebP image.")
        return true
    }

    private fun render() {
        textInput = null
        paymentInput = null
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(Color.WHITE)
            fitsSystemWindows = true
            setPadding(dp(22), dp(18), dp(22), dp(12))
        }
        setContentView(root)
        root.addView(TextView(this).apply {
            text = "sachet."
            textSize = 29f
            setTextColor(ink)
            setTypeface(typeface, Typeface.BOLD)
            setPadding(0, 0, 0, dp(2))
        })
        root.addView(TextView(this).apply { text = "A clearer moment before you act"; textSize = 13f; setTextColor(muted) })
        val nav = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, dp(18), 0, dp(8)) }
        for (label in listOf("Check", "Inbox", "Settings")) {
            nav.addView(Button(this).apply {
                text = label; isAllCaps = false; textSize = 13f
                setTextColor(if (selectedTab == label) Color.WHITE else ink)
                background = rounded(if (selectedTab == label) green else Color.rgb(245, 247, 245))
                setOnClickListener { captureDraft(); selectedTab = label; render() }
            }, LinearLayout.LayoutParams(0, dp(42), 1f).apply { marginEnd = dp(5) })
        }
        root.addView(nav)
        val config = store.settings()
        if (config.optBoolean("notifications_enabled")) {
            root.addView(TextView(this).apply {
                text = if (config.optBoolean("paused", true)) "Notification previews paused · tap to resume" else "Selected notification previews on · tap to pause"
                textSize = 12f; setTextColor(green); setPadding(0, dp(8), 0, dp(10))
                setOnClickListener { store.updateSettings { it.put("paused", !it.optBoolean("paused", true)) }; captureDraft(); render() }
            })
        }
        val scroll = ScrollView(this).apply { isFillViewport = true }
        container = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(0, dp(10), 0, dp(24)) }
        scroll.addView(container)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        when (selectedTab) { "Check" -> checkScreen(); "Inbox" -> inboxScreen(); else -> settingsScreen() }
    }

    private fun checkScreen() {
        heading(if (activeCase.isBlank()) "Check a financial request" else "Add context to your case")
        paragraph("Share the claims and requested actions you want help understanding. Review the text before sending it to your Sachet server.")
        if (activeCase.isNotBlank()) {
            note("Continuing case ${activeCase.take(12)}…")
            button("Start a separate case", false) { activeCase = ""; captureDraft(); render() }
        }
        val goal = field("What are you trying to do? (optional)", "For example: withdraw my investment", 160)
        textInput = field("Conversation or request", "Paste or share relevant English text", 16000, true).apply { setText(draft) }
        if (source == "ocr") note("Text extracted on this device. Check names, amounts, and missing lines. Only reviewed text and extraction references are sent.")
        if (source == "notification") note("Notification preview: may be incomplete, updated, or missing your replies. Source app identity does not verify the sender.")
        button(if (imageBusy) "Reading image on device…" else "Choose a screenshot or QR image", false) {
            if (!imageBusy) startActivityForResult(Intent(Intent.ACTION_GET_CONTENT).apply {
                type = "image/*"; putExtra(Intent.EXTRA_MIME_TYPES, arrayOf("image/png", "image/jpeg", "image/webp")); addCategory(Intent.CATEGORY_OPENABLE)
            }, IMAGE_REQUEST)
        }
        paymentInput = field("Payment request (optional)", "upi://pay?pa=…", 4096).apply { setText(paymentRaw) }
        button("Inspect payment fields", false) {
            try { showDialog("Payment request", PaymentRequest.parse(paymentInput!!.text.toString().trim()).summary() +
                "\n\nPayment handoff is disabled pending provider and device validation.") }
            catch (error: Exception) { toast(error.message ?: "Unable to parse payment request.") }
        }
        val synthetic = CheckBox(this).apply { text = "This is a synthetic demonstration example"; textSize = 13f; setTextColor(ink) }
        container.addView(synthetic)
        val consent = CheckBox(this).apply { text = "I reviewed this content and agree to send it to my configured Sachet server"; textSize = 13f; setTextColor(ink) }
        container.addView(consent)
        note("Private checks use the server's limited local detector. This companion does not request cloud model processing or contribute your case for research. Remove PINs, OTPs, and unrelated private content.")
        button("Review and check", true) {
            captureDraft()
            if (!consent.isChecked) { toast("Review the content and confirm submission first."); return@button }
            val config = store.settings()
            if (config.optString("token").isBlank()) { toast("Connect to your server in Settings first."); return@button }
            try {
                var submitted = draft.trim()
                val data = JSONObject(provenance.toString()).put("reviewed_on_device", true)
                    .put("user_edited_extraction", draft != draftOriginal).put("coverage", "user_selected_partial_context")
                if (paymentRaw.isNotBlank()) {
                    val payment = PaymentRequest.parse(paymentRaw.trim())
                    submitted += "\n\nUser-supplied payment request:\n${payment.raw}"
                    data.put("payment_request_digest", payment.digest).put("payment_fields_unverified", true)
                }
                require(submitted.isNotBlank() && submitted.length <= 16000) { "Supply 1–16000 characters in total, including payment details." }
                require(store.records("upload_").count { it.second.optString("status") != "submitted" } < 30) { "Review pending submissions in Inbox before adding more." }
                val eventId = UUID.randomUUID().toString()
                val recordName = "upload_$eventId"
                val record = JSONObject().put("event_id", eventId).put("epoch", config.getString("epoch"))
                    .put("endpoint", config.getString("endpoint")).put("title", "Android financial request")
                    .put("goal", goal.text.toString().trim()).put("case_id", activeCase)
                    .put("data_class", if (synthetic.isChecked) "synthetic" else "private")
                    .put("text", submitted).put("source_type", source).put("observed_at", sourceTime)
                    .put("provenance", data).put("created_at", System.currentTimeMillis()).put("status", "queued")
                store.write(recordName, record)
                UploadWorker.enqueue(this, recordName)
                draft = ""; paymentRaw = ""; draftOriginal = ""; provenance = JSONObject(); activeCase = ""
                selectedTab = "Inbox"; render()
            } catch (error: Exception) { toast(error.message ?: "Unable to queue this request.") }
        }
        button("Try a labelled example", false) {
            draft = "I want to withdraw the balance shown in my investment account.\nSupport: Your withdrawal is approved. First transfer a refundable verification deposit to this personal UPI address. Do it now or your account will be locked."
            draftOriginal = draft; source = "share"; provenance = JSONObject().put("synthetic_example", true)
            sourceTime = Instant.now().toString(); render()
            // The checkbox still requires an explicit choice so its meaning remains visible.
            toast("Synthetic example loaded. Mark it as a demonstration before submitting.")
        }
        note("Sachet assesses available evidence. It cannot authenticate a sender or guarantee that a transaction is safe.")
    }

    private fun inboxScreen() {
        heading("Your checks")
        paragraph("Queued checks resume when a connection is available. Open a check to refresh its assessment; background delivery timing depends on Android.")
        button("Refresh inbox", false) { render() }
        val uploads = store.records("upload_")
        if (uploads.isEmpty()) note("Your reviewed submissions will appear here.")
        uploads.take(30).forEach { (name, record) ->
            val card = card()
            card.addView(text("${record.optString("status").replace('_', ' ')} · ${record.optString("data_class")}", 12f, green))
            card.addView(text(record.optString("text").take(110), 15f, ink))
            addButton(card, "Open check") { showRecord(name, record) }
        }
        heading("Notification previews")
        note("Only explicitly allowed apps are retained locally, for up to 24 hours and 50 entries. Nothing is uploaded until you select, review, and submit it.")
        val expiry = System.currentTimeMillis() - 24 * 60 * 60 * 1000L
        val previews = store.records("notice_").filter { (_, notice) -> notice.optLong("created_at") >= expiry }
        if (previews.isEmpty()) note("No selected notification previews. Optional access is in Settings.")
        previews.forEach { (name, notice) ->
            val card = card()
            card.addView(text(notice.getString("package") + if (notice.optBoolean("removed")) " · removed by source" else if (notice.optBoolean("updated")) " · updated" else "", 11f, muted))
            card.addView(text(notice.optString("title"), 15f, ink))
            card.addView(text(notice.optString("text").take(250), 13f, muted))
            addButton(card, "Review this preview") {
                activeCase = "" // Choosing a new preview must not silently attach it to an unrelated case.
                draft = notice.optString("title") + "\n" + notice.getString("text")
                draftOriginal = draft; source = "notification"; sourceTime = notice.getString("observed_at")
                provenance = JSONObject().put("package", notice.getString("package"))
                    .put("notification_key_digest", notice.getString("key_digest"))
                    .put("posted_at_ms", notice.optLong("posted_at"))
                    .put("updated", notice.optBoolean("updated")).put("removed", notice.optBoolean("removed"))
                    .put("sender_identity_verified", false).put("notification_fields_may_be_partial", true)
                selectedTab = "Check"; render()
            }
            addButton(card, "Discard") { store.delete(name); render() }
        }
    }

    private fun showRecord(name: String, record: JSONObject) {
        selectedTab = "Inbox"
        container.removeAllViews()
        heading("Your assessment")
        note("${record.optString("status")} · ${record.optString("data_class")} · ${record.optString("message")}")
        val result = record.optJSONObject("result")
        if (result != null) showAssessment(result)
        else paragraph("An assessment is not available yet. Queued or failed requests do not mean no concern was found.")
        val caseId = record.optString("case_id")
        if (caseId.isNotBlank()) {
            note("Case: $caseId")
            button("Refresh assessment", true) {
                val config = store.settings()
                if (config.optString("endpoint") != record.optString("endpoint") || config.optString("epoch") != record.optString("epoch")) {
                    toast("This check belongs to a different connection."); return@button
                }
                background({ ApiClient(config.getString("endpoint"), config.getString("token")).request("GET", "/v1/cases/$caseId") }) { response ->
                    store.read(name)?.let { latest ->
                        latest.put("result", response); store.write(name, latest); showRecord(name, latest)
                    }
                }
            }
            button("Add more context to this case", false) { activeCase = caseId; draft = ""; draftOriginal = ""; paymentRaw = ""; source = "share"; sourceTime = Instant.now().toString(); provenance = JSONObject(); selectedTab = "Check"; render() }
        }
        if (record.optString("status") in setOf("failed", "needs_connection")) button("Retry this submission", false) {
            record.put("status", "queued"); store.write(name, record); UploadWorker.enqueue(this, name); render()
        }
        button("Remove local copy", false) {
            AlertDialog.Builder(this).setTitle("Remove this local copy?")
                .setMessage("This cancels pending work on this phone. Content already sent remains on your server; delete the case in the web app to remove it there.")
                .setPositiveButton("Remove") { _, _ -> WorkManager.getInstance(this).cancelUniqueWork(name); store.delete(name); render() }
                .setNegativeButton("Keep", null).show()
        }
        button("Back to inbox", false) { render() }
    }

    private fun showAssessment(result: JSONObject) {
        val assessment = result.optJSONObject("assessment")
        if (assessment == null) { paragraph("Assessment is waiting for processing. Refresh to check again."); return }
        note("${assessment.optString("processing_status", "unknown")} · ${assessment.optString("engine", "engine not provided")}")
        heading(assessment.optString("headline", "Assessment pending"))
        paragraph(assessment.optString("next_action", "Add relevant context or independently verify the request."))
        val concerns = assessment.optJSONArray("concerns") ?: JSONArray()
        for (index in 0 until concerns.length()) {
            val concern = concerns.getJSONObject(index)
            paragraph(concern.optString("description"))
            val evidence = concern.optJSONArray("evidence") ?: JSONArray()
            for (item in 0 until evidence.length()) {
                val citation = evidence.getJSONObject(item)
                note("“${citation.optString("quote") }”\nSource ${citation.optString("event_id").take(16)} · ${citation.optInt("start")}–${citation.optInt("end")}")
            }
        }
        val limitations = assessment.optJSONArray("limitations")
        if (limitations != null) for (index in 0 until limitations.length()) note(limitations.optString(index))
        if (!assessment.isNull("clarification")) assessment.optString("clarification").takeIf { it.isNotBlank() }?.let { note("Clarification: $it") }
        note("Assessment revision ${result.optInt("revision")}. You can add a correction as new case context, or use the web app's targeted correction controls.")
    }

    private fun settingsScreen() {
        heading("Your connection")
        paragraph("Connect to the Sachet server you trust. Credentials and pending content are encrypted using Android's protected key store.")
        val config = store.settings()
        val endpoint = field("Server origin", "https://sachet.example", 300).apply { setText(config.optString("endpoint")); inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_URI }
        val token = field("Access token", "Leave blank to keep the saved token", 2048).apply {
            inputType = InputType.TYPE_CLASS_TEXT or InputType.TYPE_TEXT_VARIATION_PASSWORD
            importantForAutofill = View.IMPORTANT_FOR_AUTOFILL_NO
        }
        button("Save connection", true) {
            try {
                val address = endpoint.text.toString().trim().trimEnd('/')
                ApiClient.validateEndpoint(address, BuildConfig.DEBUG)
                store.updateSettings {
                    val replacementToken = token.text.toString().trim()
                    if (address != it.optString("endpoint") || (replacementToken.isNotBlank() && replacementToken != it.optString("token"))) {
                        it.put("epoch", UUID.randomUUID().toString()).put("token", "")
                    }
                    it.put("endpoint", address)
                    if (replacementToken.isNotBlank()) it.put("token", replacementToken)
                }
                token.text.clear(); toast("Connection saved.")
            } catch (error: Exception) { toast(error.message ?: "Invalid connection.") }
        }
        button("Create a demo session on this server", false) {
            val address = endpoint.text.toString().trim().trimEnd('/')
            background({ ApiClient(address, "").request("POST", "/v1/sessions", JSONObject().put("role", "user")) }) { response ->
                store.updateSettings {
                    it.put("endpoint", address).put("token", response.getString("token")).put("epoch", UUID.randomUUID().toString())
                }
                token.text.clear(); toast("Demo session connected. Use synthetic examples.")
            }
        }
        note("The demo session endpoint works only when the server enables demo mode. Live deployments require provisioned authentication. This app never stores bank credentials.")
        heading("Optional notification previews")
        paragraph("Choose exact Android app package names. The listener stores a local preview from those apps only. It cannot see full conversations, outgoing replies, or hidden content.")
        val packages = field("Allowed app packages, one per line", "Add only the apps you want to review", 1500, true).apply {
            val list = config.optJSONArray("allowlist") ?: JSONArray()
            setText((0 until list.length()).joinToString("\n") { list.getString(it) })
        }
        val enabled = Switch(this).apply { text = "Allow local notification previews"; isChecked = config.optBoolean("notifications_enabled"); setPadding(0, dp(12), 0, dp(12)); setTextColor(ink) }
        container.addView(enabled)
        button("Save notification choices", false) {
            val list = packages.text.toString().split(Regex("[\\s,]+" )).filter { it.isNotBlank() }.distinct()
            if (list.size > 15 || list.any { !it.matches(Regex("[A-Za-z][A-Za-z0-9_]*(\\.[A-Za-z0-9_]+)+")) || it == packageName }) {
                toast("Choose at most 15 valid package names; Sachet cannot listen to itself."); return@button
            }
            if (enabled.isChecked && list.isEmpty()) { toast("Add at least one allowed app."); return@button }
            store.updateSettings { it.put("allowlist", JSONArray(list)); it.put("notifications_enabled", enabled.isChecked); it.put("paused", !enabled.isChecked) }
            render()
        }
        button("Open Android notification access", false) { startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)) }
        note("Android permission and the choices above are both required. Permission alone does not enable capture. Alerts may be hidden or delayed by Android or the source app.")
        heading("Local privacy")
        button("Erase local content and disconnect", false) {
            AlertDialog.Builder(this).setTitle("Erase this phone's Sachet data?")
                .setMessage("This cancels pending uploads, erases local previews and tokens, and pauses capture. Already submitted server cases remain; remove them separately in the web app.")
                .setPositiveButton("Erase local data") { _, _ ->
                    WorkManager.getInstance(this).cancelAllWorkByTag("sachet_upload")
                    imageGeneration++; imageBusy = false
                    store.clearLocal(); draft = ""; paymentRaw = ""; provenance = JSONObject(); activeCase = ""; render()
                }.setNegativeButton("Cancel", null).show()
        }
        note("Live payment handoff is disabled in this build. No automatic payments, accessibility access, microphone access, or SMS database access is requested.")
    }

    @Deprecated("Legacy picker works on all supported devices")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == IMAGE_REQUEST && resultCode == RESULT_OK) data?.data?.let { captureDraft(); extractImage(it) }
    }

    private fun extractImage(uri: Uri) {
        if (imageBusy) return
        if (uri.scheme != "content") { toast("Choose an image from an Android content provider."); return }
        imageBusy = true
        val generation = ++imageGeneration
        executor.execute {
            val result = runCatching {
                val mime = contentResolver.getType(uri)
                require(mime in setOf("image/png", "image/jpeg", "image/webp")) { "Choose a PNG, JPEG, or WebP image." }
                val bytes = contentResolver.openInputStream(uri)?.use { readLimited(it, 10_000_000) }
                    ?: error("The source did not grant access to this image.")
                val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
                require(bounds.outWidth > 0 && bounds.outHeight > 0 && bounds.outWidth.toLong() * bounds.outHeight <= 16_000_000) { "Image is invalid or larger than 16 megapixels." }
                require(bounds.outMimeType in setOf("image/png", "image/jpeg", "image/webp")) { "File content is not a supported image." }
                val options = BitmapFactory.Options().apply { inSampleSize = if (maxOf(bounds.outWidth, bounds.outHeight) > 3000) 2 else 1 }
                val bitmap = BitmapFactory.decodeByteArray(bytes, 0, bytes.size, options) ?: error("Image could not be decoded.")
                val image = InputImage.fromBitmap(bitmap, 0)
                val recognizer = TextRecognition.getClient(TextRecognizerOptions.DEFAULT_OPTIONS)
                val scanner = BarcodeScanning.getClient(BarcodeScannerOptions.Builder().setBarcodeFormats(Barcode.FORMAT_QR_CODE).build())
                try {
                    val recognition = Tasks.await(recognizer.process(image), 30, TimeUnit.SECONDS)
                    val barcodes = Tasks.await(scanner.process(image), 30, TimeUnit.SECONDS)
                    val regions = JSONArray()
                    recognition.textBlocks.take(40).forEach { block ->
                        val box = block.boundingBox
                        // Original OCR text may contain details the user removes during review.
                        // Preserve geometry only; upload exactly the reviewed editor text.
                        regions.put(JSONObject().put("left", box?.left).put("top", box?.top)
                            .put("right", box?.right).put("bottom", box?.bottom))
                    }
                    JSONObject().put("text", recognition.text.take(16000))
                        .put("regions", regions).put("image_ref", UUID.randomUUID().toString())
                        .put("coordinate_width", bitmap.width).put("coordinate_height", bitmap.height)
                        .put("qr_values", JSONArray(barcodes.mapNotNull { it.rawValue?.take(4096) }.take(5)))
                } finally { recognizer.close(); scanner.close(); bitmap.recycle() }
            }
            runOnUiThread {
                if (isFinishing || isDestroyed || generation != imageGeneration) return@runOnUiThread
                imageBusy = false
                result.onSuccess { extracted ->
                    draft = extracted.getString("text"); draftOriginal = draft; source = "ocr"; sourceTime = Instant.now().toString()
                    provenance = JSONObject().put("local_ocr", true).put("image_ref", extracted.getString("image_ref"))
                        .put("ocr_regions", extracted.getJSONArray("regions"))
                        .put("coordinate_width", extracted.getInt("coordinate_width")).put("coordinate_height", extracted.getInt("coordinate_height"))
                        .put("original_image_uploaded", false).put("orientation_requires_review", true)
                    val qr = extracted.getJSONArray("qr_values")
                    paymentRaw = if (qr.length() == 1 && qr.optString(0).startsWith("upi://pay?")) qr.optString(0) else ""
                    selectedTab = "Check"; render()
                    if (qr.length() > 1) showDialog("Multiple QR values", "Review which request belongs to this interaction. None was selected automatically.\n\n" + (0 until qr.length()).joinToString("\n\n") { qr.getString(it) })
                    else if (qr.length() == 1 && paymentRaw.isBlank()) showDialog("QR content", "This QR uses an unsupported payment scheme. It will not be opened.\n\n${qr.getString(0)}")
                    if (draft.isBlank() && paymentRaw.isBlank()) toast("No readable text or supported payment QR found. Try a clearer image.")
                }.onFailure { toast(it.message ?: "Could not read the image. Share text or try a clearer screenshot.") }
            }
        }
    }

    private fun captureDraft() { textInput?.let { draft = it.text.toString() }; paymentInput?.let { paymentRaw = it.text.toString() } }
    private fun <T> background(work: () -> T, success: (T) -> Unit) {
        toast("Connecting…")
        executor.execute {
            val result = runCatching(work)
            runOnUiThread {
                if (isFinishing || isDestroyed) return@runOnUiThread
                result.onSuccess(success).onFailure { toast(it.message ?: "Connection failed.") }
            }
        }
    }
    private fun field(label: String, placeholder: String, max: Int, multiline: Boolean = false): EditText {
        container.addView(text(label, 12f, muted).apply { setPadding(0, dp(15), 0, dp(5)) })
        return EditText(this).apply {
            hint = placeholder; textSize = 15f; setTextColor(ink); setHintTextColor(Color.rgb(140, 148, 143))
            setPadding(dp(12), dp(10), dp(12), dp(10)); background = rounded(Color.rgb(248, 249, 248), Color.rgb(225, 231, 227))
            filters = arrayOf(InputFilter.LengthFilter(max)); gravity = Gravity.TOP or Gravity.START
            inputType = InputType.TYPE_CLASS_TEXT or if (multiline) InputType.TYPE_TEXT_FLAG_MULTI_LINE else 0
            if (multiline) minLines = 4 else setSingleLine(true)
            importantForAutofill = View.IMPORTANT_FOR_AUTOFILL_NO
        }.also { container.addView(it, LinearLayout.LayoutParams(-1, -2)) }
    }
    private fun card(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL; background = rounded(Color.rgb(248, 250, 248), Color.rgb(230, 235, 231)); setPadding(dp(14), dp(12), dp(14), dp(10))
    }.also { container.addView(it, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(12) }) }
    private fun heading(value: String) { container.addView(text(value, 23f, ink).apply { setTypeface(typeface, Typeface.BOLD); setPadding(0, dp(14), 0, dp(8)) }) }
    private fun paragraph(value: String) { if (value.isNotBlank()) container.addView(text(value, 15f, ink).apply { setPadding(0, dp(4), 0, dp(10)) }) }
    private fun note(value: String) { if (value.isNotBlank()) container.addView(text(value, 12f, muted).apply { setPadding(0, dp(7), 0, dp(7)) }) }
    private fun text(value: String, size: Float, color: Int) = TextView(this).apply { text = value; textSize = size; setTextColor(color); setLineSpacing(dp(3).toFloat(), 1f) }
    private fun button(label: String, primary: Boolean, click: () -> Unit) { addButton(container, label, primary, click) }
    private fun addButton(parent: LinearLayout, label: String, primary: Boolean = false, click: () -> Unit) {
        parent.addView(Button(this).apply {
            text = label; textSize = 14f; isAllCaps = false; setTextColor(if (primary) Color.WHITE else green)
            background = rounded(if (primary) green else Color.rgb(240, 246, 241)); setPadding(dp(12), dp(6), dp(12), dp(6))
            setOnClickListener { click() }
        }, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(10); bottomMargin = dp(2) })
    }
    private fun rounded(fill: Int, stroke: Int? = null) = GradientDrawable().apply {
        shape = GradientDrawable.RECTANGLE; cornerRadius = dp(10).toFloat(); setColor(fill); if (stroke != null) setStroke(dp(1), stroke)
    }
    private fun showDialog(title: String, body: String) { AlertDialog.Builder(this).setTitle(title).setMessage(body).setPositiveButton("Close", null).show() }
    private fun toast(message: String) { Toast.makeText(this, message.take(240), Toast.LENGTH_LONG).show() }
    private fun dp(value: Int) = (resources.displayMetrics.density * value).toInt()
    companion object { private const val IMAGE_REQUEST = 20 }
}
