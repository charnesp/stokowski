"""Regression tests for Linear issue state fetch path."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from stokowski.linear import ISSUES_BY_STATES_QUERY, LinearClient


def test_issues_by_states_query_fetches_labels():
    """Gate/rework workflow resolution requires labels in this fetch path."""
    assert "labels { nodes { name } }" in ISSUES_BY_STATES_QUERY


@pytest.mark.asyncio
async def test_fetch_issues_by_states_includes_labels_on_issues():
    client = LinearClient("https://api.linear.app/graphql", "test-key")
    page = {
        "issues": {
            "pageInfo": {"hasNextPage": False, "endCursor": None},
            "nodes": [
                {
                    "id": "issue-1",
                    "identifier": "MAN-35",
                    "state": {"name": "Gate Approved"},
                    "labels": {"nodes": [{"name": "Debug"}, {"name": "Bug"}]},
                }
            ],
        }
    }

    with patch.object(client, "_graphql", new_callable=AsyncMock) as mock_gql:
        mock_gql.return_value = page
        issues = await client.fetch_issues_by_states("proj", ["Gate Approved"])

    assert len(issues) == 1
    assert issues[0].identifier == "MAN-35"
    assert issues[0].labels == ["debug", "bug"]
