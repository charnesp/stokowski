## ADDED Requirements

### Requirement: Lifecycle phase template variable

The lifecycle template context SHALL include `lifecycle_phase` with value `pre` when rendering the pre-run lifecycle for the primary work prompt, and value `post` when rendering the post-run lifecycle template.

#### Scenario: Primary work prompt uses pre phase

- **WHEN** the system renders the lifecycle section appended as Layer 3 in `assemble_prompt` for the first agent turn
- **THEN** `lifecycle_phase` SHALL equal `pre`

#### Scenario: Post-run follow-up uses post phase

- **WHEN** the system renders the post-run lifecycle template for the follow-up turn
- **THEN** `lifecycle_phase` SHALL equal `post`

### Requirement: Post-run rendering uses external template only

The function or code path that renders the post-run lifecycle section SHALL NOT embed closure-only markdown as string literals in Python; it SHALL load an external Markdown file and render it with Jinja2, consistent with the pre-run lifecycle externalization rule.

#### Scenario: No hardcoded post-run prose

- **WHEN** inspecting the implementation of post-run lifecycle rendering
- **THEN** there SHALL be no string literals containing the `<stokowski:report>` example block or `## Commit Information` instructional prose except in test fixtures
- **AND** production rendering SHALL load from the configured or default post-run template path

### Requirement: Closure-only instructions in post-run when two-turn closure applies

For states where **`post_run`** is **true**, normative instructions for the structured work report (`<stokowski:report>`), the `## Commit Information` four-bullet contract, mandatory `git` command reminders, and when applicable agent-gate routing markers SHALL reside in the post-run lifecycle template file, not in the pre-run (`lifecycle_prompt`) file used at Layer 3 of the **primary work** prompt.

For **`type: agent-gate`** states with **`post_run: false`**, those obligations MAY live entirely in the state's **stage** `prompt` file (for example `review-findings-route.md`); the pre-run lifecycle SHALL still supply issue context, transition keys, and any compact routing reminder so the assembled prompt stays coherent.

#### Scenario: Default repository layout for two-turn agent

- **WHEN** operators use Stokowski-supplied default prompt files for this version
- **AND** `post_run` is true for an `agent` state (including when omitted)
- **THEN** the pre-run lifecycle file SHALL omit the long generic closure block used for long work turns
- **AND** the post-run lifecycle file SHALL contain that block for the second turn

#### Scenario: Agent-gate with post_run false relies on stage plus pre-run

- **WHEN** a state has `type: agent-gate` and `post_run: false` and a stage prompt that defines report, commit bullets, and routing markers
- **THEN** the implementation SHALL NOT append the post-run template as a second turn for that state

#### Scenario: Agent-gate with post_run true uses post-run template on second turn

- **WHEN** a state has `type: agent-gate` and `post_run: true`
- **THEN** the long closure contract SHALL be deliverable via the post-run lifecycle on the second turn like for `agent` states

## MODIFIED Requirements

### Requirement: Template context variables

The lifecycle template SHALL receive all necessary context variables for rendering dynamic content.

#### Scenario: Available template variables

- **WHEN** rendering any lifecycle template (pre-run or post-run)
- **THEN** the following variables SHALL be available:
  - `issue` - full Issue object with all attributes
  - `state_name` - current state name
  - `state_cfg` - StateConfig for current state
  - `linear_states` - LinearStatesConfig
  - `workflow_states` - dict of all workflow states
  - `run` - run number
  - `is_rework` - boolean for rework status
  - `recent_comments` - list of recent comments
  - `previous_error` - previous error message
  - `transitions` - available transitions
  - `lifecycle_phase` - string `pre` or `post` identifying which lifecycle file is being rendered
