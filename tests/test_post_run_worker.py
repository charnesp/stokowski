"""Post-run follow-up turn on the orchestrator worker path."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from stokowski.config import parse_workflow_file
from stokowski.models import Issue, RunAttempt
from stokowski.orchestrator import Orchestrator

POST_RUN_WORKFLOW = """
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
        linear_state: terminal
"""


@pytest.mark.asyncio
async def test_run_worker_invokes_runner_twice_when_post_run_enabled(tmp_path: Path):
    """After a successful work turn, a second run_turn receives the post-run prompt."""
    wf_file = tmp_path / "workflow.yaml"
    wf_file.write_text(POST_RUN_WORKFLOW)
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "g.md").write_text("global")
    (prompts / "w.md").write_text("stage")
    (prompts / "lifecycle.md").write_text("pre {{ lifecycle_phase }}")
    (prompts / "lifecycle-post-run.md").write_text("post {{ lifecycle_phase }}")

    orch = Orchestrator(wf_file)
    orch.workflow = parse_workflow_file(wf_file)
    orch._issue_state_runs["i1"] = 2
    orch._issue_workflow_cache["i1"] = orch.cfg.workflows["default"]

    issue = Issue(
        id="i1",
        identifier="T-1",
        title="t",
        state="In Progress",
        labels=[],
    )
    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        attempt=1,
        state_name="work",
        workflow_name="default",
    )

    ws = MagicMock()
    ws.path = tmp_path

    prompts_seen: list[str] = []
    hook_flags: list[tuple[bool, bool]] = []

    async def fake_run_turn(
        *,
        prompt: str,
        attempt: RunAttempt,
        run_before_hook: bool = True,
        run_after_hook: bool = True,
        **_kwargs: object,
    ):
        prompts_seen.append(prompt)
        hook_flags.append((run_before_hook, run_after_hook))
        attempt.status = "succeeded"
        attempt.full_output = "ok"
        return attempt

    mock_client = MagicMock()
    mock_client.post_comment = AsyncMock(return_value=True)
    mock_client.update_issue_state = AsyncMock(return_value=False)

    with (
        patch("stokowski.orchestrator.ensure_workspace", new_callable=AsyncMock, return_value=ws),
        patch.object(orch, "_ensure_tracker_client", return_value=mock_client),
        patch.object(orch, "_render_prompt_async", AsyncMock(return_value="WORK_PROMPT")),
        patch.object(orch, "_render_post_run_prompt_async", AsyncMock(return_value="POST_PROMPT")),
        patch("stokowski.orchestrator.run_turn", side_effect=fake_run_turn),
    ):
        await orch._run_worker(issue, attempt)

    assert prompts_seen == ["WORK_PROMPT", "POST_PROMPT"]
    assert hook_flags == [(True, False), (False, True)]


@pytest.mark.asyncio
async def test_run_worker_single_turn_when_post_run_false(tmp_path: Path):
    yaml = POST_RUN_WORKFLOW.replace(
        "      work:\n        type: agent\n        prompt: prompts/w.md",
        "      work:\n        type: agent\n        post_run: false\n        prompt: prompts/w.md",
    )
    wf_file = tmp_path / "workflow.yaml"
    wf_file.write_text(yaml)
    prompts = tmp_path / "prompts"
    prompts.mkdir()
    (prompts / "g.md").write_text("global")
    (prompts / "w.md").write_text("stage")
    (prompts / "lifecycle.md").write_text("pre")
    (prompts / "lifecycle-post-run.md").write_text("post")

    orch = Orchestrator(wf_file)
    orch.workflow = parse_workflow_file(wf_file)
    orch._issue_state_runs["i1"] = 2
    orch._issue_workflow_cache["i1"] = orch.cfg.workflows["default"]

    issue = Issue(
        id="i1",
        identifier="T-1",
        title="t",
        state="In Progress",
        labels=[],
    )
    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        attempt=1,
        state_name="work",
        workflow_name="default",
    )

    ws = MagicMock()
    ws.path = tmp_path
    prompts_seen: list[str] = []
    hook_flags: list[tuple[bool, bool]] = []

    async def fake_run_turn(
        *,
        prompt: str,
        attempt: RunAttempt,
        run_before_hook: bool = True,
        run_after_hook: bool = True,
        **_kwargs: object,
    ):
        prompts_seen.append(prompt)
        hook_flags.append((run_before_hook, run_after_hook))
        attempt.status = "succeeded"
        attempt.full_output = "single"
        return attempt

    mock_client = MagicMock()
    mock_client.post_comment = AsyncMock(return_value=True)
    mock_client.update_issue_state = AsyncMock(return_value=False)

    with (
        patch("stokowski.orchestrator.ensure_workspace", new_callable=AsyncMock, return_value=ws),
        patch.object(orch, "_ensure_tracker_client", return_value=mock_client),
        patch.object(orch, "_render_prompt_async", AsyncMock(return_value="WORK_ONLY")),
        patch.object(orch, "_render_post_run_prompt_async", AsyncMock()) as post_mock,
        patch("stokowski.orchestrator.run_turn", side_effect=fake_run_turn),
    ):
        await orch._run_worker(issue, attempt)

    assert prompts_seen == ["WORK_ONLY"]
    assert hook_flags == [(True, True)]
    post_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_worker_fails_fast_unknown_state_no_workspace(tmp_path: Path):
    """Unknown ``state_name`` fails before workspace and never calls ``run_turn``."""
    wf_file = tmp_path / "workflow.yaml"
    wf_file.write_text(POST_RUN_WORKFLOW)
    orch = Orchestrator(wf_file)
    orch.workflow = parse_workflow_file(wf_file)
    orch._issue_state_runs["i1"] = 1
    orch._issue_workflow_cache["i1"] = orch.cfg.workflows["default"]

    issue = Issue(
        id="i1",
        identifier="T-1",
        title="t",
        state="In Progress",
        labels=[],
    )
    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        attempt=1,
        state_name="ghost_state",
        workflow_name="default",
    )

    on_exit = Mock()
    with (
        patch("stokowski.orchestrator.ensure_workspace", new_callable=AsyncMock) as ws_mock,
        patch.object(orch, "_on_worker_exit", on_exit),
        patch("stokowski.orchestrator.run_turn", new_callable=AsyncMock) as run_mock,
    ):
        await orch._run_worker(issue, attempt)

    ws_mock.assert_not_awaited()
    run_mock.assert_not_awaited()
    assert attempt.status == "failed"
    assert "ghost_state" in (attempt.error or "")
    on_exit.assert_called_once_with(issue, attempt)


@pytest.mark.asyncio
async def test_run_worker_no_post_run_or_after_hook_when_work_fails_with_post_run_planned(
    tmp_path: Path,
):
    """If work turn fails while post_run is enabled, no second turn (no post-run, no after_run on work)."""
    wf_file = tmp_path / "workflow.yaml"
    wf_file.write_text(POST_RUN_WORKFLOW)
    orch = Orchestrator(wf_file)
    orch.workflow = parse_workflow_file(wf_file)
    orch._issue_state_runs["i1"] = 2
    orch._issue_workflow_cache["i1"] = orch.cfg.workflows["default"]

    issue = Issue(
        id="i1",
        identifier="T-1",
        title="t",
        state="In Progress",
        labels=[],
    )
    attempt = RunAttempt(
        issue_id=issue.id,
        issue_identifier=issue.identifier,
        attempt=1,
        state_name="work",
        workflow_name="default",
    )

    ws = MagicMock()
    ws.path = tmp_path
    hook_flags: list[tuple[bool, bool]] = []

    async def fake_run_turn(
        *,
        attempt: RunAttempt,
        run_before_hook: bool = True,
        run_after_hook: bool = True,
        **_kwargs: object,
    ):
        hook_flags.append((run_before_hook, run_after_hook))
        attempt.status = "failed"
        attempt.error = "simulated work failure"
        return attempt

    mock_client = MagicMock()
    mock_client.post_comment = AsyncMock(return_value=True)
    mock_client.update_issue_state = AsyncMock(return_value=False)

    with (
        patch("stokowski.orchestrator.ensure_workspace", new_callable=AsyncMock, return_value=ws),
        patch.object(orch, "_ensure_tracker_client", return_value=mock_client),
        patch.object(orch, "_render_prompt_async", AsyncMock(return_value="WORK_PROMPT")),
        patch.object(orch, "_render_post_run_prompt_async", AsyncMock()) as post_mock,
        patch("stokowski.orchestrator.run_turn", side_effect=fake_run_turn),
    ):
        await orch._run_worker(issue, attempt)

    assert hook_flags == [(True, False)]
    post_mock.assert_not_awaited()
