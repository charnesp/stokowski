## 1. Configuration and default templates

- [ ] 1.1 Extend `PromptsConfig` and YAML parsing (`stokowski/config.py`) with optional `lifecycle_post_run_prompt`, defaulting to `prompts/lifecycle-post-run.md` when unset; mirror behavior for per-workflow `prompts` blocks. Parse **`post_run`** on states; implement defaults and **`agent-gate`** validation per specs.
- [ ] 1.2 Add repository default `lifecycle-post-run.md` under `.stokowski/prompts/` (or workflow template directory per existing conventions) containing all moved closure content: `<stokowski:report>`, `## Commit Information`, `git` checklist, agent-gate routing block, gate approval section conditionals.
- [ ] 1.3 Trim `.stokowski/prompts/lifecycle.md` to pre-run-only content (issue context, transitions, rework, `investigate` contract, etc.); optionally rename file to `lifecycle-pre-run.md` and update `workflow.yaml` references to match the chosen naming.

## 2. Lifecycle rendering

- [ ] 2.1 Add `lifecycle_phase` (`"pre"` / `"post"`) to the Jinja context in `build_lifecycle_context` (or equivalent) and cover with unit tests in `tests/test_prompt.py`.
- [ ] 2.2 Implement a dedicated code path to load and render the post-run template (reuse `build_lifecycle_section` with phase discriminator or a thin wrapper) without hardcoding closure prose in Python.
- [ ] 2.3 Keep `assemble_prompt` Layer 3 using **only** the pre-run template; ensure resumed-session rules still include pre-run lifecycle as today unless design explicitly narrows post-run (document in code if so).

## 3. Orchestrator two-turn closure

- [ ] 3.1 Add **`post_run`** to `StateConfig` with default **`true`** when omitted for **`type: agent`**; for **`type: agent-gate`**, require explicit **`post_run`** in YAML and **validate** (fail if missing). After a successful first runner completion, enqueue the second invocation **iff** effective **`post_run`** is **true**.
- [ ] 3.2 When **`post_run`** is true: parse `<stokowski:report>` (and agent-gate routing when applicable) from the **post-run** turn. When **`post_run`** is false: parse from the **single** turn output only. Define behavior when the post-run turn fails (retry, error comment, or gate) and implement accordingly.
- [ ] 3.3 Add **`post_run: false`** to every **`agent-gate`** state in **`.stokowski/workflow.yaml`** (and `workflow.example.yaml` if present); confirm `gate`, `terminal`, and other non-runner states never use this flag.
- [ ] 3.4 Ensure post-run prompt assembly **skips** comment image embedding (`embed_images_in_prompt` / lifecycle image path) for the follow-up turn while preserving existing behavior on the first work turn.

## 4. Tests and documentation

- [ ] 4.1 Add tests for **`post_run`** defaults and validation; assert pre/post lifecycle rendering when `post_run` is true; assert single-turn parsing when `post_run` is false on `agent-gate`.
- [ ] 4.2 Add orchestration-level test (mock runner or fixture) verifying two calls in order and parsing from the second response.
- [ ] 4.3 Update `README.md`, `CLAUDE.md`, and `workflow.example.yaml` (or equivalent) to document `lifecycle_prompt` as pre-run, describe `lifecycle_post_run_prompt`, and explain the pre → work → post sequence.

## 5. Verification

- [ ] 5.1 Run the project test suite and fix regressions until green.
