"""Tracker abstraction layer for issue tracking systems.

This module defines the abstract interface that all tracker implementations must follow,
along with common types and exceptions.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar

from .models import BlockerRef, Issue


# Type variable for TrackerConfig subclasses
T = TypeVar("T", bound="TrackerConfig")

logger = logging.getLogger("stokowski.tracker")


@dataclass(frozen=True)
class CommentsFetchResult:
    """Result of fetching comments from a tracker.

    Attributes:
        nodes: List of comment nodes (each roughly {id, body, createdAt})
        complete: True when the full history was loaded successfully
    """

    nodes: list[dict]
    complete: bool


class CommentsFetchError(RuntimeError):
    """Raised when the first page of issue comments cannot be fetched."""


class TrackerClient(ABC):
    """Abstract base class for tracker implementations.

    All tracker implementations (Linear, GitHub Issues, etc.) must inherit from
    this class and implement the required methods.
    """

    @abstractmethod
    async def close(self) -> None:
        """Close any open connections and cleanup resources."""
        ...

    @abstractmethod
    async def fetch_candidate_issues(
        self, project_id: str, active_states: list[str]
    ) -> list[Issue]:
        """Fetch all issues in active states for the project.

        Args:
            project_id: The project identifier (e.g., Linear project slug)
            active_states: List of state names to fetch issues from

        Returns:
            List of Issue objects matching the criteria
        """
        ...

    @abstractmethod
    async def fetch_issue_states_by_ids(self, issue_ids: list[str]) -> dict[str, str]:
        """Fetch current states for given issue IDs.

        Args:
            issue_ids: List of issue IDs to look up

        Returns:
            Dictionary mapping issue_id -> state_name
        """
        ...

    @abstractmethod
    async def fetch_issues_by_states(
        self, project_id: str, states: list[str]
    ) -> list[Issue]:
        """Fetch issues in specific states (used for terminal cleanup).

        Args:
            project_id: The project identifier
            states: List of state names to fetch

        Returns:
            List of Issue objects in the specified states
        """
        ...

    @abstractmethod
    async def post_comment(self, issue_id: str, body: str) -> bool:
        """Post a comment on an issue.

        Args:
            issue_id: The issue ID to comment on
            body: The comment body text

        Returns:
            True on success, False otherwise
        """
        ...

    @abstractmethod
    async def fetch_comments(self, issue_id: str) -> CommentsFetchResult:
        """Fetch all comments on an issue.

        Args:
            issue_id: The issue ID to fetch comments for

        Returns:
            CommentsFetchResult with nodes and complete flag

        Raises:
            CommentsFetchError: GraphQL/network error before any page succeeds.
                After at least one successful page, errors return complete=False
                with the nodes collected so far.
        """
        ...

    @abstractmethod
    async def update_issue_state(self, issue_id: str, state_name: str) -> bool:
        """Move an issue to a new state by name.

        Args:
            issue_id: The issue ID to update
            state_name: The target state name

        Returns:
            True on success, False otherwise
        """
        ...


class TrackerConfig(ABC):
    """Abstract base class for tracker-specific configuration."""

    @classmethod
    @abstractmethod
    def from_dict(cls, config: dict[str, Any]) -> "TrackerConfig":
        """Create configuration from dictionary.

        Args:
            config: Dictionary containing configuration values.

        Returns:
            TrackerConfig instance.
        """
        ...

    @abstractmethod
    def create_client(self) -> TrackerClient:
        """Create and return a configured tracker client instance."""
        ...


class TrackerFactory:
    """Factory for creating tracker clients based on configuration.

    Supports multiple tracker implementations and provides a centralized
    way to instantiate the correct client based on config.
    """

    _registry: dict[str, Any] = {}

    @classmethod
    def register(cls, kind: str, config_class: Any) -> None:
        """Register a tracker implementation.

        Args:
            kind: The tracker type identifier (e.g., "linear", "github")
            config_class: The configuration class for this tracker type
        """
        cls._registry[kind] = config_class
        logger.debug(f"Registered tracker type '{kind}' with config class {config_class.__name__}")

    @classmethod
    def create_client(cls, kind: str, config: dict[str, Any]) -> TrackerClient:
        """Create a tracker client based on kind and config.

        Args:
            kind: The tracker type identifier
            config: Configuration dictionary for the tracker

        Returns:
            Configured TrackerClient instance

        Raises:
            ValueError: If the tracker type is not registered
        """
        if kind not in cls._registry:
            registered = list(cls._registry.keys())
            raise ValueError(
                f"Unknown tracker type '{kind}'. "
                f"Registered types: {registered}"
            )

        config_class = cls._registry[kind]
        tracker_config = config_class.from_dict(config)
        return tracker_config.create_client()

    @classmethod
    def get_supported_kinds(cls) -> list[str]:
        """Return list of registered tracker type identifiers."""
        return list(cls._registry.keys())


__all__ = [
    "TrackerClient",
    "TrackerConfig",
    "TrackerFactory",
    "CommentsFetchResult",
    "CommentsFetchError",
]

# Note: Tracker implementations should register themselves with TrackerFactory
# For example, in linear.py:
#   from stokowski.tracker import TrackerFactory
#   TrackerFactory.register("linear", LinearTrackerConfig)
#
# Then in the application's main entry point, import the implementation
# to trigger registration:
#   from stokowski import linear  # noqa: F401
