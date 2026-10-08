# Sachet engineering replay

Synthetic engineering regression; no real-world accuracy or model superiority claim.

40 base journeys; 65 prefixes. Each prefix is replayed through two deterministic input strategies.

| Strategy | Prefix expectations met | Final-case expectations met | Legitimate cases with a warning | Unsupported quotations |
| --- | ---: | ---: | ---: | ---: |
| latest_message_rules | 59/65 | 35/40 | 3/18 | 0 |
| available_context_rules | 59/65 | 35/40 | 3/18 | 0 |

## Interpretation limits

- All scenarios and provisional labels are AI-authored, synthetic and developer-visible.
- Related families and paired lookalikes are not independent draws. No human double annotation.
- These compare deterministic rules on latest message versus available context, not different AI models.
- Cloud model and structured-state contribution experiments require configured providers and independently reviewed data.
- CPU inference time excludes network, OCR, queue and user decision time. No financial loss reduction was measured.

## Cases requiring review

These are retained rather than hidden or relabelled to improve results.

| Strategy | Case/prefix | Expected | Observed |
| --- | --- | --- | --- |
| latest_message_rules | val_02/1 | explain, clarify | warn |
| available_context_rules | val_02/1 | explain, clarify | warn |
| latest_message_rules | val_04/1 | explain, clarify | warn |
| available_context_rules | val_04/1 | explain, clarify | warn |
| latest_message_rules | val_05/1 | warn | clarify |
| available_context_rules | val_05/1 | warn | clarify |
| latest_message_rules | stream_05/2 | warn | clarify |
| latest_message_rules | stream_13/2 | warn | clarify |
| available_context_rules | stream_13/2 | warn | clarify |
| latest_message_rules | stream_14/1 | explain, clarify | warn |
| available_context_rules | stream_14/1 | explain, clarify | warn |
| available_context_rules | stream_14/2 | explain, clarify | warn |
