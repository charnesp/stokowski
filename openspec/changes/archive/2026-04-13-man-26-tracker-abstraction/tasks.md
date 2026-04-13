# Tracker Abstraction Layer - Tasks

## Task 1: Create Abstract Tracker Interface

**File**: `stokowski/tracker.py` (new)

- [ ] Create abstract `TrackerClient` base class using `abc.ABC`
- [ ] Define abstract methods:
  - `fetch_candidate_issues(project_id, active_states) -> list[Issue]`
  - `fetch_issue_states_by_ids(issue_ids) -> dict[str, str]`
  - `fetch_issues_by_states(project_id, states) -> list[Issue]`
  - `post_comment(issue_id, body) -> bool`
  - `fetch_comments(issue_id) -> CommentsFetchResult`
  - `update_issue_state(issue_id, state_name) -> bool`
  - `close()`
- [ ] Create `CommentsFetchResult` dataclass
- [ ] Define base exceptions: `TrackerError`, `TrackerCommentsFetchError`
- [ ] Create `TrackerFactory` with register/create methods

## Task 2: Refactor Linear Client

**File**: `stokowski/linear.py`

- [ ] Import `TrackerClient` from tracker module
- [ ] Make `LinearClient` inherit from `TrackerClient`
- [ ] Update `CommentsFetchResult` import to come from tracker module
- [ ] Update `LinearCommentsFetchError` to inherit from `TrackerCommentsFetchError`
- [ ] Update method signatures to match interface
- [ ] Add `from_config(cls, cfg: TrackerConfig) -> LinearClient` classmethod
- [ ] Register LinearClient with TrackerFactory: `TrackerFactory.register("linear", LinearClient)`

## Task 3: Update Orchestrator

**File**: `stokowski/orchestrator.py`

- [ ] Change import: remove `LinearClient`, add `TrackerClient`
- [ ] Change import: remove `LinearCommentsFetchError`, add `TrackerCommentsFetchError`
- [ ] Change `_linear: LinearClient | None` to `_tracker: TrackerClient | None`
- [ ] Update `_ensure_linear_client()` to `_ensure_tracker()` using factory
- [ ] Update all references from `_linear` to `_tracker`
- [ ] Update exception handling for new exception hierarchy

## Task 4: Update Configuration

**File**: `stokowski/config.py`

- [ ] Add `TrackerConfig` method to create tracker instance (or keep factory in tracker.py)
- [ ] Update `validate_config()` to accept any tracker kind (not just "linear")
- [ ] Add placeholder for future tracker kinds validation

## Task 5: Testing

- [ ] Run existing tests: `uv run pytest tests/ -v`
- [ ] Verify Linear integration still works
- [ ] Test orchestrator with mocked TrackerClient

## Acceptance Criteria

- [ ] `stokowski/tracker.py` exists with full interface definition
- [ ] `LinearClient` implements `TrackerClient`
- [ ] Orchestrator depends only on `TrackerClient` interface
- [ ] All tests pass
- [ ] Linear workflow continues to function identically
