import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "evaluation" / "run.py"
spec = importlib.util.spec_from_file_location("sachet_evaluation", MODULE)
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


def test_input_allowlist_excludes_future_and_annotation_fields():
    case = evaluation.read_cases()[16]
    events = evaluation.observable_events(case["events"][:1])
    assert len(events) == 1
    assert set(events[0]) == {"id", "text", "source_type"}
    assert events[0]["id"] == "event_1"
    assert events[0]["text"] == case["events"][0]
    assert case["events"][1] not in str(events)


def test_seed_has_unique_ids_and_prefix_annotations():
    cases = evaluation.read_cases()
    assert len({c["id"] for c in cases}) == len(cases) == 40
    for row in cases:
        assert len(row["events"]) == len(row["allowed_responses"])
        assert all(row["allowed_responses"])


def test_evidence_audit_rejects_fabricated_quote():
    result = {"concerns": [{"id": "x", "evidence": [{"event_id": "e", "quote": "send an OTP"}]}]}
    assert evaluation.inspect_evidence(result, [{"id": "e", "text": "Hello"}])
