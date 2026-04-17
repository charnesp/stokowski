## Why

Current prompt assembly repeats large static instructions on every turn, which increases token usage and causes avoidable redundancy. Rework feedback anchoring was corrected to use the latest waiting gate boundary, but prompt composition still repeats large static stage content in resumed rework sessions.

## What Changes

- Introduce a prompt assembly policy that adapts stage-prompt inclusion based on rework status and session mode (`fresh` vs resumed).
- Render stage prompt files through Jinja so rework-only sections can be conditionally included/excluded instead of hardcoded duplication.
- Preserve full context delivery (global + lifecycle) where needed, while skipping stage prompt on resumed rework turns to reduce repetition.
- Align human-comment injection with gate workflow intent by sourcing comments from the latest waiting gate boundary.
- Add tests that lock expected behavior for prompt composition, rework context propagation, and comment-window selection.

## Capabilities

### New Capabilities
- `prompt-assembly-policy`: Define deterministic prompt-composition rules per turn (non-rework, rework+fresh, rework+resume) to reduce redundancy without losing critical operational context.

### Modified Capabilities
- `lifecycle-template`: Adjust recent human comment window to be anchored from the latest waiting gate context so rework prompts include the right reviewer feedback.
- `workflow-config`: Clarify and enforce how `session: inherit|fresh` influences prompt composition and session resumption behavior during rework.

## Impact

- Affected code: `stokowski/orchestrator.py`, `stokowski/prompt.py`, `stokowski/tracking.py`, and prompt templates under `.stokowski/prompts/`.
- Affected tests: prompt assembly, orchestrator rework handling, and tracking timestamp/filtering suites.
- Runtime impact: lower repeated prompt tokens on resumed rework turns; clearer and more consistent reviewer-feedback context.
