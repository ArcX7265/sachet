package `in`.sachet.app

import java.math.BigDecimal
import java.net.URI
import java.net.URLDecoder
import java.security.MessageDigest

data class PaymentRequest(val raw: String, val payee: String, val statedName: String,
    val amount: String?, val currency: String, val purpose: String, val digest: String) {
    fun summary(): String = "Recipient: $payee\nStated name: ${statedName.ifBlank { "Not supplied" }}\n" +
        "Amount: ${amount ?: "Not supplied"} $currency\nPurpose: ${purpose.ifBlank { "Not supplied" }}\n" +
        "These are request fields. They do not verify the recipient."

    companion object {
        fun parse(raw: String): PaymentRequest {
            require(raw.length in 1..4096) { "Payment request must be 1–4096 characters." }
            require(raw.none { it.code < 32 || it.code == 127 }) { "Control characters are not permitted." }
            val uri = URI(raw)
            require(uri.scheme?.lowercase() == "upi" && uri.rawAuthority == "pay" &&
                uri.rawPath.orEmpty().isEmpty() && uri.fragment == null) { "Only upi://pay requests are supported." }
            val fields = linkedMapOf<String, String>()
            require(!uri.rawQuery.isNullOrBlank()) { "Payment fields are missing." }
            for (part in uri.rawQuery.split("&")) {
                val split = part.split("=", limit = 2)
                require(split.size == 2) { "Malformed payment field." }
                val name = URLDecoder.decode(split[0], "UTF-8").lowercase()
                val value = URLDecoder.decode(split[1], "UTF-8")
                require(name.matches(Regex("[a-z][a-z0-9]{0,15}")) && !fields.containsKey(name)) { "Duplicate or invalid payment field." }
                require(value.none { it.code < 32 || it.code == 127 }) { "Control characters are not permitted." }
                fields[name] = value
            }
            val payee = fields["pa"].orEmpty()
            require(payee.matches(Regex("[A-Za-z0-9._-]{2,256}@[A-Za-z0-9.-]{2,64}"))) { "Recipient address is missing or malformed." }
            val currency = fields["cu"] ?: "INR"
            require(currency == "INR") { "Only INR requests are supported." }
            val amount = fields["am"]?.also {
                require(it.matches(Regex("[0-9]{1,9}(\\.[0-9]{1,2})?")) && BigDecimal(it) > BigDecimal.ZERO) { "Invalid payment amount." }
            }
            return PaymentRequest(raw, payee, fields["pn"].orEmpty(), amount, currency,
                fields["tn"].orEmpty(), sha256(raw))
        }
    }
}

fun sha256(value: String): String = MessageDigest.getInstance("SHA-256")
    .digest(value.toByteArray(Charsets.UTF_8)).joinToString("") { "%02x".format(it) }
