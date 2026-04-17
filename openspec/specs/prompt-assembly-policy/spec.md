## Purpose

Define how **static** prompt layers (global prompt, stage prompt) are **included or omitted** depending on **session continuity** and **stage changes**, while **lifecycle** content generally remains in the assembled user prompt. Stage prompts are **Jinja** templates and SHALL receive **rework** context (`is_rework`) for conditional sections.

## Requirements

### Requirement: Session-aware static prompt inclusion

The system SHALL compose prompts using a session-aware policy for static prompt inclusion (global + stage).

#### Scenario: New stage + fresh session includes global, stage, and lifecycle

- **WHEN** the current turn is not a rework turn
- **AND** the turn starts a fresh session
- **THEN** the assembled prompt SHALL include the rendered global prompt
- **AND** the assembled prompt SHALL include the rendered stage prompt
- **AND** the assembled prompt SHALL include lifecycle content

#### Scenario: Rework stage + fresh session includes global, stage, and lifecycle

- **WHEN** the current turn is a rework turn
- **AND** the turn starts a fresh session
- **THEN** the assembled prompt SHALL include the rendered global prompt
- **AND** the assembled prompt SHALL include the rendered stage prompt
- **AND** the assembled prompt SHALL include lifecycle content

#### Scenario: Same stage + resume session includes lifecycle only

- **WHEN** the turn resumes an existing session
- **AND** the stage has not changed in that resumed session
- **THEN** the assembled prompt SHALL omit rendered global prompt content
- **AND** the assembled prompt SHALL omit rendered stage prompt content
- **AND** the assembled prompt SHALL still include lifecycle content

#### Scenario: New stage + resume session includes stage and lifecycle

- **WHEN** the turn resumes an existing session
- **AND** the workflow has entered a new stage in that resumed session
- **THEN** the assembled prompt SHALL omit rendered global prompt content
- **AND** the assembled prompt SHALL include rendered stage prompt content for that new stage
- **AND** the assembled prompt SHALL include lifecycle content

### Requirement: Stage prompt templates support rework conditionals

Stage prompts SHALL be rendered as Jinja templates with rework context variables.

#### Scenario: Rework sections are excluded for non-rework turns

- **WHEN** a stage prompt template contains rework-only Jinja branches
- **AND** `is_rework` is false
- **THEN** rework-only sections SHALL NOT appear in rendered stage prompt content

#### Scenario: Rework sections are included for rework turns

- **WHEN** a stage prompt template contains rework-only Jinja branches
- **AND** `is_rework` is true
- **THEN** rework-only sections SHALL appear in rendered stage prompt content
