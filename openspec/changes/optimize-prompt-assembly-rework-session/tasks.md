## 1. Prompt Composition Policy

- [x] 1.1 Add a prompt-composition decision path that distinguishes non-rework, rework+fresh, and rework+resume turns.
- [x] 1.2 Wire the policy into orchestrator prompt rendering so resumed rework can omit stage prompt content while retaining lifecycle.
- [x] 1.3 Add unit tests for stage inclusion/exclusion behavior across the three policy modes.

## 2. Stage Template Rework Branching

- [x] 2.1 Ensure stage prompt rendering receives `is_rework` context in all state-machine prompt paths.
- [x] 2.2 Update representative `.stokowski/prompts/*/*.md` stage prompts to use Jinja rework branches for rework-only instructions.
- [x] 2.3 Add template rendering tests to verify rework branches are included/excluded correctly.

## 3. Gate-Anchored Human Comment Window

- [x] 3.1 Add/maintain tracking helper(s) to resolve the last waiting-gate timestamp for comment filtering.
- [x] 3.2 Update lifecycle recent-comment filtering to anchor from last waiting gate, with fallback to last tracking timestamp.
- [x] 3.3 Add tests covering waiting-gate anchor, fallback behavior, and rework lifecycle comment visibility.

## 4. Validation and Regression Safety

- [x] 4.1 Run targeted test suites for prompt assembly, orchestrator rework handling, and tracking timestamp logic.
- [x] 4.2 Validate MAN-29 replay snapshots for both rework and non-rework prompt outputs.
- [x] 4.3 Document behavior changes in change artifacts and confirm `/opsx:apply` readiness.

Notes:
- MAN-29 replay snapshots generated from live Linear data:
  - `openspec/changes/optimize-prompt-assembly-rework-session/validation/man-29-non-rework.prompt.md`
  - `openspec/changes/optimize-prompt-assembly-rework-session/validation/man-29-rework-resumed.prompt.md`
  - `openspec/changes/optimize-prompt-assembly-rework-session/validation/man-29-validation-summary.json`
