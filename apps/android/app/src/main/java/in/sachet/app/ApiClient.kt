package `in`.sachet.app

import org.json.JSONObject
import java.io.IOException
import java.io.ByteArrayOutputStream
import java.io.InputStream
import java.net.HttpURLConnection
import java.net.URI
import java.net.URL

class ApiException(val status: Int, message: String) : IOException(message)

class ApiClient(private val endpoint: String, private val token: String) {
    init { validateEndpoint(endpoint, BuildConfig.DEBUG) }

    fun request(method: String, path: String, body: JSONObject? = null): JSONObject {
        require(path.startsWith("/v1/") || path == "/health")
        val connection = URL(endpoint.trimEnd('/') + path).openConnection() as HttpURLConnection
        connection.instanceFollowRedirects = false // Never forward tokens to redirect destinations.
        connection.connectTimeout = 15_000
        connection.readTimeout = 35_000
        connection.requestMethod = method
        connection.setRequestProperty("Accept", "application/json")
        if (token.isNotBlank()) connection.setRequestProperty("Authorization", "Bearer $token")
        try {
            if (body != null) {
                connection.doOutput = true
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                connection.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            }
            val code = connection.responseCode
            if (code !in 200..299) {
                val message = when (code) {
                    401, 403 -> "Access was declined. Check your connection token."
                    409 -> "This case changed. Review the latest version before retrying."
                    422 -> "The server rejected this input. Review it and submit again."
                    429 -> "The server is busy. This submission will retry."
                    else -> "The server returned HTTP $code."
                }
                throw ApiException(code, message)
            }
            val bytes = connection.inputStream.use { readLimited(it, 1_000_000) }
            require(bytes.size <= 1_000_000) { "Server response is too large." }
            return if (bytes.isEmpty()) JSONObject() else JSONObject(String(bytes, Charsets.UTF_8))
        } finally { connection.disconnect() }
    }

    companion object {
        fun validateEndpoint(endpoint: String, debug: Boolean) {
            val uri = URI(endpoint)
            require(!uri.host.isNullOrBlank() && uri.userInfo == null && uri.fragment == null && uri.query == null &&
                uri.path.orEmpty().trim('/').isEmpty()) { "Enter a server origin without a path or credentials." }
            val localDebug = debug && uri.scheme == "http" && uri.host in setOf("10.0.2.2", "127.0.0.1", "localhost")
            require(uri.scheme == "https" || localDebug) { "Use HTTPS. Debug builds also allow emulator/loopback HTTP." }
            require(uri.port == -1 || uri.port in 1..65535) { "Invalid server port." }
        }
    }
}

fun readLimited(input: InputStream, maximum: Int): ByteArray {
    val output = ByteArrayOutputStream()
    val buffer = ByteArray(8192)
    while (true) {
        val count = input.read(buffer)
        if (count < 0) break
        require(output.size() + count <= maximum) { "Content exceeds the size limit." }
        output.write(buffer, 0, count)
    }
    return output.toByteArray()
}
