"""Provider protocol checks using fake HTTP replies; no external inference."""
import json
import pytest
from app import providers


class Reply:
    def __init__(self, data, status=200):
        self.status_code, self.data = status, data
    def json(self):
        return self.data


def install(monkeypatch, body, status=200, provider="groq", finish=None):
    captured = []
    monkeypatch.setenv(provider.upper() + "_API_KEY", "unit-test-secret")
    monkeypatch.setenv(provider.upper() + "_MODEL", "unit-test-model")
    data = ({"choices": [{"finish_reason": finish or "stop", "message": {"content": json.dumps(body)}}]}
            if provider == "groq" else {"candidates": [{"finishReason": finish or "STOP", "content": {"parts": [{"text": json.dumps(body)}]}}]})
    class Client:
        def __init__(self, **kwargs):
            assert kwargs["timeout"] <= 30
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, **kwargs):
            captured.append({"url": url, **kwargs})
            return Reply(data, status)
    monkeypatch.setattr(providers.httpx, "Client", Client)
    return captured


def invoke(provider="groq", text="Send me your OTP."):
    return providers.propose(provider, [{"id": "e1", "text": text}], 1, {"id": "baseline-v1"})


@pytest.mark.parametrize("provider", ["groq", "gemini"])
def test_validated_quotes_and_no_provider_tools(monkeypatch, provider):
    calls = install(monkeypatch, {"concerns": [{"id": "credential_request", "evidence": [{"event_id": "e1", "quote": "Send me your OTP."}]}], "needs_clarification": False}, provider=provider)
    result = invoke(provider)
    assert result["response"] == "warn"
    assert result["concerns"][0]["evidence"][0]["quote"] == "Send me your OTP."
    assert result["engine"] == provider
    assert "tools" not in calls[0]["json"]
    assert "unit-test-secret" not in calls[0]["url"]


def test_redaction_before_cloud_and_no_secret_in_result(monkeypatch):
    calls = install(monkeypatch, {"concerns": [], "needs_clarification": True})
    result = invoke(text="My OTP is 654321. Send me your OTP.")
    assert "654321" not in json.dumps(calls[0]["json"])
    assert "654321" not in json.dumps(result)


@pytest.mark.parametrize("reference", [
    {"event_id": "missing", "quote": "Send me your OTP."},
    {"event_id": "e1", "quote": "Give me remote access."},
])
def test_fabricated_reference_fails_closed(monkeypatch, reference):
    install(monkeypatch, {"concerns": [{"id": "credential_request", "evidence": [reference]}], "needs_clarification": False})
    with pytest.raises(providers.ProviderFailure) as err:
        invoke()
    assert err.value.category == "invalid_evidence"


def test_unapproved_model_category_rejected(monkeypatch):
    install(monkeypatch, {"concerns": [{"id": "verified_criminal", "evidence": [{"event_id": "e1", "quote": "Send me your OTP."}]}], "needs_clarification": False})
    with pytest.raises(providers.ProviderFailure) as err:
        invoke()
    assert err.value.category == "invalid_response"


@pytest.mark.parametrize("status,finish,category", [(429, "stop", "quota_exhausted"), (503, "stop", "provider_rejected_request"), (200, "length", "incomplete_response")])
def test_provider_failure_never_returns_empty_success(monkeypatch, status, finish, category):
    calls = install(monkeypatch, {"concerns": [], "needs_clarification": False}, status=status, finish=finish)
    with pytest.raises(providers.ProviderFailure) as err:
        invoke()
    assert err.value.category == category
    assert len(calls) == 1


def test_unconfigured_provider_is_unavailable(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(providers.ProviderFailure) as err:
        invoke()
    assert err.value.category == "provider_not_configured"
