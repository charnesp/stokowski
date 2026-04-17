## ADDED Requirements

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
