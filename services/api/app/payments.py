import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit, parse_qsl

def parse_payment(uri):
    if len(uri) > 4096 or any(ord(c) < 32 for c in uri):
        raise ValueError("Unsupported payment request.")
    parsed = urlsplit(uri)
    if parsed.scheme.lower() != "upi" or parsed.netloc.lower() != "pay" or parsed.path not in {"", "/"} or parsed.fragment:
        raise ValueError("Only upi://pay requests are supported.")
    if re.search(r"%(?![0-9A-Fa-f]{2})", parsed.query):
        raise ValueError("Malformed percent encoding.")
    fields = {}
    for key, value in parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True):
        key = key.lower()
        if key in fields:
            raise ValueError("Duplicate payment fields are not accepted.")
        if any(ord(c) < 32 for c in value):
            raise ValueError("Control characters are not accepted.")
        fields[key] = value
    if not re.fullmatch(r"[A-Za-z0-9._-]{2,256}@[A-Za-z0-9.-]{2,64}", fields.get("pa", "")):
        raise ValueError("A valid-format payee identifier is required; format does not verify identity.")
    if fields.get("cu", "INR").upper() != "INR":
        raise ValueError("Only INR is supported.")
    amount = None
    if "am" in fields:
        if not re.fullmatch(r"\d{1,9}(?:\.\d{1,2})?", fields["am"]):
            raise ValueError("Amount must be a positive decimal with at most two decimal places.")
        parsed_amount = Decimal(fields["am"])
        if parsed_amount <= 0 or parsed_amount > Decimal("1000000"):
            raise ValueError("Amount is outside this preview's supported range.")
        amount = format(parsed_amount.quantize(Decimal("0.01")), "f")
    if len(fields.get("pn", "")) > 160 or len(fields.get("tn", "")) > 500:
        raise ValueError("Payment description is too long.")
    details = {"payee": fields["pa"], "amount": amount, "currency": "INR", "display_name": fields.get("pn", ""), "note": fields.get("tn", ""), "original_fields": fields}
    details["digest"] = hashlib.sha256(json.dumps(details, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    details["limitations"] = ["Payee name and identifier are supplied claims; recipient identity is unverified.", "This preview does not execute or intercept payments."]
    return details
