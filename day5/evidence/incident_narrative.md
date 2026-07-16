# Incident narrative — trace-00000007

*Reconstructed entirely from the Day-5 timeline viewer by someone who did not
run the job. No raw logs, no source access — only `faultline_store`.*

## Summary
Run **trace-00000007** ended in **ERROR**. It executed
4 spans. The failure originates in
**`tool.sum`** (a `tool` span) at sequence 6.

## What happened, in order
The `agent` root span started, called the `model` to plan, then ran the tool
steps in sequence. `tool.retrieve` succeeded; **`tool.sum` failed** with:

> `RiskyToolError: tool sum exploded (token=***REDACTED*** at index 1`

Because the tracer closes spans on the way out, the failure propagated up: the
parent `agent` span is also recorded as `error`. The verify step never ran.

## Root cause & blast radius
- **Root-cause span:** `tool.sum`
- **Failing path (root → failure):** agent > tool.sum
- **Unaffected:** model planning and retrieval both completed `ok`.

## How this was reconstructed
`reconstruct()` issued indexed queries against the SQLite store (`SEARCH ...
USING INDEX`), ordered the spans by their logical clock, and walked parent
links from the failing leaf to the root. No wall-clock, no guesswork.

## Note on redaction
The tool's error text originally interpolated a secret. The stored message shows
`token=***REDACTED***` — the secret never reached the store (Day-4 redaction
policy), so this narrative is safe to share.
