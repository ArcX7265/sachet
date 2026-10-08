# Provider and model readiness

No live provider result has been measured for this build. Model identifiers and API credentials are supplied by local configuration, never embedded in the client. Using a model through a free API requires that account's actual free allocation; the application cannot make a billing guarantee on behalf of the provider.

## Implemented protocol checks

`tests/test_provider_contract.py` uses fake HTTP responses to exercise Groq/Gemini request shapes, absence of model tools, redaction before transmission, schema validation, exact source quotations, unsupported categories, missing configuration, quota errors and incomplete responses. These are protocol and failure-behavior tests, not model quality measurements.

## Before enabling a selected model

- Confirm the model supports the configured structured-output schema and current free account limits.
- Run the same permitted English engineering fixtures through the provider.
- Manually review assertion roles and the meaning of quotes; exact matching alone cannot validate interpretation.
- Measure error/refusal frequency, end-to-end latency, token use and useful assessment coverage.
- Compare direct conversation assessment against structured processing on independently reviewed cases before claiming an improvement.
- Keep real private content disabled until the data-handling route and consent requirements are established.

## Primary API references checked during implementation

- [Groq OpenAI compatibility](https://console.groq.com/docs/openai)
- [Gemini structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Groq data controls](https://console.groq.com/docs/your-data)
- [Gemini terms](https://ai.google.dev/gemini-api/terms)
- [Razorpay webhook validation](https://razorpay.com/docs/webhooks/validate-test/)
