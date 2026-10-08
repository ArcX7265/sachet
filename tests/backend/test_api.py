"""Integration regression tests. All data and gateway responses are synthetic."""
import hashlib
import hmac
import json
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from app import main
from app.engine import assess
from app.providers import ProviderFailure


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("SACHET_DB_PATH", str(tmp_path / "test.sqlite3"))
    for name in ("GROQ_API_KEY", "GEMINI_API_KEY", "RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "RAZORPAY_WEBHOOK_SECRET"):
        monkeypatch.delenv(name, raising=False)
    with TestClient(main.app) as app:
        yield app


def login(client, role="user"):
    result = client.post("/v1/sessions", json={"role": role})
    assert result.status_code == 200, result.text
    return {"Authorization": "Bearer " + result.json()["token"]}


def case(client, headers, **kwargs):
    result = client.post("/v1/cases", headers=headers, json={"title": "Synthetic test", **kwargs})
    assert result.status_code == 200, result.text
    return result.json()


def add(client, headers, case_id, text="Send me your OTP to complete your bank refund.", **kwargs):
    result = client.post(f"/v1/cases/{case_id}/events", headers=headers,
                         json={"text": text, "idempotency_key": str(uuid4()), **kwargs})
    assert result.status_code == 200, result.text
    return result.json()


def contributed(client, headers, text="Send me your OTP to complete your bank refund."):
    item = case(client, headers)
    add(client, headers, item["id"], text)
    report = client.post(f"/v1/cases/{item['id']}/contributions", headers=headers, json={"consent": True})
    assert report.status_code == 200, report.text
    return item, report.json()


def proposal(client, analyst, candidate, pattern_id="release_deposit", groups=None):
    review = client.post(f"/v1/analyst/candidates/{candidate}/reviews", headers=analyst,
                         json={"status": "accepted_for_evaluation", "reason": "Synthetic candidate for regression testing."})
    assert review.status_code == 200
    response = client.post("/v1/analyst/updates", headers=analyst, json={"candidate_id": candidate, "title": "Reviewed synthetic variation", "pattern": {
        "id": pattern_id, "description": "A deposit is conditional on a claimed release code.",
        "term_groups": groups or [["release code"], ["processing deposit"], ["first transfer"]],
        "next_action": "Pause and independently verify the claimed release."}})
    assert response.status_code == 200, response.text
    return response.json()


def test_demo_authentication_default_and_revocation(client, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")
    assert client.post("/v1/sessions", json={"role": "admin"}).status_code == 403
    monkeypatch.setenv("DEMO_MODE", "true")
    owner = login(client)
    assert client.get("/v1/cases").status_code == 401
    assert client.delete("/v1/sessions/current", headers=owner).status_code == 200
    assert client.get("/v1/cases", headers=owner).status_code == 401


def test_case_ownership_and_role_boundaries(client):
    owner, stranger, analyst = login(client), login(client), login(client, "analyst")
    item = case(client, owner)
    path = f"/v1/cases/{item['id']}"
    assert client.get(path, headers=stranger).status_code == 404
    assert client.delete(path, headers=stranger).status_code == 404
    assert client.get(path, headers=analyst).status_code == 404
    assert client.post("/v1/cases", headers=analyst, json={}).status_code == 403
    assert client.get("/v1/analyst/candidates", headers=owner).status_code == 403
    assert client.post("/v1/admin/bundles/baseline-v1/rollback", headers=analyst).status_code == 403


@pytest.mark.parametrize("data_class", ["private", "consented"])
def test_private_data_cannot_reach_free_cloud(client, monkeypatch, data_class):
    calls = []
    monkeypatch.setattr(main, "propose", lambda *args: calls.append(args))
    headers = login(client)
    assert client.post("/v1/cases", headers=headers, json={"mode": "cloud", "provider": "groq", "data_class": data_class}).status_code == 403
    assert calls == []


def test_provider_failure_retains_source_without_safe_fallback(client, monkeypatch):
    def fail(*args):
        raise ProviderFailure("invalid_response")
    monkeypatch.setattr(main, "propose", fail)
    headers = login(client)
    item = case(client, headers, mode="cloud", provider="groq", data_class="synthetic")
    current = add(client, headers, item["id"])
    assert len(current["events"]) == 1
    assert current["assessment"]["processing_status"] == "unavailable"
    assert current["assessment"]["failure_category"] == "invalid_response"
    assert current["assessment"]["engine"] == "groq"
    assert current["alerts"] == []


def test_shared_daily_provider_budget(client, monkeypatch):
    monkeypatch.setenv("SACHET_CLOUD_DAILY_REQUEST_LIMIT", "1")
    calls = []
    def fake(provider, events, revision, bundle):
        calls.append(provider)
        return assess(events, revision, bundle)
    monkeypatch.setattr(main, "propose", fake)
    for provider in ["groq", "gemini"]:
        headers = login(client)
        item = case(client, headers, mode="cloud", provider=provider, data_class="synthetic")
        current = add(client, headers, item["id"])
    assert calls == ["groq"]
    assert current["assessment"]["failure_category"] == "local_daily_budget_exhausted"


def test_idempotency_content_conflict_and_replay(client):
    headers = login(client)
    first = case(client, headers, idempotency_key="create-once")
    second = case(client, headers, idempotency_key="create-once")
    assert first["id"] == second["id"]
    assert client.post("/v1/cases", headers=headers, json={"title": "Different", "idempotency_key": "create-once"}).status_code == 409
    initial = add(client, headers, first["id"], idempotency_key="event-once")
    repeated = add(client, headers, first["id"], idempotency_key="event-once")
    assert initial["revision"] == repeated["revision"] == 1
    assert len(repeated["history"]) == 1
    conflict = client.post(f"/v1/cases/{first['id']}/events", headers=headers,
                           json={"text": "Different content", "idempotency_key": "event-once"})
    assert conflict.status_code == 409


def test_retry_recovers_committed_event_without_assessment(client, monkeypatch):
    headers = login(client)
    item = case(client, headers)
    original = main.process
    monkeypatch.setattr(main, "process", lambda case_id: None)
    initial = add(client, headers, item["id"], idempotency_key="recover")
    assert initial["assessment"] is None
    monkeypatch.setattr(main, "process", original)
    recovered = add(client, headers, item["id"], idempotency_key="recover")
    assert recovered["revision"] == 1
    assert len(recovered["events"]) == 1
    assert recovered["assessment"]["response"] == "warn"


def test_alerts_ignore_paraphrase_but_realert_on_amount_or_action(client):
    headers = login(client)
    item = case(client, headers)
    current = add(client, headers, item["id"], "Pay INR 2000 before we release your refund.")
    alert = current["alerts"][0]
    assert client.post(f"/v1/cases/{item['id']}/alerts/{alert['id']}/acknowledge", headers=headers).status_code == 200
    current = add(client, headers, item["id"], "Please pay INR 2000.00 first to unlock your refund.")
    assert current["alerts"][0]["notification_count"] == 1
    assert current["alerts"][0]["acknowledged"] is True
    current = add(client, headers, item["id"], "Pay 5000 rupees before we release your refund.")
    assert current["alerts"][0]["notification_count"] == 2
    assert current["alerts"][0]["acknowledged"] is False
    assert len(current["assessment"]["concerns"][0]["evidence"]) >= 3
    current = add(client, headers, item["id"], "Please give me your password.")
    assert {a["concern_id"] for a in current["alerts"] if a["active"]} == {"advance_payment", "credential_request"}


def test_correction_retracts_alert_and_preserves_trace(client):
    headers = login(client)
    item = case(client, headers)
    initial = add(client, headers, item["id"])
    path = f"/v1/cases/{item['id']}/corrections"
    body = {"event_id": initial["events"][0]["id"], "text": "Never share your OTP. This is a training example.", "idempotency_key": "correction"}
    result = client.post(path, headers=headers, json=body)
    assert result.status_code == 200, result.text
    current = result.json()
    assert current["revision"] == 2
    assert current["assessment"]["response"] != "warn"
    assert current["alerts"][0]["active"] is False
    assert current["events"][0]["active"] is False
    assert len(current["history"]) == 2
    assert client.post(path, headers=headers, json=body).json()["revision"] == 2
    assert client.post(path, headers=headers, json={**body, "idempotency_key": "conflicting"}).status_code == 409


def test_notification_updates_supersede_same_source(client):
    headers = login(client)
    item = case(client, headers)
    add(client, headers, item["id"], source_type="notification", source_event_id="notification-1")
    current = add(client, headers, item["id"], "Never share your OTP.", source_type="notification", source_event_id="notification-1")
    assert [e["active"] for e in current["events"]] == [False, True]
    assert current["assessment"]["processing_status"] == "partial"
    assert current["assessment"]["response"] != "warn"


def test_stale_job_cannot_replace_latest_assessment(client, monkeypatch):
    headers = login(client)
    item = case(client, headers)
    original = main.assess
    raced = False
    def racing(events, revision, bundle):
        nonlocal raced
        if not raced:
            raced = True
            add(client, headers, item["id"], "Install AnyDesk for a bank refund.")
        return original(events, revision, bundle)
    monkeypatch.setattr(main, "assess", racing)
    current = add(client, headers, item["id"])
    assert current["revision"] == 2
    assert current["assessment"]["case_revision"] == 2
    assert len([a for a in current["history"] if a["stale"]]) == 1
    assert all(a["revision"] == 2 for a in current["alerts"])


def test_contribution_is_minimized_consented_and_idempotent(client):
    headers, analyst = login(client), login(client, "analyst")
    item = case(client, headers, goal="Private account 998877665544")
    add(client, headers, item["id"], "Contact joe@example.com says share your OTP 654321 for the bank refund.")
    path = f"/v1/cases/{item['id']}/contributions"
    assert client.post(path, headers=headers, json={"consent": False}).status_code == 422
    first = client.post(path, headers=headers, json={"consent": True}).json()
    second = client.post(path, headers=headers, json={"consent": True}).json()
    assert first["id"] == second["id"]
    shared = client.get("/v1/analyst/candidates", headers=analyst).text
    assert "joe@example.com" not in shared and "654321" not in shared and "998877665544" not in shared
    assert "credential_request" in shared
    assert client.get(f"/v1/cases/{item['id']}", headers=analyst).status_code == 404


def test_review_evaluation_release_and_rollback(client):
    headers, analyst, admin = login(client), login(client, "analyst"), login(client, "admin")
    item, contribution = contributed(client, headers)
    bundle = proposal(client, analyst, contribution["candidate_id"])
    activation = f"/v1/admin/bundles/{bundle['id']}/activate"
    assert client.post(activation, headers=admin).status_code == 409
    assert client.post(activation, headers=analyst).status_code == 403
    evaluated = client.post(f"/v1/analyst/updates/{bundle['id']}/evaluate", headers=analyst).json()
    assert evaluated["evaluation"]["passed"] is True
    assert evaluated["evaluation"]["improvements"] > 0
    assert client.post(activation, headers=admin).status_code == 200
    assert client.get("/v1/health").json()["active_bundle"] == bundle["id"]
    assert client.post("/v1/admin/bundles/baseline-v1/rollback", headers=admin).status_code == 200
    assert client.get("/v1/health").json()["active_bundle"] == "baseline-v1"
    assert client.post(f"/v1/admin/bundles/{bundle['id']}/rollback", headers=admin).status_code == 200


def test_regression_update_is_rejected(client):
    headers, analyst, admin = login(client), login(client, "analyst"), login(client, "admin")
    _, contribution = contributed(client, headers)
    bundle = proposal(client, analyst, contribution["candidate_id"], groups=[["pay", "release"]])
    evaluated = client.post(f"/v1/analyst/updates/{bundle['id']}/evaluate", headers=analyst).json()
    assert evaluated["evaluation"]["passed"] is False
    assert evaluated["evaluation"]["regressions"] > 0
    assert client.post(f"/v1/admin/bundles/{bundle['id']}/activate", headers=admin).status_code == 409


def test_case_deletion_removes_derivatives_and_active_update(client):
    headers, analyst, admin = login(client), login(client, "analyst"), login(client, "admin")
    item, contribution = contributed(client, headers)
    bundle = proposal(client, analyst, contribution["candidate_id"])
    client.post(f"/v1/analyst/updates/{bundle['id']}/evaluate", headers=analyst)
    client.post(f"/v1/admin/bundles/{bundle['id']}/activate", headers=admin)
    assert client.delete(f"/v1/cases/{item['id']}", headers=headers).status_code == 200
    assert client.get(f"/v1/cases/{item['id']}", headers=headers).status_code == 404
    assert client.get("/v1/analyst/candidates", headers=analyst).json()["candidates"] == []
    assert client.get("/v1/health").json()["active_bundle"] == "baseline-v1"
    with main.db() as conn:
        for table in ["events", "assessments", "alerts", "contributions", "payments", "orders", "order_attempts"]:
            assert conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0] == 0


def test_withdraw_one_report_from_shared_candidate_rebuilds_and_invalidates_descendants(client):
    headers, analyst = login(client), login(client, "analyst")
    first, report1 = contributed(client, headers)
    _, report2 = contributed(client, headers, "Install AnyDesk for a banking refund.")
    with main.db() as conn:
        conn.execute("UPDATE contributions SET candidate_id=? WHERE id=?", (report1["candidate_id"], report2["id"]))
        for bundle_id, parent_id, candidate in [("synthetic-parent", "baseline-v1", report1["candidate_id"]), ("synthetic-child", "synthetic-parent", report2["candidate_id"])]:
            conn.execute("INSERT INTO bundles VALUES(?,0,?)", (bundle_id, main.dump({"id": bundle_id, "parent_id": parent_id, "candidate_id": candidate})))
    response = client.delete(f"/v1/cases/{first['id']}/contributions/{report1['id']}", headers=headers)
    assert response.status_code == 200, response.text
    candidates = client.get("/v1/analyst/candidates", headers=analyst).json()["candidates"]
    candidate = next(c for c in candidates if c["id"] == report1["candidate_id"])
    assert candidate["status"] == "needs_evidence"
    assert candidate["workflow_tags"] == ["remote_access"]
    with main.db() as conn:
        assert conn.execute("SELECT count(*) FROM bundles WHERE id LIKE 'synthetic-%'").fetchone()[0] == 0


def test_expired_sources_are_deleted_on_case_list(client):
    headers = login(client)
    item, _ = contributed(client, headers)
    with main.db() as conn:
        stored = json.loads(conn.execute("SELECT data FROM cases WHERE id=?", (item["id"],)).fetchone()[0])
        stored["retention_until"] = "2000-01-01T00:00:00+00:00"
        conn.execute("UPDATE cases SET data=? WHERE id=?", (main.dump(stored), item["id"]))
    assert client.get("/v1/cases", headers=headers).json()["cases"] == []
    with main.db() as conn:
        assert conn.execute("SELECT count(*) FROM candidates").fetchone()[0] == 0


def test_body_limits_include_malformed_header_and_stream(client):
    assert client.post("/v1/sessions", content=b"{}", headers={"content-length": "bad"}).status_code == 400
    assert client.post("/v1/sessions", content=b"x" * 100001).status_code == 413
    assert client.post("/v1/sessions", content=iter([b"x" * 60000, b"y" * 60000])).status_code == 413


def test_payment_preview_binding_is_owned_and_revision_specific(client):
    headers, stranger = login(client), login(client)
    item = case(client, headers)
    add(client, headers, item["id"])
    preview = client.post("/v1/payment-requests", headers=headers, json={"case_id": item["id"], "uri": "upi://pay?pa=merchant@bank&am=120.50&pn=Claimed%20merchant"}).json()
    assert preview["amount"] == "120.50" and preview["mode"] == "preview"
    path = f"/v1/payment-requests/{preview['id']}/handoff"
    assert client.post(path, headers=stranger, json={"digest": preview["digest"]}).status_code == 404
    assert client.post(path, headers=headers, json={"digest": "é" * 64}).status_code == 409
    assert "disabled" in client.post(path, headers=headers, json={"digest": preview["digest"]}).text
    add(client, headers, item["id"], "More context arrived.")
    assert "stale" in client.post(path, headers=headers, json={"digest": preview["digest"]}).text


@pytest.mark.parametrize("uri", ["https://malicious.invalid", "upi://pay?pa=user@bank&pa=other@bank", "upi://pay?pa=user@bank&am=-1", "upi://pay?pa=user@bank&am=NaN", "upi://pay?pa=user@bank&cu=USD", "upi://pay?pa=user@bank&pn=%ZZ", "upi://pay?pa=user@bank&pn=%0a"])
def test_invalid_payment_request_rejected(client, uri):
    headers = login(client)
    item = case(client, headers)
    assert client.post("/v1/payment-requests", headers=headers, json={"case_id": item["id"], "uri": uri}).status_code == 422


def gateway_setup(client, monkeypatch, behavior="success"):
    headers = login(client)
    item = case(client, headers)
    add(client, headers, item["id"], "Please pay your chosen grocery bill.")
    preview = client.post("/v1/payment-requests", headers=headers, json={"case_id": item["id"], "uri": "upi://pay?pa=merchant@bank&am=120.50"}).json()
    for name, value in {"RAZORPAY_KEY_ID": "rzp_test_fake", "RAZORPAY_KEY_SECRET": "fake-secret", "RAZORPAY_WEBHOOK_SECRET": "fake-hook"}.items():
        monkeypatch.setenv(name, value)
    calls = []
    class Gateway:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def post(self, url, **kwargs):
            calls.append(kwargs)
            if behavior == "timeout":
                raise httpx.ReadTimeout("Synthetic timeout")
            if behavior == "malformed":
                return httpx.Response(200, json=[])
            return httpx.Response(200, json={"id": "order_synthetic", "amount": 12050, "currency": "INR"})
    monkeypatch.setattr(main.httpx, "Client", Gateway)
    body = {"payment_request_id": preview["id"], "digest": preview["digest"], "idempotency_key": "only-one"}
    return headers, body, calls


def signed_event(client, kind="payment.captured", event_id="event-1", amount=12050, signature=None, **extra):
    body = {"event": kind, "payload": {"payment": {"entity": {"id": "pay_synthetic", "order_id": "order_synthetic", "amount": amount, "currency": "INR", "status": kind.split(".")[1], **extra}}}}
    raw = json.dumps(body).encode()
    signature = signature or hmac.new(b"fake-hook", raw, hashlib.sha256).hexdigest()
    return client.post("/v1/webhooks/payments/razorpay", content=raw,
                       headers={"content-type": "application/json", "x-razorpay-signature": signature, "x-razorpay-event-id": event_id})


def test_gateway_requires_keys_and_no_fake_success(client):
    assert client.post("/v1/payments/test-orders", headers=login(client), json={"payment_request_id": "fake", "digest": "x" * 64, "idempotency_key": "fake"}).status_code == 503


def test_gateway_order_idempotency_and_signed_confirmation(client, monkeypatch):
    headers, body, calls = gateway_setup(client, monkeypatch)
    first = client.post("/v1/payments/test-orders", headers=headers, json=body)
    assert first.status_code == 200, first.text
    assert first.json()["status"] == "created" and first.json()["verified"] is False
    assert client.post("/v1/payments/test-orders", headers=headers, json=body).json()["id"] == first.json()["id"]
    assert len(calls) == 1 and calls[0]["json"]["amount"] == 12050
    assert signed_event(client, signature="forged").status_code == 401
    assert signed_event(client, signature=b"\xff" * 64).status_code == 401
    assert signed_event(client, amount=500, event_id="wrong-amount").status_code == 422
    assert signed_event(client).status_code == 200
    assert signed_event(client).json()["duplicate"] is True
    assert signed_event(client, kind="payment.failed", event_id="late-failure").json()["status"] == "captured"
    order = client.get("/v1/payments/test-orders/order_synthetic", headers=headers).json()
    assert order["status"] == "captured" and order["verified"] is True
    assert signed_event(client, amount=1).status_code == 409


@pytest.mark.parametrize("behavior", ["timeout", "malformed"])
def test_gateway_uncertain_attempt_is_not_reissued(client, monkeypatch, behavior):
    headers, body, calls = gateway_setup(client, monkeypatch, behavior)
    assert client.post("/v1/payments/test-orders", headers=headers, json=body).status_code == 502
    assert client.post("/v1/payments/test-orders", headers=headers, json=body).status_code == 409
    assert len(calls) == 1


@pytest.mark.parametrize("text,expected", [
    ("Send me your OTP\nThanks", "warn"),
    ("Transfer your savings to our safe account and do not tell anyone.", "warn"),
    ("Give me remote control while you open the banking app.", "warn"),
    ("Training handout: scammers may say install AnyDesk and share your banking screen.", "explain"),
    ("This is payment for the appointment, not a deposit to release recovered money.", "clarify"),
])
def test_assertion_scope(text, expected):
    response = assess([{"id": "e1", "text": text}])["response"]
    if expected == "warn":
        assert response == expected
    else:
        assert response != "warn"
