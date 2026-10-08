package `in`.sachet.app

import android.content.Context
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.Data
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.Worker
import androidx.work.WorkerParameters
import org.json.JSONObject
import java.io.IOException
import java.time.Instant
import java.util.concurrent.TimeUnit

class UploadWorker(context: Context, parameters: WorkerParameters) : Worker(context, parameters) {
    override fun doWork(): Result {
        val name = inputData.getString("record") ?: return Result.failure()
        val store = SecureStore(applicationContext)
        val record = runCatching { store.read(name) }.getOrNull() ?: return Result.failure()
        val config = store.settings()
        val epoch = record.getString("epoch")
        if (epoch != config.getString("epoch")) return Result.failure()
        if (config.optString("token").isBlank()) return finish(store, name, record, "needs_connection", "Connect in Settings, then retry.")
        if (config.optString("endpoint") != record.optString("endpoint")) {
            return finish(store, name, record, "needs_connection", "Server changed. Review and resubmit to the new server.")
        }
        try {
            val api = ApiClient(config.getString("endpoint"), config.getString("token"))
            record.put("status", "sending").put("attempted_at", Instant.now().toString())
            if (!store.writeIfCurrent(name, record, epoch)) return Result.failure()
            var caseId = record.optString("case_id")
            if (caseId.isBlank()) {
                val created = api.request("POST", "/v1/cases", JSONObject()
                    .put("title", record.getString("title"))
                    .put("goal", record.optString("goal"))
                    .put("data_class", record.getString("data_class"))
                    .put("mode", "local")
                    .put("idempotency_key", record.getString("event_id")))
                caseId = created.getString("id")
                require(caseId.matches(Regex("[a-zA-Z0-9_-]{1,100}")))
                record.put("case_id", caseId)
                if (!stillCurrent(store, name, epoch)) return Result.failure()
                if (!store.writeIfCurrent(name, record, epoch)) return Result.failure()
            }
            require(caseId.matches(Regex("[a-zA-Z0-9_-]{1,100}")))
            val event = JSONObject()
                .put("text", record.getString("text"))
                .put("source_type", record.getString("source_type"))
                .put("idempotency_key", record.getString("event_id"))
                .put("source_event_id", record.optJSONObject("provenance")?.optString("notification_key_digest")
                    ?.takeIf { record.getString("source_type") == "notification" && it.isNotBlank() } ?: record.getString("event_id"))
                .put("observed_at", record.getString("observed_at"))
                .put("provenance", record.optJSONObject("provenance") ?: JSONObject())
            val response = api.request("POST", "/v1/cases/$caseId/events", event)
            if (!stillCurrent(store, name, epoch)) return Result.failure()
            record.put("status", "submitted").put("result", response)
                .put("submitted_at", Instant.now().toString()).put("message", "Open the result to see assessment status.")
            if (!store.writeIfCurrent(name, record, epoch)) return Result.failure()
            return Result.success()
        } catch (error: ApiException) {
            if (!stillCurrent(store, name, epoch)) return Result.failure()
            if ((error.status == 429 || error.status >= 500) && runAttemptCount < 6) {
                record.put("status", "retrying").put("message", error.message)
                if (!store.writeIfCurrent(name, record, epoch)) return Result.failure()
                return Result.retry()
            }
            return finish(store, name, record, "failed", error.message ?: "Server request failed.")
        } catch (_: IOException) {
            if (!stillCurrent(store, name, epoch)) return Result.failure()
            if (runAttemptCount >= 6) return finish(store, name, record, "failed", "Connection failed. Retry when the server is available.")
            record.put("status", "retrying").put("message", "Waiting for a working connection.")
            if (!store.writeIfCurrent(name, record, epoch)) return Result.failure()
            return Result.retry()
        } catch (_: Exception) {
            if (stillCurrent(store, name, epoch)) finish(store, name, record, "failed", "Could not complete this submission. Review the input and connection.")
            return Result.failure()
        }
    }

    private fun stillCurrent(store: SecureStore, name: String, epoch: String) =
        !isStopped && store.settings().getString("epoch") == epoch && store.read(name) != null

    private fun finish(store: SecureStore, name: String, record: JSONObject, status: String, message: String): Result {
        record.put("status", status).put("message", message)
        store.writeIfCurrent(name, record, record.getString("epoch"))
        return Result.failure()
    }

    companion object {
        fun enqueue(context: Context, name: String) {
            val request = OneTimeWorkRequestBuilder<UploadWorker>()
                .setInputData(Data.Builder().putString("record", name).build())
                .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .addTag("sachet_upload").build()
            WorkManager.getInstance(context).enqueueUniqueWork(name, ExistingWorkPolicy.KEEP, request)
        }
    }
}
