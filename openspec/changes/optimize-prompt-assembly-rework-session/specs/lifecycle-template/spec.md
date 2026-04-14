## ADDED Requirements

### Requirement: Recent comments are anchored from latest waiting gate
The lifecycle recent human comment window SHALL be anchored from the most recent gate marker with status `waiting` when available.

#### Scenario: Waiting gate timestamp is used as boundary
- **WHEN** issue comments include a gate tracking marker with status `waiting`
- **THEN** the system SHALL use the latest waiting gate timestamp as the lower bound for `recent_comments`
- **AND** only non-tracking human comments after that timestamp SHALL be included

#### Scenario: Fallback to latest tracking when no waiting gate exists
- **WHEN** issue comments contain no gate marker with status `waiting`
- **THEN** the system SHALL use the latest tracking timestamp as the lower bound for `recent_comments`
- **AND** only non-tracking human comments after that timestamp SHALL be included

### Requirement: Rework lifecycle section includes anchored review comments
Rework lifecycle rendering SHALL show review comments derived from the anchored recent comment window.

#### Scenario: Rework prompt shows comments from gate review period
- **WHEN** a rework turn is rendered
- **AND** human comments exist after the last waiting gate boundary
- **THEN** those comments SHALL appear in the lifecycle rework section

### Requirement: Rework lifecycle prioritizes human review feedback
In rework mode, lifecycle content SHALL prioritize human review comments as the primary explanation for why prior work was rejected.

#### Scenario: Rework prompt emphasizes review feedback before action
- **WHEN** a rework turn is rendered with human comments
- **THEN** the lifecycle SHALL present those comments before execution guidance
- **AND** the lifecycle SHALL explicitly instruct the agent to address all listed comments before completion
