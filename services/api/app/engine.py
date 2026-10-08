"""Inspectible English pattern baseline. Its quality must be measured independently."""
import hashlib
import re
from datetime import datetime, timezone

NEGATION = re.compile(r"\b(?:never|do not|don't|don’t|won't|will not|should not|avoid|beware|scammers? (?:may|often|ask|say)|example of|training (?:example|handout)|awareness (?:session|advice)|invented (?:classroom|example)|no (?:payment|deposit|fee|otp)|not (?:a deposit|required|needed|necessary))\b", re.I)
PAY = re.compile(r"\b(?:pay|send|transfer|deposit|remit)\b", re.I)
FUNDS = re.compile(r"\b(?:withdrawal|withdraw|refund|profits?|winnings|prize|recover|recovery|funds)\b", re.I)
CONDITION = re.compile(r"\b(?:release|unlock|before|first|required|mandatory|to receive|to withdraw)\b", re.I)
FEE = re.compile(r"\b(?:fee|tax|deposit|payment|money|amount|charge|INR|rupees|rs)\b|₹", re.I)
SENSITIVE = re.compile(r"\b(?:OTP|PIN|password|one.time (?:password|code)|seed phrase|recovery phrase)\b", re.I)
SHARE = re.compile(r"\b(?:send|share|tell|provide|give|read out|forward)\b", re.I)
REMOTE = re.compile(r"\b(?:AnyDesk|TeamViewer|remote (?:access|control)|screen.?shar(?:e|ing)|QuickSupport)\b", re.I)
INSTALL = re.compile(r"\b(?:install|download|enable|start|grant|allow|open|give)\b", re.I)
FINANCE = re.compile(r"\b(?:bank|banking|payment|refund|withdrawal|UPI|investment|wallet)\b", re.I)

def evidence(event, text, start=0):
    return {"event_id": event["id"], "quote": text, "start": start, "end": start + len(text)}

def assess(events: list[dict], revision: int = 1, bundle: dict | None = None) -> dict:
    bundle = bundle or {"id": "baseline-v1", "patterns": []}
    events = [e for e in events if e.get("active", True)]
    pieces = []
    for event in events:
        # Sentence/clause scope prevents a later 'do not tell anyone' instruction
        # from negating an earlier transfer demand. This remains a lexical heuristic.
        for match in re.finditer(r"[^\n]+?(?:[!?;]|\.(?!\d)|(?=\n)|$)", event["text"]):
            quote = match.group().strip()
            if quote:
                start = match.start() + len(match.group()) - len(match.group().lstrip())
                split = re.search(r"\s+and\s+(?=do not|don't|never)", quote, re.I)
                if split:
                    pieces.append((event, quote[:split.start()], start))
                    pieces.append((event, quote[split.end():], start + split.end()))
                else:
                    pieces.append((event, quote, start))
    positive = [p for p in pieces if not NEGATION.search(p[1])]
    concerns = []
    relations = []
    seen = set()
    def add(code, description, refs, action):
        if code in seen:
            existing = next(c for c in concerns if c["id"] == code)
            for p in refs:
                ref = evidence(*p)
                if ref not in existing["evidence"]:
                    existing["evidence"].append(ref)
                    existing["evidence_refs"].append(p[0]["id"])
            return
        seen.add(code)
        concerns.append({"id": code, "description": description, "evidence": [evidence(*p) for p in refs], "evidence_refs": [p[0]["id"] for p in refs], "next_action": action, "limitations": ["The supplied material does not verify the sender's identity or intent."], "support": "explicit_request"})
    for p in positive:
        event, text, start = p
        if PAY.search(text) and CONDITION.search(text) and FEE.search(text):
            fund_ref = p if FUNDS.search(text) else next((q for q in reversed(positive[:positive.index(p)]) if FUNDS.search(q[1])), None)
            if fund_ref:
                refs = [p] if fund_ref == p else [fund_ref, p]
                add("advance_payment", "An additional payment appears to be a condition for accessing claimed funds.", refs, "Pause the additional payment. Verify the claimed funds and fee through the organization's independently located official channel.")
                if len(refs) > 1:
                    relations.append({"type": "possibly_conditions_on", "from_event": p[0]["id"], "to_event": fund_ref[0]["id"], "inferred": True, "limitation": "The relationship is inferred from the selected case context; the events may concern different transactions."})
        if SHARE.search(text) and SENSITIVE.search(text):
            add("credential_request", "The message requests a sensitive authentication secret.", [p], "Do not share the secret. Verify the request using an independently located official support channel.")
        if REMOTE.search(text) and INSTALL.search(text):
            fin_ref = p if FINANCE.search(text) else next((q for q in positive if FINANCE.search(q[1])), None)
            if fin_ref:
                add("remote_access", "A request for device or screen access is connected to a financial interaction.", [p] if fin_ref == p else [fin_ref, p], "Pause the access request. Verify the support interaction independently before granting access.")
        if PAY.search(text) and re.search(r"\b(?:safe account|security account|verification account)\b", text, re.I):
            add("safe_account", "The message asks for a transfer to an account described as a security or verification measure.", [p], "Pause the transfer and contact your bank using a previously trusted official channel.")
    for pattern in bundle.get("patterns", []):
        refs = []
        for group in pattern["term_groups"]:
            match = next((p for p in positive if any(term.casefold() in p[1].casefold() for term in group)), None)
            if not match:
                break
            if match not in refs:
                refs.append(match)
        else:
            add(pattern["id"], pattern["description"], refs, pattern["next_action"])
    partial = any(e.get("source_type") in {"notification", "ocr"} for e in events)
    financial = any(FINANCE.search(p[1]) or PAY.search(p[1]) for p in pieces)
    response = "warn" if concerns else "clarify" if financial else "explain"
    clarification = "What are you being asked to do next, and what are you expecting to receive?" if response == "clarify" else None
    limitations = ["Limited English pattern rules; unfamiliar wording and missing context can lead to missed concerns.", "An empty concern list does not establish that an interaction is safe.", "Only material supplied to this case is assessed; identity and transaction legitimacy are not verified."]
    if partial:
        limitations.append("Notification or OCR input may omit context or contain extraction errors.")
    return {"case_revision": revision, "bundle_version": bundle["id"], "processing_status": "partial" if partial else "complete", "evidence_sufficiency": "sufficient_for_stated_concern" if concerns else "limited", "response": response, "headline": concerns[0]["description"] if concerns else "More context would help" if clarification else "No supported concern found in the supplied material", "summary": "The assessment follows the quoted requests and available case context.", "concerns": concerns, "relations": relations, "clarification": clarification, "next_action": concerns[0]["next_action"] if concerns else "Add the next requested action or independently verify the financial request.", "limitations": limitations, "engine": "local_rules", "model": None, "change_summary": "Assessment created from the current source revision.", "created_at": datetime.now(timezone.utc).isoformat()}

def minimize(text: str) -> str:
    text = re.sub(r"(?i)(\b(?:otp|pin|password|account(?: number)?|card(?: number)?)\s*(?:is|:|=)?\s*)[A-Za-z0-9-]{4,}", r"\1[REDACTED]", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+", "[IDENTIFIER]", text)
    text = re.sub(r"https?://\S+", "[LINK]", text)
    text = re.sub(r"(?<!\w)(?:\+?\d[\d -]{8,}\d)(?!\w)", "[NUMBER]", text)
    return text

def fingerprint(concern):
    # Alert identity follows the requested action and material values, not wording.
    # This deliberately small policy cannot identify every meaningful semantic change.
    text = " ".join(e["quote"].casefold() for e in concern["evidence"])
    from decimal import Decimal
    amounts = sorted({str(Decimal(t.replace(",", "")).normalize()) for t in re.findall(r"\b\d[\d,]*(?:\.\d{1,2})?\b", text)})
    secrets = sorted({"otp" if t.startswith("one") else t for t in re.findall(r"\b(?:otp|pin|password|one.time (?:password|code)|seed phrase|recovery phrase)\b", text)})
    access = sorted(set(re.findall(r"\b(?:anydesk|teamviewer|quicksupport|remote (?:access|control)|screen.?shar(?:e|ing))\b", text)))
    identifiers = sorted(set(re.findall(r"[\w.+-]+@[\w.-]+|https?://\S+", text)))
    material = [concern["id"], amounts, secrets, access, identifiers]
    import json
    return hashlib.sha256(json.dumps(material, separators=(",", ":")).encode()).hexdigest()
