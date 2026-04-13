# Tracker Abstraction Layer - Design

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Orchestrator                                    │
│                          (depends on interface)                         │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   TrackerClient       │
                    │   (abc.ABC)           │
                    └───────────┬───────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
  ┌────────▼────────┐  ┌───────▼────────┐  ┌──────▼──────┐
  │  LinearClient     │  │ GitHubClient   │  │ JiraClient  │
  │  (GraphQL)        │  │ (REST/GraphQL) │  │ (REST)       │
  └───────────────────┘  └────────────────┘  └─────────────┘
```

## Interface Design

### Abstract Base Class

```python
# stokowski/tracker.py

class TrackerClient(abc.ABC):
    """Abstract interface for issue tracker clients."""

    @abc.abstractmethod
    async def fetch_candidate_issues(
        self, project_id: str, active_states: list[str]
    ) -> list[Issue]:
        """Fetch all issues in active states for the project."""
        ...

    @abc.abstractmethod
    async def fetch_issue_states_by_ids(
        self, issue_ids: list[str]
    ) -> dict[str, str]:
        """Fetch current states for given issue IDs. Returns {id: state_name}."""
        ...

    @abc.abstractmethod
    async def fetch_issues_by_states(
        self, project_id: str, states: list[str]
    ) -> list[Issue]:
        """Fetch issues in specific states (for terminal cleanup)."""
        ...

    @abc.abstractmethod
    async def post_comment(self, issue_id: str, body: str) -> bool:
        """Post a comment on an issue. Returns True on success."""
        ...

    @abc.abstractmethod
    async def fetch_comments(self, issue_id: str) -> CommentsFetchResult:
        """Fetch all comments on an issue."""
        ...

    @abc.abstractmethod
    async def update_issue_state(self, issue_id: str, state_name: str) -> bool:
        """Move an issue to a new state by name. Returns True on success."""
        ...

    @abc.abstractmethod
    async def close(self):
        """Close any open connections/resources."""
        ...
```

### Exceptions

```python
class TrackerError(RuntimeError):
    """Base exception for tracker operations."""

class TrackerCommentsFetchError(TrackerError):
    """Raised when comments cannot be fetched."""

class TrackerAuthError(TrackerError):
    """Raised when authentication fails."""

class TrackerNotFoundError(TrackerError):
    """Raised when a resource is not found."""
```

## Refactoring Plan

### Phase 1: Create the Abstraction Layer

1. **Create `stokowski/tracker.py`**
   - Define `TrackerClient` ABC with all required abstract methods
   - Define `CommentsFetchResult` dataclass (moved from linear.py)
   - Define tracker-specific exceptions

2. **Update `stokowski/linear.py`**
   - Rename `LinearClient` methods to match interface
   - Make `LinearClient` inherit from `TrackerClient`
   - Update imports from `linear.py` to `tracker.py` in orchestrator
   - Keep `LinearCommentsFetchError` as subclass of `TrackerCommentsFetchError`

### Phase 2: Update the Orchestrator

1. **Update `stokowski/orchestrator.py`**
   - Change import: `from .linear import LinearClient` → `from .tracker import TrackerClient`
   - Change `_linear: LinearClient | None` → `_tracker: TrackerClient | None`
   - Update `_ensure_linear_client()` to use factory

### Phase 3: Update Configuration

1. **Update `stokowski/config.py`**
   - Add `resolved_tracker_kind()` method (for future extensibility)
   - Update `validate_config()` to support generic tracker kinds
   - Keep Linear-specific fields for now (they'll be used by LinearClient)

### Phase 4: Create Tracker Factory

1. **Create factory in `stokowski/tracker.py` or separate module**

```python
class TrackerFactory:
    """Factory for creating tracker clients based on configuration."""

    _registry: dict[str, type[TrackerClient]] = {}

    @classmethod
    def register(cls, kind: str, client_class: type[TrackerClient]):
        """Register a tracker client implementation."""
        cls._registry[kind] = client_class

    @classmethod
    def create(cls, cfg: TrackerConfig) -> TrackerClient:
        """Create a tracker client based on config."""
        kind = cfg.kind
        if kind not in cls._registry:
            raise ValueError(f"Unknown tracker kind: {kind}")
        return cls._registry[kind].from_config(cfg)
```

## Files to Modify

| File | Changes |
|------|---------|
| `stokowski/tracker.py` | **NEW** - Abstract interface, factory, exceptions |
| `stokowski/linear.py` | Make `LinearClient` implement `TrackerClient` |
| `stokowski/orchestrator.py` | Use `TrackerClient` interface |
| `stokowski/config.py` | Update for generic tracker support |

## Backward Compatibility

- Configuration format remains unchanged
- Linear continues to work exactly as before
- The `linear_states` config section name can remain for now (changing it would be breaking)
- Environment variable names (LINEAR_API_KEY, etc.) remain for Linear client

## Testing Strategy

1. Unit tests for the factory pattern
2. Ensure Linear client still passes integration tests
3. Verify orchestrator works with mocked TrackerClient

## Future Extensibility

Once this abstraction is in place, adding a new tracker requires:

1. Implement `TrackerClient` interface
2. Register with `TrackerFactory.register("newtracker", NewTrackerClient)`
3. Add tracker-specific config section
4. Update documentation

The orchestrator and workflow logic remain unchanged.
