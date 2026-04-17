## Purpose

When an **`agent`** or **`agent-gate`** state has effective **`post_run: true`**, Stokowski runs a **second** runner turn whose user-visible instructions are dominated by a **post-run lifecycle** Markdown template (Jinja2). That template carries closure-only obligations: structured work report, `## Commit Information`, optional agent-gate routing markers, without re-injecting global or stage prompts unless explicitly documented.

## Requirements

### Requirement: Dedicated post-run lifecycle template

The system SHALL support a dedicated Markdown template (Jinja2) for **post-run** closure instructions: structured work report (`<stokowski:report>`), `## Commit Information` contract, mandatory `git` verification reminders, and when applicable agent-gate routing markers (`<<<STOKOWSKI_ROUTE>>>` / `<<<END_STOKOWSKI_ROUTE>>>`). That template is used **only** when the effective per-state flag **`post_run`** is **true** after the first runner turn (see `workflow-config` capability).

#### Scenario: Post-run file is distinct from pre-run

- **WHEN** both pre-run and post-run templates are configured
- **THEN** the post-run file SHALL be loaded independently from the pre-run lifecycle file
- **AND** each SHALL be rendered with the lifecycle template context including `lifecycle_phase` set to `post` for post-run (see `lifecycle-template` capability)

### Requirement: Two-turn closure when `post_run` is true

For states of type **`agent`** or **`agent-gate`** where the effective **`post_run`** flag is **true**, after the first runner invocation completes without a workflow-aborting error, the orchestrator SHALL perform a **second** runner invocation whose user-visible instructions are dominated by the rendered post-run lifecycle (global and stage prompts omitted unless an implementation explicitly documents a narrow exception in code comments and tests).

#### Scenario: Final assistant output is authoritative after post-run

- **WHEN** `post_run` is true for the current state
- **AND** the post-run turn completes
- **THEN** the orchestrator SHALL parse `<stokowski:report>` from the post-run turn assistant output
- **AND** for `agent-gate`, routing markers SHALL be resolved from that same post-run output when routing is parsed from the post-run turn
- **AND** that output SHALL be treated as the canonical submission for transition and issue comments derived from the report

#### Scenario: First turn not canonical when two-turn post-run ran

- **WHEN** `post_run` is true
- **AND** the first (work) turn assistant output contains a `<stokowski:report>` block
- **AND** the post-run turn completes afterward
- **THEN** the system SHALL still prefer the post-run turn output for canonical report parsing and SHALL NOT treat the first turn report alone as sufficient for successful closure

#### Scenario: Agent analysis states default to two-turn post-run

- **WHEN** a workflow state has `type: agent` and a state name used for analysis-only work (for example `investigate`)
- **AND** `post_run` is omitted from YAML for that state
- **THEN** the effective `post_run` SHALL be true
- **AND** the two-turn post-run sequence SHALL run

#### Scenario: Typical agent-gate single turn with explicit opt-out

- **WHEN** a workflow state has `type: agent-gate` and `post_run: false`
- **AND** the first runner invocation completes successfully
- **THEN** the orchestrator SHALL NOT enqueue a post-run follow-up turn
- **AND** the system SHALL parse `<stokowski:report>` and routing markers from the first turn assistant output only

#### Scenario: Atypical agent-gate with two-turn post-run

- **WHEN** a workflow state has `type: agent-gate` and effective `post_run` is true (explicit `true` or omitted per `workflow-config` defaults)
- **THEN** the orchestrator SHALL apply the same two-turn post-run sequence as for `agent` states

### Requirement: No comment image embedding on post-run turn

When assembling the follow-up post-run prompt, the system SHALL NOT attach comment-sourced images to the lifecycle section (no second pass of image embedding for `downloaded_images` on that turn). The work turn remains responsible for rich multimodal context when images are enabled.

#### Scenario: Post-run lifecycle text only

- **WHEN** the orchestrator builds the post-run follow-up user prompt and `post_run` is true
- **THEN** the lifecycle portion SHALL be rendered without embedding comment images into that prompt
- **AND** the first work turn assembly MAY still embed images per existing policy

### Requirement: Default post-run template path

When `lifecycle_post_run_prompt` is not set, the system SHALL resolve and render `prompts/lifecycle-post-run.md` relative to the same base directory used for `lifecycle_prompt` (workflow directory containing `workflow.yaml`), for use when the post-run follow-up turn runs (`post_run` true).

#### Scenario: Implicit default

- **GIVEN** prompts configuration omits `lifecycle_post_run_prompt`
- **WHEN** the orchestrator prepares the post-run follow-up turn and `post_run` is true for the state
- **THEN** it SHALL load `prompts/lifecycle-post-run.md` from the workflow directory
- **AND** if that file is missing the system SHALL raise `FileNotFoundError` with a path that identifies the expected post-run template
