# Case study — the recovery loop that spent its budget on stale context

## Executive summary

A primary latency incident became a cross-component recovery failure. Retry opened the breaker, fallback returned context with the right headline value but wrong tokens, and a narrow semantic judge accepted the result inside its known blind spot. Repetition recovery then selected the same provider and exhausted the cost envelope.

No wrong answer reached the user because the global ceiling worked. The request still failed: containment is not correct service.

## Evidence-led diagnosis

The legacy trace `1e15a90d23a9ae6bec3b033fddf4d2cdfeb2af02ddd00e79ff01561d7c0bbe36` links the false accept, three same-fingerprint verifications, secondary re-entry, and final ceiling error. The deterministic replay remained red across 20 repetitions and four Python hash seeds.

The root cause was not “the model made a mistake.” A narrow judge was given authority inside a documented failure slice, while replan lacked a route-diversity constraint.

## Fix

The fixed policy performs an exact token check, quarantines the stale provider/fingerprint, and requires recovery to select an independent trusted route. These are system controls with observable behavior.

## Verified outcome

- legacy: `contained_cost_ceiling`, cost 11, latency 98, **red**
- fixed: `recovered_correct`, cost 11, latency 94, **green**
- fixed trace: `241054bff3c6c8146a228bd3af416ca1318aa6616d22dd09ffcfbbb75f100017`
- replay-verified fix: **True**

## Claim boundary

This proves the corrective controls for the seeded simulator incident. It does not prove that an independent provider is truly independent in production; dependency mapping and live fault drills remain required.
