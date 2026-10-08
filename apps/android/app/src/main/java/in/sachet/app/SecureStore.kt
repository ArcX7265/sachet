package `in`.sachet.app

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.security.KeyStore
import java.util.UUID
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

/** Private encrypted files keep text and tokens out of WorkManager's unencrypted input DB. */
class SecureStore(context: Context) {
    private val directory = File(context.noBackupFilesDir, "sachet").apply { mkdirs() }

    private fun key(): SecretKey {
        val keystore = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (keystore.getKey(KEY_ALIAS, null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder(KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true).build())
        }.generateKey()
    }

    fun read(name: String): JSONObject? = synchronized(LOCK) {
        require(name.matches(Regex("[a-zA-Z0-9_-]{1,100}")))
        val file = AtomicFile(File(directory, "$name.bin"))
        if (!file.baseFile.exists()) return@synchronized null
        val encoded = file.readFully()
        require(encoded.size in 29..2_000_000) { "Local record is unavailable." }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, encoded.copyOfRange(0, 12)))
        cipher.updateAAD(name.toByteArray(Charsets.UTF_8))
        JSONObject(String(cipher.doFinal(encoded.copyOfRange(12, encoded.size)), Charsets.UTF_8))
    }

    fun write(name: String, value: JSONObject) = synchronized(LOCK) {
        require(name.matches(Regex("[a-zA-Z0-9_-]{1,100}")))
        val plain = value.toString().toByteArray(Charsets.UTF_8)
        require(plain.size <= 1_900_000) { "Local record is too large." }
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        cipher.updateAAD(name.toByteArray(Charsets.UTF_8))
        val atomic = AtomicFile(File(directory, "$name.bin"))
        val stream = atomic.startWrite()
        try {
            stream.write(cipher.iv + cipher.doFinal(plain))
            atomic.finishWrite(stream)
        } catch (error: Exception) {
            atomic.failWrite(stream)
            throw error
        }
    }

    fun settings(): JSONObject = synchronized(LOCK) {
        read("settings") ?: JSONObject()
            .put("endpoint", if (BuildConfig.DEBUG) "http://10.0.2.2:8000" else "")
            .put("token", "")
            .put("epoch", UUID.randomUUID().toString())
            .put("notifications_enabled", false)
            .put("paused", true)
            .put("allowlist", JSONArray())
            .also { write("settings", it) }
    }

    fun updateSettings(change: (JSONObject) -> Unit) = synchronized(LOCK) {
        val current = settings()
        change(current)
        write("settings", current)
    }

    /** Keep a cancelled/deleted upload from restoring content after a connection change or erase. */
    fun writeIfCurrent(name: String, value: JSONObject, epoch: String): Boolean = synchronized(LOCK) {
        if (settings().getString("epoch") != epoch || read(name) == null) return@synchronized false
        write(name, value)
        true
    }

    fun records(prefix: String): List<Pair<String, JSONObject>> = synchronized(LOCK) {
        directory.listFiles().orEmpty().filter { it.name.startsWith(prefix) && it.extension == "bin" }
            .mapNotNull { file -> runCatching { file.nameWithoutExtension to read(file.nameWithoutExtension)!! }.getOrNull() }
            .filter { (name, value) ->
                if (name.startsWith("notice_") && value.optLong("created_at") < System.currentTimeMillis() - 86_400_000L) {
                    delete(name)
                    false
                } else true
            }
            .sortedByDescending { it.second.optLong("created_at") }
    }

    fun delete(name: String) = synchronized(LOCK) {
        require(name.matches(Regex("[a-zA-Z0-9_-]{1,100}")))
        AtomicFile(File(directory, "$name.bin")).delete()
    }

    fun clearLocal() = synchronized(LOCK) {
        directory.listFiles().orEmpty().forEach { it.delete() }
        settings() // A new epoch prevents a running worker from restoring old results.
    }

    fun saveNotification(record: JSONObject) = synchronized(LOCK) {
        val config = settings()
        val allowlist = config.optJSONArray("allowlist") ?: return@synchronized
        if (!config.optBoolean("notifications_enabled") || config.optBoolean("paused", true) ||
            !(0 until allowlist.length()).any { allowlist.optString(it) == record.optString("package") }) return@synchronized
        val name = "notice_${record.getString("key_digest")}"
        val previous = read(name)
        if (previous?.optString("content_digest") == record.optString("content_digest")) return@synchronized
        record.put("first_seen_at", previous?.optLong("first_seen_at") ?: System.currentTimeMillis())
        record.put("updated", previous != null)
        write(name, record)
        val expiry = System.currentTimeMillis() - 24 * 60 * 60 * 1000L
        records("notice_").forEachIndexed { index, entry ->
            if (index >= 50 || entry.second.optLong("created_at") < expiry) delete(entry.first)
        }
    }

    companion object {
        private val LOCK = Any()
        private const val KEY_ALIAS = "sachet-local-v1"
    }
}
