package `in`.sachet.app

/** Best-effort minimization before storage; it is not a complete secret detector. */
fun redactNotificationCredentials(value: String): String = value.lineSequence().joinToString("\n") { line ->
    if (Regex("(?i)\\b(otp|one.?time (?:password|code)|verification code|pin)\\b").containsMatchIn(line)) {
        line.replace(Regex("\\b[0-9]{4,8}\\b"), "[code removed]")
    } else line
}
