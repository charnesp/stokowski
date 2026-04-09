"""Orchestrator behaviour for agent-gate states."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from stokowski.config import parse_workflow_file
from stokowski.models import Issue, RunAttempt
from stokowski.orchestrator import Orchestrator

AG_GATE_YAML = """
tracker:
  project_slug: test-project

workflows:
  default:
    default: true
    prompts:
      global_prompt: prompts/g.md
    states:
      start:
        type: agent
        prompt: prompts/start.md
        transitions:
          complete: route
      route:
        type: agent-gate
        prompt: prompts/route.md
        default_transition: to_human
        transitions:
          pick_fix: fix
          to_human: human
      fix:
        type: agent
        prompt: prompts/fix.md
        transitions:
          complete: route
      human:
        type: gate
        linear_state: review
        rework_to: start
        transitions:
          approve: done
      done:
        type: terminal
"""

AG_ONLY_YAML = """
tracker:
  project_slug: test-project

workflows:
  default:
    default: true
    prompts:
      global_prompt: prompts/g.md
    states:
      work:
        type: agent
        prompt: prompts/w.md
        transitions:
          complete: done
      done:
        type: terminal
"""

ROUTE_OK = """<<<STOKOWSKI_ROUTE>>>
{"transition": "pick_fix"}
<<<END_STOKOWSKI_ROUTE>>>
<stokowski:report>
## Summary
ok
</stokowski:report>
"""


def _orch(tmp_path, content: str) -> Orchestrator:
    wf_file = tmp_path / "workflow.yaml"
    wf_file.write_text(content)
    o = Orchestrator(wf_file)
    o.workflow = parse_workflow_file(wf_file)
    return o


def _issue() -> Issue:
    return Issue(
        id="i1",
        identifier="T-1",
        title="t",
        state="In Progress",
        labels=[],
    )


@pytest.mark.asyncio
async def test_agent_gate_success_transitions_chosen_key_and_posts_report(tmp_path):
    orch = _orch(tmp_path, AG_GATE_YAML)
    issue = _issue()
    orch._issue_workflow_cache[issue.id] = orch.cfg.get_workflow_for_issue(issue)
    orch._issue_current_state[issue.id] = "route"

    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        status="succeeded",
        state_name="route",
        full_output=ROUTE_OK,
    )

    mock_client = MagicMock()
    mock_client.post_comment = AsyncMock(return_value=True)
    mock_safe = AsyncMock()

    bg_tasks: list[asyncio.Task[None]] = []
    real_create_task = asyncio.create_task

    def capture_create_task(coro):  # type: ignore[no-untyped-def]
        t = real_create_task(coro)
        bg_tasks.append(t)
        return t

    with (
        patch.object(orch, "_ensure_linear_client", return_value=mock_client),
        patch.object(orch, "_safe_transition", mock_safe),
        patch("stokowski.orchestrator.asyncio.create_task", side_effect=capture_create_task),
    ):
        orch._on_worker_exit(issue, attempt)
        await asyncio.gather(*bg_tasks)

    mock_safe.assert_awaited_once_with(issue, "pick_fix")
    assert mock_client.post_comment.await_count == 1
    bodies = [
        str(c.kwargs.get("body") or c.args[1]) for c in mock_client.post_comment.await_args_list
    ]
    assert any("stokowski:report" in b for b in bodies)
    assert not any("route-error" in b for b in bodies)


@pytest.mark.asyncio
async def test_agent_gate_routing_error_posts_fallback_and_error_comment(tmp_path):
    orch = _orch(tmp_path, AG_GATE_YAML)
    issue = _issue()
    orch._issue_workflow_cache[issue.id] = orch.cfg.get_workflow_for_issue(issue)
    orch._issue_current_state[issue.id] = "route"

    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        status="succeeded",
        state_name="route",
        full_output="no routing markers at all",
    )

    mock_client = MagicMock()
    mock_client.post_comment = AsyncMock(return_value=True)
    mock_safe = AsyncMock()

    bg_tasks: list[asyncio.Task[None]] = []
    real_create_task = asyncio.create_task

    def capture_create_task(coro):  # type: ignore[no-untyped-def]
        t = real_create_task(coro)
        bg_tasks.append(t)
        return t

    with (
        patch.object(orch, "_ensure_linear_client", return_value=mock_client),
        patch.object(orch, "_safe_transition", mock_safe),
        patch("stokowski.orchestrator.asyncio.create_task", side_effect=capture_create_task),
    ):
        orch._on_worker_exit(issue, attempt)
        await asyncio.gather(*bg_tasks)

    mock_safe.assert_awaited_once_with(issue, "to_human")
    assert mock_client.post_comment.await_count == 1
    bodies = [
        str(c.kwargs.get("body") or c.args[1]) for c in mock_client.post_comment.await_args_list
    ]
    assert any("route-error" in b for b in bodies)
    assert not any("stokowski:report" in b for b in bodies)


@pytest.mark.asyncio
async def test_agent_state_still_complete_and_generic_report(tmp_path):
    orch = _orch(tmp_path, AG_ONLY_YAML)
    issue = _issue()
    orch._issue_workflow_cache[issue.id] = orch.cfg.get_workflow_for_issue(issue)
    orch._issue_current_state[issue.id] = "work"

    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        status="succeeded",
        state_name="work",
        full_output="<stokowski:report>x</stokowski:report>",
    )

    mock_client = MagicMock()
    mock_client.post_comment = AsyncMock(return_value=True)
    mock_client.fetch_comments = AsyncMock(return_value=[])
    mock_safe = AsyncMock()

    bg_tasks: list[asyncio.Task[None]] = []
    real_create_task = asyncio.create_task

    def capture_create_task(coro):  # type: ignore[no-untyped-def]
        t = real_create_task(coro)
        bg_tasks.append(t)
        return t

    with (
        patch.object(orch, "_ensure_linear_client", return_value=mock_client),
        patch.object(orch, "_safe_transition", mock_safe),
        patch("stokowski.orchestrator.asyncio.create_task", side_effect=capture_create_task),
    ):
        orch._on_worker_exit(issue, attempt)
        await asyncio.gather(*bg_tasks)

    mock_safe.assert_awaited_once_with(issue, "complete")
    assert mock_client.post_comment.await_count == 1


LEGACY_ROOT_AGENT_GATE_YAML = """
tracker:
  project_slug: test-project

prompts:
  global_prompt: prompts/g.md

states:
  start:
    type: agent
    prompt: prompts/start.md
    transitions:
      complete: route
  route:
    type: agent-gate
    prompt: prompts/route.md
    default_transition: to_human
    transitions:
      pick_fix: fix
      to_human: human
  fix:
    type: agent
    prompt: prompts/fix.md
    transitions:
      complete: route
  human:
    type: gate
    linear_state: review
    rework_to: start
    transitions:
      approve: done
  done:
    type: terminal
"""


@pytest.mark.asyncio
async def test_agent_gate_legacy_root_states_same_as_workflows(tmp_path):
    orch = _orch(tmp_path, LEGACY_ROOT_AGENT_GATE_YAML)
    issue = _issue()
    orch._issue_current_state[issue.id] = "route"

    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        status="succeeded",
        state_name="route",
        workflow_name="default",
        full_output=ROUTE_OK,
    )

    mock_client = MagicMock()
    mock_client.post_comment = AsyncMock(return_value=True)
    mock_safe = AsyncMock()

    bg_tasks: list[asyncio.Task[None]] = []
    real_create_task = asyncio.create_task

    def capture_create_task(coro):  # type: ignore[no-untyped-def]
        t = real_create_task(coro)
        bg_tasks.append(t)
        return t

    with (
        patch.object(orch, "_ensure_linear_client", return_value=mock_client),
        patch.object(orch, "_safe_transition", mock_safe),
        patch("stokowski.orchestrator.asyncio.create_task", side_effect=capture_create_task),
    ):
        orch._on_worker_exit(issue, attempt)
        await asyncio.gather(*bg_tasks)

    mock_safe.assert_awaited_once_with(issue, "pick_fix")
    assert mock_client.post_comment.await_count == 1


@pytest.mark.asyncio
async def test_agent_gate_resolves_workflow_from_attempt_when_cache_empty(tmp_path):
    orch = _orch(tmp_path, AG_GATE_YAML)
    issue = _issue()
    orch._issue_current_state[issue.id] = "route"
    assert issue.id not in orch._issue_workflow_cache

    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        status="succeeded",
        state_name="route",
        workflow_name="default",
        full_output=ROUTE_OK,
    )

    mock_client = MagicMock()
    mock_client.post_comment = AsyncMock(return_value=True)
    mock_safe = AsyncMock()

    bg_tasks: list[asyncio.Task[None]] = []
    real_create_task = asyncio.create_task

    def capture_create_task(coro):  # type: ignore[no-untyped-def]
        t = real_create_task(coro)
        bg_tasks.append(t)
        return t

    with (
        patch.object(orch, "_ensure_linear_client", return_value=mock_client),
        patch.object(orch, "_safe_transition", mock_safe),
        patch("stokowski.orchestrator.asyncio.create_task", side_effect=capture_create_task),
    ):
        orch._on_worker_exit(issue, attempt)
        await asyncio.gather(*bg_tasks)

    mock_safe.assert_awaited_once_with(issue, "pick_fix")
    assert mock_client.post_comment.await_count == 1
