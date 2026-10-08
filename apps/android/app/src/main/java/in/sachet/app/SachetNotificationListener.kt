package `in`.sachet.app

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import org.json.JSONObject
import java.time.Instant

/** Captures only a local preview. No network request or worker is started by this service. */
class SachetNotificationListener : NotificationListenerService() {
    override fun onNotificationPosted(sbn: StatusBarNotification) {
        if (sbn.packageName == packageName) return
        runCatching {
            val store = SecureStore(this)
            val config = store.settings()
            if (!config.optBoolean("notifications_enabled") || config.optBoolean("paused", true)) return
            val allowlist = config.optJSONArray("allowlist") ?: return
            val permitted = (0 until allowlist.length()).any { allowlist.getString(it) == sbn.packageName }
            if (!permitted || sbn.notification.flags and Notification.FLAG_GROUP_SUMMARY != 0) return
            val extras = sbn.notification.extras
            val title = redactNotificationCredentials(extras.getCharSequence(Notification.EXTRA_TITLE)?.toString().orEmpty().take(200))
            val text = (extras.getCharSequence(Notification.EXTRA_BIG_TEXT)
                ?: extras.getCharSequence(Notification.EXTRA_TEXT))?.toString().orEmpty().take(4000)
            if (text.isBlank()) return
            // Do not retain obvious one-time credentials in the notification preview.
            val sanitized = redactNotificationCredentials(text)
            val digest = sha256(sbn.key)
            store.saveNotification(JSONObject()
                .put("key_digest", digest).put("content_digest", sha256(title + "\n" + sanitized))
                .put("package", sbn.packageName).put("title", title).put("text", sanitized)
                .put("created_at", System.currentTimeMillis()).put("posted_at", sbn.postTime)
                .put("observed_at", Instant.now().toString()).put("removed", false))
        } // A malformed external notification must never crash the service or expose content in logs.
    }

    override fun onNotificationRemoved(sbn: StatusBarNotification) {
        if (sbn.packageName == packageName) return
        runCatching {
            val store = SecureStore(this)
            val name = "notice_${sha256(sbn.key)}"
            val record = store.read(name) ?: return
            record.put("removed", true).put("removed_at", System.currentTimeMillis())
            store.write(name, record)
        }
    }
}
