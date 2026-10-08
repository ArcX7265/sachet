import os
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app import main


@pytest.fixture
def client(monkeypatch):
    with tempfile.TemporaryDirectory(prefix="sachet-narrative-") as directory:
        monkeypatch.setenv("SACHET_DB_PATH", str(Path(directory) / "test.sqlite3"))
        monkeypatch.setenv("DEMO_MODE", "true")
        with TestClient(main.app) as c:
            yield c


def session(client, role="user"):
    token = client.post("/v1/sessions", json={"role": role}).json()["token"]
    return {"Authorization": "Bearer " + token}


def case(client, headers):
    cid = client.post("/v1/cases", headers=headers, json={"title": "PRIVATE TITLE", "data_class": "synthetic"}).json()["id"]
    client.post(f"/v1/cases/{cid}/events", headers=headers, json={"text": "PRIVATE ORIGINAL TEXT: release code after a deposit", "idempotency_key": "e1"})
    return cid


def test_narrative_needs_exact_current_preview_and_explicit_consent(client):
    headers = session(client)
    cid = case(client, headers)
    url = f"/v1/cases/{cid}/contributions"
    narrative = "A caller promised a release code after a processing deposit. OTP is 654321."
    assert client.post(url, headers=headers, json={"consent": True, "narrative": narrative}).status_code == 409
    preview = client.post(url + "/preview", headers=headers, json={"narrative": narrative}).json()
    assert "654321" not in str(preview)
    assert "PRIVATE ORIGINAL TEXT" not in str(preview)
    assert "PRIVATE TITLE" not in str(preview)
    body = {"consent": False, "narrative": narrative, "preview_digest": preview["preview_digest"]}
    assert client.post(url, headers=headers, json=body).status_code == 422
    body["consent"] = True
    changed = {**body, "narrative": narrative + " Another step."}
    assert client.post(url, headers=headers, json=changed).status_code == 409
    result = client.post(url, headers=headers, json=body)
    assert result.status_code == 200
    assert result.json()["preview"] == preview
    assert client.post(url, headers=headers, json=body).json()["id"] == result.json()["id"]


def test_new_case_evidence_invalidates_report_preview(client):
    headers = session(client)
    cid = case(client, headers)
    url = f"/v1/cases/{cid}/contributions"
    narrative = "Processing deposit requested to obtain a release code."
    preview = client.post(url + "/preview", headers=headers, json={"narrative": narrative}).json()
    client.post(f"/v1/cases/{cid}/events", headers=headers, json={"text": "The contact now wants a second deposit.", "idempotency_key": "e2"})
    result = client.post(url, headers=headers, json={"consent": True, "narrative": narrative, "preview_digest": preview["preview_digest"]})
    assert result.status_code == 409


def test_unfamiliar_reports_can_be_related_without_existing_rule_tags(client):
    headers = session(client)
    notes = ["A contact promised a release code after a processing deposit.", "Another contact requires processing deposit for release code delivery."]
    for note in notes:
        cid = case(client, headers)
        url = f"/v1/cases/{cid}/contributions"
        p = client.post(url + "/preview", headers=headers, json={"narrative": note}).json()
        assert client.post(url, headers=headers, json={"consent": True, "narrative": note, "preview_digest": p["preview_digest"]}).status_code == 200
    analyst = session(client, "analyst")
    reports = client.get("/v1/analyst/candidates", headers=analyst).json()["candidates"]
    assert len(reports) == 2
    assert reports[0]["similar_candidates"][0]["shared_terms"]
    assert reports[0]["independence"] == "unverified"
    assert "PRIVATE ORIGINAL TEXT" not in str(reports)
