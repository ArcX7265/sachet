"""Engineering replay, deliberately separate from claims of real-world accuracy.

Only allowlisted observable text reaches the detector. Expected outcomes are read
after inference. All fixtures are synthetic and developer-visible.
"""
from __future__ import annotations
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))


def read_cases():
    legacy = json.loads((ROOT / "evaluation" / "engineering-seed.json").read_text(encoding="utf-8"))
    streaming = json.loads((ROOT / "evaluation" / "streaming.json").read_text(encoding="utf-8"))
    rows = []
    mapping = {"concern": "warn", "limited": "explain", "clarify": "clarify"}
    for row in legacy["cases"]:
        rows.append({
            "id": row["id"], "family": row["pair_group"], "scenario_type": row["expectation"]["scenario_type"],
            "events": [row["text"]],
            "allowed_responses": [[mapping[x] for x in row["expectation"]["allowed_statuses"]]],
            "source": "legacy engineering fixture",
        })
    for row in streaming["cases"]:
        rows.append({**row, "source": "streaming engineering fixture"})
    return rows


def observable_events(texts):
    # Do not pass IDs carrying scenario labels, expected verdicts, later messages,
    # family names, annotations, or final outcomes to inference.
    return [{"id": f"event_{i+1}", "text": text, "source_type": "user_shared_text"} for i, text in enumerate(texts)]


def inspect_evidence(result, events):
    sources = {e["id"]: e["text"] for e in events}
    errors = []
    for concern in result.get("concerns", []):
        for ref in concern.get("evidence", []):
            text = sources.get(ref.get("event_id"))
            quote = ref.get("quote", "")
            if text is None or not quote or quote not in text:
                errors.append({"concern": concern.get("id"), "reason": "unresolved or unsupported quotation"})
    return errors


def evaluate():
    from app.engine import assess
    cases = read_cases()
    records = []
    for row in cases:
        for index in range(len(row["events"])):
            prefix = observable_events(row["events"][:index + 1])
            for baseline, events in (("latest_message_rules", prefix[-1:]), ("available_context_rules", prefix)):
                before = time.perf_counter()
                result = assess(events, revision=index + 1)
                duration = (time.perf_counter() - before) * 1000
                allowed = row["allowed_responses"][index]
                records.append({
                    "case_id": row["id"], "family": row["family"], "scenario_type": row["scenario_type"],
                    "prefix": index + 1, "final_prefix": index == len(row["events"]) - 1,
                    "baseline": baseline, "expected_responses": allowed, "response": result["response"],
                    "matches_engineering_expectation": result["response"] in allowed,
                    "evidence_errors": inspect_evidence(result, events), "latency_ms": round(duration, 3),
                    "engine": result.get("engine"), "concern_ids": [c["id"] for c in result.get("concerns", [])],
                })
    report = {
        "purpose": "Synthetic engineering regression; no real-world accuracy or model superiority claim.",
        "case_count": len(cases), "source_counts": dict(Counter(c["source"] for c in cases)),
        "prefix_count": sum(len(c["events"]) for c in cases),
        "limitations": [
            "All scenarios and provisional labels are AI-authored, synthetic and developer-visible.",
            "Related families and paired lookalikes are not independent draws. No human double annotation.",
            "These compare deterministic rules on latest message versus available context, not different AI models.",
            "Cloud model and structured-state contribution experiments require configured providers and independently reviewed data.",
            "CPU inference time excludes network, OCR, queue and user decision time. No financial loss reduction was measured.",
        ], "records": records,
    }
    out = ROOT / "evaluation" / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "engineering-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = ["# Sachet engineering replay", "", report["purpose"], "", f"{report['case_count']} base journeys; {report['prefix_count']} prefixes. Each prefix is replayed through two deterministic input strategies.", "", "| Strategy | Prefix expectations met | Final-case expectations met | Legitimate cases with a warning | Unsupported quotations |", "| --- | ---: | ---: | ---: | ---: |"]
    for baseline in ("latest_message_rules", "available_context_rules"):
        subset = [r for r in records if r["baseline"] == baseline]
        final = [r for r in subset if r["final_prefix"]]
        legit = {r["case_id"] for r in subset if r["scenario_type"] == "legitimate_lookalike"}
        warned = {r["case_id"] for r in subset if r["scenario_type"] == "legitimate_lookalike" and r["response"] == "warn"}
        lines.append(f"| {baseline} | {sum(r['matches_engineering_expectation'] for r in subset)}/{len(subset)} | {sum(r['matches_engineering_expectation'] for r in final)}/{len(final)} | {len(warned)}/{len(legit)} | {sum(len(r['evidence_errors']) for r in subset)} |")
    lines += ["", "## Interpretation limits", ""] + [f"- {x}" for x in report["limitations"]]
    lines += ["", "## Cases requiring review", "", "These are retained rather than hidden or relabelled to improve results.", "", "| Strategy | Case/prefix | Expected | Observed |", "| --- | --- | --- | --- |"]
    for row in records:
        if not row["matches_engineering_expectation"] or row["evidence_errors"]:
            lines.append(f"| {row['baseline']} | {row['case_id']}/{row['prefix']} | {', '.join(row['expected_responses'])} | {row['response']} |")
    (out / "engineering-results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:11]))
    print(f"Full results: {out / 'engineering-results.md'}")
    return report


if __name__ == "__main__":
    evaluate()
