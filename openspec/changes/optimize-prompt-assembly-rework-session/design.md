## Context

Prompt assembly currently concatenates global prompt, stage prompt, and lifecycle on every turn, regardless of whether the runner is resuming an existing session. This duplicates long static instructions in resumed rework flows and increases token costs. Historically, rework comment context was bounded by the latest tracking marker, which could exclude human review comments left between gate waiting and gate rework events; the current baseline now anchors this window from the latest waiting gate with a fallback to latest tracking.

The change needs to preserve safety-critical behavior (structured reporting, transitions, lifecycle context) while reducing redundant prompt payload in resumed rework turns.

## Goals / Non-Goals

**Goals:**
- Introduce deterministic prompt composition rules for three cases:
  - non-rework
  - rework + fresh session
  - rework + resumed session
- Enable stage prompt templates to conditionally render rework-only guidance through Jinja variables.
- Keep lifecycle context authoritative and always present.
- Ensure review comments for rework are sourced from the latest waiting gate boundary.
- Add focused tests so behavior is stable and explicit.

**Non-Goals:**
- Redesign the full workflow state machine.
- Persist session state to disk beyond current in-memory behavior.
- Introduce model-specific token optimizations beyond prompt-shape policy.

## Decisions

### 1) Prompt composition policy is evaluated at render time
Prompt assembly will determine whether to include stage content based on:
- current state rework status
- whether the turn is using a fresh session (`session: fresh` or missing session id) versus resume

Rationale:
- Keeps policy close to render behavior.
- Avoids changing workflow semantics.
- Preserves lifecycle as the always-on dynamic layer.

Alternatives considered:
- Config-only policy per state with no default logic: rejected (too much operator burden for a baseline fix).
- Always lifecycle-only on resume: rejected (non-rework resumed turns still need stage guidance).

### 2) Stage prompts become Jinja-aware with `is_rework`
Stage prompt rendering already uses Jinja context; we will standardize use of `is_rework` in stage templates so rework-specific instructions are conditionally included/excluded.

Rationale:
- Eliminates duplicated static text variants.
- Lets each stage own its rework nuance declaratively.

Alternatives considered:
- Separate `stage.rework_prompt` files: rejected (file sprawl and drift risk).

### 3) Rework comment window is anchored from last waiting gate
Recent human comments for lifecycle rendering will be taken from:
- `get_last_gate_waiting_timestamp(comments)` when available,
- falling back to `get_last_tracking_timestamp(comments)` otherwise.

Rationale:
- Makes reviewer feedback the primary source of truth for rework intent: these comments explain why work was rejected and what must be corrected.
- Matches reviewer mental model: comments made during gate review should remain visible when rework starts.
- Maintains compatibility where no waiting gate marker exists.

Lifecycle presentation requirement for this decision:
- In rework mode, human review comments must be visually prominent and appear before execution guidance so the agent cannot miss why the state moved to rework.
- Rework instructions should explicitly require addressing all listed human comments before claiming completion.

Alternatives considered:
- Never filter comments in rework: rejected (noise and token growth).
- Anchor to latest rework marker: rejected (drops reviewer feedback created before rework marker).

### 4) Backward-compatible defaults
If state templates do not yet use rework conditionals, behavior remains correct, only with reduced stage inclusion in resumed rework turns according to policy.

Rationale:
- Allows incremental rollout across workflow prompt sets.

## Risks / Trade-offs

- **[Risk] Stage omission in resumed rework may hide critical state rules** -> **Mitigation:** keep lifecycle mandatory constraints authoritative; add tests for expected stage inclusion/exclusion by mode.
- **[Risk] Incorrect rework detection from tracking edge cases** -> **Mitigation:** derive from parsed gate tracking and validate target-state match.
- **[Risk] Prompt template regressions due to new Jinja branches** -> **Mitigation:** template rendering tests and one end-to-end prompt assembly snapshot per mode.

## Migration Plan

1. Implement helper logic for prompt policy decision in orchestrator/prompt assembly path.
2. Introduce/verify tracking helper for last waiting gate timestamp and wire comment filtering.
3. Update stage templates to use `is_rework` for rework-only sections where needed.
4. Add/adjust unit tests for:
   - rework detection and `is_rework` propagation
   - comment-window anchor behavior
   - rework lifecycle rendering priority (human comments shown and emphasized before action guidance)
   - stage inclusion policy by session mode
5. Validate with live issue replay (e.g., MAN-29 timeline snapshots) before rollout.

Rollback:
- Revert policy gate to always include stage prompt (existing behavior) while retaining tracking/comment fixes independently.

## Resolved Decisions

- Prompt composition policy is configured globally for v1 (no per-state override in `workflow.yaml`).
- No periodic full-stage resend on long resumed sessions; lifecycle is sent each turn and already carries the required formal guards.
- No additional compact lifecycle `state constraints` block for now; current lifecycle content is considered sufficient.

## Implementation Status

- Implemented session-aware static prompt policy:
  - fresh session: include global + stage + lifecycle
  - resumed session, same stage: include lifecycle only (skip global + stage)
  - resumed session, new stage: include stage + lifecycle (skip global)
- Wired orchestration with session-id awareness for resumed turns.
- Added `is_rework` to stage-template rendering context and updated representative `.stokowski/prompts/feature/*.md` stage prompts with Jinja rework branches.
- Verified behavior with targeted tests:
  - `uv run pytest tests/test_prompt.py tests/test_agent_gate_orchestrator.py tests/test_tracking_gate_waiting.py`
- Validated MAN-29 replay snapshots using live Linear issue data (`issue(id: "MAN-29")`):
  - non-rework prompt length: 15875 chars
  - rework resumed prompt length (same-stage replay): 2497 chars
  - global prompt present in resumed rework: false
  - stage prompt present in non-rework: true
  - stage prompt present in resumed rework (same-stage replay): false
  - artifacts saved under `openspec/changes/optimize-prompt-assembly-rework-session/validation/`
