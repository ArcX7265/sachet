package `in`.sachet.app

import java.io.ByteArrayInputStream
import org.junit.Assert.*
import org.junit.Test

class InputBoundaryTest {
    @Test fun parsesPaymentWithoutTrustingStatedName() {
        val parsed = PaymentRequest.parse("upi://pay?pa=merchant%40bank&pn=Sample+Store&am=12.50&cu=INR&tn=Invoice")
        assertEquals("merchant@bank", parsed.payee)
        assertEquals("Sample Store", parsed.statedName)
        assertEquals("12.50", parsed.amount)
        assertTrue(parsed.summary().contains("do not verify"))
    }

    @Test fun rejectsAmbiguousOrUnsupportedPaymentInputs() {
        val inputs = listOf(
            "upi://pay?pa=one@bank&%70a=two@bank", // Encoded duplicate recipient.
            "upi://pay?pa=one@bank&am=-1",
            "upi://pay?pa=one@bank&am=0",
            "upi://pay?pa=one@bank&am=1.001",
            "upi://pay?pa=one@bank&am=1e3",
            "upi://pay?pa=one@bank&cu=USD",
            "upi://pay?pa=one@bank&tn=hello%0Aworld",
            "upi://pay?pa=one@bank#hidden",
            "upi://pay/other?pa=one@bank",
            "https://pay.example/?pa=one@bank"
        )
        inputs.forEach { value -> assertThrows(value, IllegalArgumentException::class.java) { PaymentRequest.parse(value) } }
    }

    @Test fun changedRecipientAmountAndPurposeInvalidateDigest() {
        val original = PaymentRequest.parse("upi://pay?pa=one@bank&am=12&tn=Invoice").digest
        assertNotEquals(original, PaymentRequest.parse("upi://pay?pa=two@bank&am=12&tn=Invoice").digest)
        assertNotEquals(original, PaymentRequest.parse("upi://pay?pa=one@bank&am=13&tn=Invoice").digest)
        assertNotEquals(original, PaymentRequest.parse("upi://pay?pa=one@bank&am=12&tn=Deposit").digest)
    }

    @Test fun endpointBoundaryAllowsOnlyTlsAndExplicitDebugLoopback() {
        ApiClient.validateEndpoint("https://api.example:443", false)
        ApiClient.validateEndpoint("http://10.0.2.2:8000", true)
        listOf("http://api.example", "https://user:secret@api.example", "https://api.example/path", "https://api.example?key=secret", "https://api.example#x").forEach {
            assertThrows(IllegalArgumentException::class.java) { ApiClient.validateEndpoint(it, true) }
        }
        assertThrows(IllegalArgumentException::class.java) { ApiClient.validateEndpoint("http://10.0.2.2:8000", false) }
        assertThrows(IllegalArgumentException::class.java) { ApiClient.validateEndpoint("http://10.0.2.2.attacker.example:8000", true) }
    }

    @Test fun readsBoundedInputAndRejectsExcess() {
        assertArrayEquals(byteArrayOf(1, 2), readLimited(ByteArrayInputStream(byteArrayOf(1, 2)), 2))
        assertThrows(IllegalArgumentException::class.java) { readLimited(ByteArrayInputStream(ByteArray(3)), 2) }
    }

    @Test fun removesCodeBeforeOrAfterCredentialLabel() {
        assertEquals("[code removed] is your OTP", redactNotificationCredentials("123456 is your OTP"))
        assertEquals("Your verification code: [code removed]", redactNotificationCredentials("Your verification code: 123456"))
        assertEquals("Invoice 123456", redactNotificationCredentials("Invoice 123456"))
    }
}
