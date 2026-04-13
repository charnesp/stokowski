# Tracker Abstraction Layer

## Overview

Create a complete abstraction layer between the Stokowski orchestrator and the underlying issue tracker. This will decouple the application from Linear-specific implementations and enable future support for other trackers (GitHub Issues, Jira, etc.).

## Problem Statement

Currently, the codebase has tight coupling to Linear:

1. `LinearClient` in `linear.py` is instantiated directly in the orchestrator
2. `LinearCommentsFetchError` is imported and handled specifically
3. Configuration assumes Linear GraphQL endpoint structure
4. Issue state management is Linear-specific

This makes it impossible to swap in a different tracker without modifying core orchestrator code.

## Solution

Introduce an abstract `TrackerClient` interface that defines the contract between the orchestrator and any issue tracker implementation. Refactor the orchestrator to depend only on this interface.

### Key Design Decisions

1. **Abstract Base Class**: Define `TrackerClient` using Python's `abc.ABC` to enforce the interface contract
2. **Factory Pattern**: Create a tracker factory that instantiates the appropriate client based on `config.tracker.kind`
3. **Generic Issue Model**: Use the existing `Issue` model (already generic) across all trackers
4. **Comment Abstraction**: Abstract comment fetching/creation since different trackers have different formats

## Scope

### In Scope

- Create abstract `TrackerClient` base class
- Refactor `LinearClient` to implement the interface
- Create tracker factory for client instantiation
- Update orchestrator to use the abstraction
- Update config validation for generic tracker support

### Out of Scope

- Implementing actual GitHub/Jira clients (future work)
- Changing the `Issue` model structure (it's already generic)
- Modifying workflow state machine logic (state names are already configurable via `linear_states`)

## Success Criteria

1. `orchestrator.py` imports only from `tracker.py` (the interface), not `linear.py`
2. `LinearClient` implements `TrackerClient` interface
3. Configuration validation passes with `tracker.kind: linear` and can be extended for other kinds
4. All existing tests pass
5. No behavioral changes for Linear users

## References

- Current Linear implementation: `stokowski/linear.py`
- Orchestrator: `stokowski/orchestrator.py`
- Configuration: `stokowski/config.py`
- Issue model: `stokowski/models.py`
