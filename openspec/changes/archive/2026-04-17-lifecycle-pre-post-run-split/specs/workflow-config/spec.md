## ADDED Requirements

### Requirement: Optional lifecycle post-run prompt path

Workflow `prompts` configuration SHALL accept an optional string field `lifecycle_post_run_prompt` naming a Markdown file path relative to the directory containing `workflow.yaml`.

#### Scenario: Workflow-scoped post-run prompt

- **WHEN** a workflow defines `prompts.lifecycle_post_run_prompt: prompts/lifecycle-post-run.md`
- **THEN** the parsed `PromptsConfig` for that workflow SHALL store that path
- **AND** the system SHALL resolve the file relative to the workflow.yaml directory when loading prompts

### Requirement: Pre-run lifecycle prompt remains lifecycle_prompt

The existing required field `lifecycle_prompt` SHALL continue to designate the **pre-run** lifecycle Markdown template path; documentation MAY describe it as pre-run lifecycle. No new required YAML key SHALL replace `lifecycle_prompt` for backward compatibility.

#### Scenario: Legacy config unchanged

- **WHEN** a workflow sets only `lifecycle_prompt` (and omits `lifecycle_post_run_prompt`)
- **THEN** validation SHALL succeed as today for that field
- **AND** the pre-run template SHALL load from `lifecycle_prompt`
- **AND** the post-run template SHALL use the default path `prompts/lifecycle-post-run.md` per capability `lifecycle-post-run`

### Requirement: Per-state post_run for runner states

State definitions with `type: agent` or `type: agent-gate` SHALL support a boolean field **`post_run`**. For **`type: agent`**, the field **MAY** be omitted (see default scenario). For **`type: agent-gate`**, the field **MUST** be present (see separate requirement).

#### Scenario: Default true when omitted on agent

- **WHEN** a state has `type: agent` and the YAML omits `post_run`
- **THEN** the parsed `StateConfig` SHALL treat effective `post_run` as **true**
- **AND** the orchestrator SHALL be eligible to run the post-run follow-up turn for that state

#### Scenario: Agent explicit opt-out

- **WHEN** a state has `type: agent` and `post_run: false`
- **THEN** effective `post_run` SHALL be false
- **AND** the orchestrator SHALL NOT run the post-run follow-up turn for that state

### Requirement: Agent-gate must declare post_run explicitly

For every state with **`type: agent-gate`**, the YAML definition **SHALL** include a **`post_run`** key with a boolean value. Validation **SHALL** fail if `post_run` is absent on an `agent-gate` state.

#### Scenario: Typical gate documents single-turn intent

- **WHEN** a state has `type: agent-gate` and `post_run: false`
- **THEN** validation SHALL succeed
- **AND** effective `post_run` SHALL be false

#### Scenario: Atypical gate opts into two-turn closure

- **WHEN** a state has `type: agent-gate` and `post_run: true`
- **THEN** validation SHALL succeed
- **AND** effective `post_run` SHALL be true

#### Scenario: Missing post_run on agent-gate fails validation

- **WHEN** a state has `type: agent-gate` and the YAML omits `post_run`
- **THEN** validation SHALL fail with an explicit error that `post_run` is required for `agent-gate` states
