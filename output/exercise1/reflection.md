# Reflection: AI Spatial Blind Spots

## What I learned

1. AI should not guess missing coordinates.
- In this dataset, three records had longitude `0` with otherwise valid Taiwan latitudes.
- The correct action was to mark longitude as missing, not to invent or infer exact coordinates.

2. Bounding-box validation is necessary but not sufficient.
- A Taiwan range check (`116-124` lon, `20-27` lat) catches obvious errors.
- However, values inside the range can still be wrong, so additional spatial checks are needed.

3. Text location fields are not reliable geocodes by themselves.
- Facility name, village, and address help context, but they cannot guarantee a precise point without external geocoding/reference data.
- Offline cleaning can improve consistency but cannot fully restore spatial truth.

4. Non-spatial field quality affects spatial workflows.
- Phone and text formatting errors do not directly change geometry, but they reduce record quality and can break joins, QA scripts, and downstream integrations.

5. Conservative correction policy is safer for geospatial data.
- If a value is objectively malformed, standardize it.
- If a value is unrecoverable (e.g., scientific notation phone numbers), set null and document the change.
- If a spatial value is suspicious but not provably correctable, flag for manual review.

## Practical guardrails for future tasks

- Always run coordinate range checks first.
- Separate deterministic fixes from speculative fixes.
- Keep a backup before rewriting data.
- Produce line-level audit logs for every correction.
- Use manual validation for unresolved spatial anomalies.
