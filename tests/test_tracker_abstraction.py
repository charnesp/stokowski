"""Tests for the tracker abstraction layer."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock
from stokowski.tracker import (
    TrackerClient,
    TrackerConfig,
    TrackerFactory,
    CommentsFetchResult,
    CommentsFetchError,
)
from stokowski.linear import LinearClient, LinearTrackerConfig


class TestCommentsFetchResult:
    """Tests for CommentsFetchResult dataclass."""

    def test_create_with_nodes_and_complete(self):
        """Should create a result with nodes and complete flag."""
        nodes = [{"id": "c1", "body": "comment 1"}, {"id": "c2", "body": "comment 2"}]
        result = CommentsFetchResult(nodes=nodes, complete=True)

        assert result.nodes == nodes
        assert result.complete is True

    def test_create_empty(self):
        """Should create an empty result."""
        result = CommentsFetchResult(nodes=[], complete=True)

        assert result.nodes == []
        assert result.complete is True

    def test_immutable(self):
        """Should be immutable (frozen dataclass)."""
        result = CommentsFetchResult(nodes=[], complete=True)

        with pytest.raises(AttributeError):
            result.complete = False  # type: ignore[misc]


class TestCommentsFetchError:
    """Tests for CommentsFetchError exception."""

    def test_raise_with_message(self):
        """Should raise with a message."""
        with pytest.raises(CommentsFetchError, match="Failed to fetch"):
            raise CommentsFetchError("Failed to fetch comments")

    def test_is_runtime_error(self):
        """Should be a RuntimeError subclass."""
        assert issubclass(CommentsFetchError, RuntimeError)


class TestTrackerClientAbstract:
    """Tests that TrackerClient is properly abstract."""

    def test_cannot_instantiate_base(self):
        """Should not be able to instantiate TrackerClient directly."""
        with pytest.raises(TypeError):
            TrackerClient()  # type: ignore[abstract]

    def test_requires_close_method(self):
        """Should require close method to be implemented."""

        class IncompleteClient(TrackerClient):
            pass

        with pytest.raises(TypeError):
            IncompleteClient()  # type: ignore[abstract]

    def test_requires_all_methods(self):
        """Should require all abstract methods to be implemented."""

        class PartialClient(TrackerClient):
            async def close(self):
                pass

        with pytest.raises(TypeError):
            PartialClient()  # type: ignore[abstract]


class MockTrackerClient(TrackerClient):
    """A mock implementation for testing the abstract interface."""

    def __init__(self, issues=None):
        from stokowski.models import Issue
        self.issues = issues or []
        self.comments = {}
        self.closed = False
        self.state_updates = []
        self.commented_issues = []

    async def close(self):
        self.closed = True

    async def fetch_candidate_issues(self, project_id: str, active_states: list[str]):
        from stokowski.models import Issue
        return [
            issue for issue in self.issues
            if issue.state in active_states
        ]

    async def fetch_issue_states_by_ids(self, issue_ids: list[str]):
        return {
            issue.id: issue.state
            for issue in self.issues
            if issue.id in issue_ids
        }

    async def fetch_issues_by_states(self, project_id: str, states: list[str]):
        return [
            issue for issue in self.issues
            if issue.state in states
        ]

    async def post_comment(self, issue_id: str, body: str):
        self.commented_issues.append((issue_id, body))
        return True

    async def fetch_comments(self, issue_id: str):
        nodes = self.comments.get(issue_id, [])
        return CommentsFetchResult(nodes=nodes, complete=True)

    async def update_issue_state(self, issue_id: str, state_name: str):
        self.state_updates.append((issue_id, state_name))
        return True


class TestTrackerClientInterface:
    """Tests for the TrackerClient interface using MockTrackerClient."""

    @pytest.fixture
    def mock_client(self):
        return MockTrackerClient()

    @pytest.fixture
    def sample_issue(self):
        from datetime import datetime, UTC
        from stokowski.models import Issue, BlockerRef
        return Issue(
            id="issue-123",
            identifier="PROJ-123",
            title="Test Issue",
            description="A test issue",
            priority=1,
            state="In Progress",
            branch_name="feature/test",
            url="https://example.com/issues/123",
            labels=["bug", "urgent"],
            blocked_by=[],
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    @pytest.mark.anyio
    async def test_close(self, mock_client):
        """Should mark client as closed."""
        await mock_client.close()
        assert mock_client.closed is True

    @pytest.mark.anyio
    async def test_fetch_candidate_issues(self, mock_client, sample_issue):
        """Should fetch issues matching active states."""
        mock_client.issues = [sample_issue]

        issues = await mock_client.fetch_candidate_issues("proj-1", ["In Progress"])

        assert len(issues) == 1
        assert issues[0].identifier == "PROJ-123"

    @pytest.mark.anyio
    async def test_fetch_candidate_issues_no_match(self, mock_client, sample_issue):
        """Should return empty list when no states match."""
        mock_client.issues = [sample_issue]

        issues = await mock_client.fetch_candidate_issues("proj-1", ["Done"])

        assert len(issues) == 0

    @pytest.mark.anyio
    async def test_fetch_issue_states_by_ids(self, mock_client, sample_issue):
        """Should fetch states for given issue IDs."""
        mock_client.issues = [sample_issue]

        states = await mock_client.fetch_issue_states_by_ids(["issue-123"])

        assert states == {"issue-123": "In Progress"}

    @pytest.mark.anyio
    async def test_fetch_issue_states_empty(self, mock_client):
        """Should return empty dict for empty issue IDs."""
        states = await mock_client.fetch_issue_states_by_ids([])

        assert states == {}

    @pytest.mark.anyio
    async def test_fetch_issues_by_states(self, mock_client, sample_issue):
        """Should fetch issues in specified states."""
        mock_client.issues = [sample_issue]

        issues = await mock_client.fetch_issues_by_states("proj-1", ["In Progress"])

        assert len(issues) == 1

    @pytest.mark.anyio
    async def test_post_comment(self, mock_client):
        """Should post a comment."""
        success = await mock_client.post_comment("issue-123", "Test comment")

        assert success is True
        assert mock_client.commented_issues == [("issue-123", "Test comment")]

    @pytest.mark.anyio
    async def test_fetch_comments(self, mock_client):
        """Should fetch comments for an issue."""
        mock_client.comments = {
            "issue-123": [
                {"id": "c1", "body": "Comment 1", "createdAt": "2024-01-01"},
                {"id": "c2", "body": "Comment 2", "createdAt": "2024-01-02"},
            ]
        }

        result = await mock_client.fetch_comments("issue-123")

        assert result.complete is True
        assert len(result.nodes) == 2
        assert result.nodes[0]["body"] == "Comment 1"

    @pytest.mark.anyio
    async def test_fetch_comments_empty(self, mock_client):
        """Should handle empty comments."""
        result = await mock_client.fetch_comments("issue-456")

        assert result.complete is True
        assert result.nodes == []

    @pytest.mark.anyio
    async def test_update_issue_state(self, mock_client):
        """Should update issue state."""
        success = await mock_client.update_issue_state("issue-123", "Done")

        assert success is True
        assert mock_client.state_updates == [("issue-123", "Done")]


class TestTrackerConfigAbstract:
    """Tests that TrackerConfig is properly abstract."""

    def test_cannot_instantiate_base(self):
        """Should not be able to instantiate TrackerConfig directly."""
        with pytest.raises(TypeError):
            TrackerConfig()  # type: ignore[abstract]

    def test_requires_create_client(self):
        """Should require create_client method."""

        class IncompleteConfig(TrackerConfig):
            pass

        with pytest.raises(TypeError):
            IncompleteConfig()  # type: ignore[abstract]


class MockTrackerConfig(TrackerConfig):
    """A mock configuration for testing."""

    def __init__(self, endpoint: str = "", api_key: str = ""):
        self.endpoint = endpoint
        self.api_key = api_key

    @classmethod
    def from_dict(cls, config: dict):  # type: ignore[override]
        return cls(
            endpoint=config.get("endpoint", ""),
            api_key=config.get("api_key", ""),
        )

    def create_client(self) -> "MockTrackerClient":
        return MockTrackerClient()


class TestTrackerFactory:
    """Tests for TrackerFactory."""

    def test_register_tracker_type(self):
        """Should be able to register a tracker type."""
        TrackerFactory.register("mock", MockTrackerConfig)

        assert "mock" in TrackerFactory.get_supported_kinds()

    def test_create_client_registered(self):
        """Should create client for registered type."""
        TrackerFactory.register("mock2", MockTrackerConfig)

        client = TrackerFactory.create_client("mock2", {"endpoint": "http://test", "api_key": "key123"})

        assert isinstance(client, MockTrackerClient)

    def test_create_client_unknown_type(self):
        """Should raise error for unknown tracker type."""
        with pytest.raises(ValueError, match="Unknown tracker type"):
            TrackerFactory.create_client("unknown", {})

    def test_create_client_includes_error_message(self):
        """Should include registered types in error message."""
        TrackerFactory.register("mock3", MockTrackerConfig)

        with pytest.raises(ValueError) as exc_info:
            TrackerFactory.create_client("nonexistent", {})

        error_msg = str(exc_info.value)
        assert "nonexistent" in error_msg
        assert "mock3" in error_msg


class TestLinearClientImplementsInterface:
    """Tests that LinearClient properly implements TrackerClient."""

    def test_is_tracker_client_subclass(self):
        """Should be a subclass of TrackerClient."""
        assert issubclass(LinearClient, TrackerClient)

    def test_has_required_methods(self):
        """Should have all required methods from TrackerClient."""
        required_methods = [
            'close',
            'fetch_candidate_issues',
            'fetch_issue_states_by_ids',
            'fetch_issues_by_states',
            'post_comment',
            'fetch_comments',
            'update_issue_state',
        ]

        for method in required_methods:
            assert hasattr(LinearClient, method), f"LinearClient missing {method}"


class TestLinearTrackerConfigImplementsInterface:
    """Tests that LinearTrackerConfig properly implements TrackerConfig."""

    def test_is_tracker_config_subclass(self):
        """Should be a subclass of TrackerConfig."""
        assert issubclass(LinearTrackerConfig, TrackerConfig)

    def test_has_from_dict(self):
        """Should have from_dict class method."""
        assert hasattr(LinearTrackerConfig, 'from_dict')
        assert callable(getattr(LinearTrackerConfig, 'from_dict'))

    def test_has_create_client(self):
        """Should have create_client method."""
        assert hasattr(LinearTrackerConfig, 'create_client')


class TestLinearFactoryRegistration:
    """Tests that Linear is properly registered with the factory."""

    def test_linear_is_registered(self):
        """Should have 'linear' registered in the factory."""
        kinds = TrackerFactory.get_supported_kinds()
        assert "linear" in kinds

    def test_create_linear_client(self):
        """Should be able to create a Linear client via factory."""
        client = TrackerFactory.create_client("linear", {
            "endpoint": "https://api.linear.app/graphql",
            "api_key": "test-key",
            "project_slug": "test-project",
        })

        assert isinstance(client, LinearClient)
