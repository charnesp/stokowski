# Route after automated code review (agent-gate)

You have just **finished** the adversarial `code-review` pass (see prior context). Your job now is only to **classify the outcome** and emit the machine route — no new code review prose beyond what goes into `<stokowski:report>`.

**Transitions (use exactly one key in `<<<STOKOWSKI_ROUTE>>>`):**

- **`has_findings`** — blocking or important issues were found; the issue should go to **`correct-findings-code-review`** to fix them, then re-enter **`code-review`** automatically after that agent completes.
- **`clean`** — no meaningful findings; proceed to the human **`merge-review`** gate.
- **`needs_human`** — ambiguous, conflicting, or you cannot decide safely; Stokowski also uses this as the **default** if routing JSON is missing or invalid → same as sending to **`merge-review`**.

Output **both** lifecycle blocks: `<stokowski:report>` (summary for Linear) and the `<<<STOKOWSKI_ROUTE>>>` … `<<<END_STOKOWSKI_ROUTE>>>` JSON with `"transition": "<key>"`.
