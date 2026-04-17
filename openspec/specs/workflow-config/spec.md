## Purpose

Parse and validate multi-workflow configuration from workflow.yaml with backwards compatibility support.

## Requirements

### Requirement: Parse multi-workflow configuration
The system SHALL parse `workflows:` section from workflow.yaml into typed WorkflowConfig objects.

#### Scenario: Valid multi-workflow config
- **WHEN** workflow.yaml contains `workflows:` with "debug" and "feature" entries
- **THEN** ServiceConfig SHALL expose `workflows: Dict[str, WorkflowConfig]`
- **AND** each WorkflowConfig SHALL contain `label`, `default`, `states`, `prompts`

#### Scenario: Backwards compatibility with single workflow
- **WHEN** workflow.yaml contains root-level `states:` without `workflows:`
- **THEN** ServiceConfig SHALL create implicit "default" workflow from root config
- **AND** existing code using `config.states` SHALL continue working

### Requirement: Validate workflow configuration
The system SHALL validate each workflow independently and across workflows.

#### Scenario: Per-workflow validation
- **WHEN** validating workflow configuration
- **THEN** each workflow SHALL pass existing state machine validation (transitions exist, gates have rework_to, etc.)

#### Scenario: Cross-workflow validation
- **WHEN** multiple workflows define `default: true`
- **THEN** validation SHALL fail with error "Multiple default workflows defined"

#### Scenario: Missing label and not default
- **WHEN** a workflow has neither `label` nor `default: true`
- **THEN** validation SHALL fail with error "Workflow must have label or be marked default"

### Requirement: Resolve workflow prompts
The system SHALL resolve prompt paths relative to the workflow.yaml directory.

#### Scenario: Workflow-scoped global prompt
- **WHEN** a workflow defines `prompts.global_prompt: prompts/debug/global.md`
- **THEN** the system SHALL load from path relative to workflow.yaml directory

#### Scenario: Workflow-scoped stage prompt
- **WHEN** a state defines `prompt: prompts/debug/reproduce.md`
- **THEN** the system SHALL load from the resolved path

### Requirement: Optional lifecycle post-run prompt path

Workflow `prompts` configuration SHALL accept an optional string field `lifecycle_post_run_prompt` naming a Markdown file path relative to the directory containing `workflow.yaml`. When omitted, the effective path SHALL be `prompts/lifecycle-post-run.md` (see `PromptsConfig.resolved_lifecycle_post_run_prompt`).

#### Scenario: Workflow-scoped post-run prompt

- **WHEN** a workflow defines `prompts.lifecycle_post_run_prompt: prompts/lifecycle-post-run.md`
- **THEN** the parsed `PromptsConfig` for that workflow SHALL store that path
- **AND** the system SHALL resolve the file relative to the workflow.yaml directory when loading the post-run template

#### Scenario: Legacy config omits post-run path

- **WHEN** a workflow sets only `lifecycle_prompt` (and omits `lifecycle_post_run_prompt`)
- **THEN** validation SHALL succeed
- **AND** the pre-run template SHALL load from `lifecycle_prompt`
- **AND** the resolved post-run template path SHALL be `prompts/lifecycle-post-run.md` for the post-run follow-up turn when `post_run` is effective

### Requirement: Pre-run lifecycle prompt remains lifecycle_prompt

The required field `lifecycle_prompt` SHALL designate the **pre-run** lifecycle Markdown template path. No new required YAML key SHALL replace `lifecycle_prompt` for backward compatibility.

#### Scenario: Naming is backward compatible

- **WHEN** existing configs use `lifecycle_prompt` only
- **THEN** parsing and validation SHALL behave as before for that field
- **AND** documentation MAY describe it as pre-run lifecycle

### Requirement: Parse agent-gate state type

The system SHALL accept `type: agent-gate` in workflow state definitions and SHALL represent it in `StateConfig` with the same execution-related fields as `agent` states (`prompt`, `linear_state`, `runner`, optional overrides) where applicable.

#### Scenario: Round-trip for agent-gate state

- **WHEN** workflow.yaml defines a state with `type: agent-gate` and a `prompt` path
- **THEN** parsing SHALL produce a `StateConfig` with `type` equal to `agent-gate`
- **AND** the `prompt` path SHALL be preserved for prompt loading

### Requirement: Validate agent-gate transitions and default

The system SHALL require that every `agent-gate` state defines a non-empty `transitions` map, a mandatory `default_transition` string that matches a key in that map, that every transition target names an existing state in the same workflow (or root state machine in legacy mode), and that the target state of `default_transition` has `type: gate` (human validation path for routing failures).

#### Scenario: Missing default_transition fails validation

- **WHEN** a state has `type: agent-gate` and `transitions` with at least one entry
- **AND** `default_transition` is absent or empty
- **THEN** validation SHALL fail with an explicit error

#### Scenario: default_transition not in transitions fails validation

- **WHEN** `default_transition` is set to `clean`
- **AND** `transitions` has no key `clean`
- **THEN** validation SHALL fail with an explicit error

#### Scenario: Unknown transition target fails validation

- **WHEN** an `agent-gate` state maps `has_findings` to a state name not defined in the workflow
- **THEN** validation SHALL fail with an explicit error

#### Scenario: default_transition target must be a gate

- **WHEN** an `agent-gate` state has `default_transition: clean`
- **AND** `transitions.clean` names an `agent` or `terminal` state
- **THEN** validation SHALL fail with an explicit error stating that the default routing target must be `type: gate`

### Requirement: State machine validation includes agent-gate

Per-workflow validation SHALL run the new `agent-gate` rules alongside existing checks for `agent`, `gate`, and `terminal` states without weakening existing gate or agent rules.

#### Scenario: Mixed workflow passes

- **WHEN** a workflow contains only valid `agent`, `gate`, `terminal`, and `agent-gate` states with consistent transitions
- **THEN** validation SHALL succeed

### Requirement: post_run defaults for agent and agent-gate

Runner states **`agent`** and **`agent-gate`** SHALL support an optional boolean field **`post_run`**. When the field is **absent** from YAML, the effective value SHALL be **true** (orchestrator may run a post-run lifecycle-only follow-up turn after a successful work turn). When **`post_run: false`** is set explicitly, the orchestrator SHALL use a **single** runner turn for that state.

#### Scenario: agent without post_run key

- **WHEN** a state has `type: agent` and the YAML omits `post_run`
- **THEN** the effective `post_run` SHALL be **true**
- **AND** the orchestrator SHALL be eligible to run the post-run follow-up turn for that state

#### Scenario: agent explicit opt-out

- **WHEN** a state has `type: agent` and `post_run: false`
- **THEN** the effective `post_run` SHALL be false
- **AND** the orchestrator SHALL NOT run the post-run follow-up turn for that state

#### Scenario: agent-gate without post_run key validates

- **WHEN** a state has `type: agent-gate` and valid `transitions`, `default_transition`, and `prompt`
- **AND** the YAML omits the `post_run` key
- **THEN** `validate_config` SHALL NOT fail solely because `post_run` is missing
- **AND** the effective post-run flag for that state SHALL be **true**

#### Scenario: agent-gate explicit opt-out

- **WHEN** a state has `type: agent-gate` and `post_run: false`
- **THEN** validation SHALL succeed
- **AND** the effective `post_run` SHALL be false

#### Scenario: agent-gate explicit two-turn closure

- **WHEN** a state has `type: agent-gate` and `post_run: true`
- **THEN** validation SHALL succeed
- **AND** the effective `post_run` SHALL be true

### Requirement: Session mode influences prompt composition

Workflow session mode SHALL determine static prompt inclusion (global + stage) for all turns.

#### Scenario: New stage with fresh session

- **WHEN** a non-rework turn targets a state configured with `session: fresh`
- **THEN** the system SHALL start a new session
- **AND** include global, stage, and lifecycle content in the assembled prompt

#### Scenario: Rework prompt composition with inherited session

- **WHEN** a rework turn targets a state configured with `session: inherit`
- **AND** a resumable session id is available
- **THEN** the system SHALL resume the prior session
- **AND** omit global prompt content from the assembled prompt
- **AND** include stage prompt content only when entering a new stage in that resumed session
- **AND** keep lifecycle content in the assembled prompt

#### Scenario: Non-rework prompt composition with inherited session

- **WHEN** a non-rework turn targets a state configured with `session: inherit`
- **AND** a resumable session id is available
- **THEN** the system SHALL resume the prior session
- **AND** omit global prompt content from the assembled prompt
- **AND** include stage prompt content only when entering a new stage in that resumed session
- **AND** keep lifecycle content in the assembled prompt

#### Scenario: Rework prompt composition with fresh session

- **WHEN** a rework turn targets a state configured with `session: fresh`
- **THEN** the system SHALL start a new session
- **AND** include global, stage, and lifecycle content in the assembled prompt

#### Scenario: Rework stage + resume session, same stage

- **WHEN** a rework turn resumes an existing session
- **AND** the stage has not changed in that resumed session
- **THEN** the system SHALL include lifecycle content only (omit global and stage)

#### Scenario: Rework stage + resume session, new stage

- **WHEN** a rework turn resumes an existing session
- **AND** the workflow has entered a new stage in that resumed session
- **THEN** the system SHALL include stage and lifecycle content
- **AND** omit global content

### Requirement: Stage prompt rendering receives rework context

Workflow prompt rendering SHALL pass `is_rework` into stage prompt template rendering context.

#### Scenario: Stage template uses rework branch

- **WHEN** a stage prompt template references `is_rework`
- **THEN** rendering SHALL evaluate template branches using the current turn's rework status
