"""State machine tracking via structured Linear comments."""

from __future__ import annotations

import contextlib
import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("stokowski.tracking")

STATE_PATTERN = re.compile(r"<!-- stokowski:state ({.*?}) -->")
GATE_PATTERN = re.compile(r"<!-- stokowski:gate ({.*?}) -->")


def make_state_comment(state: str, run: int = 1, workflow: str | None = None) -> str:
    """Build a structured state-tracking comment."""
    payload: dict[str, Any] = {
        "state": state,
        "run": run,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if workflow:
        payload["workflow"] = workflow
    machine = f"<!-- stokowski:state {json.dumps(payload)} -->"
    wf_info = f" [{workflow}]" if workflow else ""
    human = f"**[Stokowski]** Entering state: **{state}**{wf_info} (run {run})"
    return f"{machine}\n\n{human}"


def make_gate_comment(
    state: str,
    status: str,
    prompt: str = "",
    rework_to: str | None = None,
    run: int = 1,
    workflow: str | None = None,
) -> str:
    """Build a structured gate-tracking comment."""
    payload: dict[str, Any] = {
        "state": state,
        "status": status,
        "run": run,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    if rework_to:
        payload["rework_to"] = rework_to
    if workflow:
        payload["workflow"] = workflow

    machine = f"<!-- stokowski:gate {json.dumps(payload)} -->"

    if status == "waiting":
        human = f"**[Stokowski]** Awaiting human review: **{state}**"
        if prompt:
            human += f" — {prompt}"
    elif status == "approved":
        human = f"**[Stokowski]** Gate **{state}** approved."
    elif status == "rework":
        human = f"**[Stokowski]** Rework requested at **{state}**. Returning to: **{rework_to}**"
        if run > 1:
            human += f" (run {run})"
    elif status == "escalated":
        human = (
            f"**[Stokowski]** Max rework exceeded at **{state}**. "
            f"Escalating for human intervention."
        )
    else:
        human = f"**[Stokowski]** Gate **{state}** status: {status}"

    return f"{machine}\n\n{human}"


def parse_latest_tracking(comments: list[dict]) -> dict[str, Any] | None:
    """Return the most recent state or gate tracking entry.

    Picks the candidate with the latest effective time: ``timestamp`` in the
    JSON payload (preferred), else the comment's ``createdAt``. Order of
    comments in the API response does not matter.

    If no candidate has a parseable time, falls back to the last marker in
    scan order (state, then gate, per comment — same as legacy).

    Returns a dict with ``type`` ``"state"`` or ``"gate"`` plus JSON fields,
    or None if no tracking markers found.
    """
    entries = _collect_tracking_entries(comments)
    if not entries:
        return None

    best: tuple[datetime, dict[str, Any]] | None = None
    for eff, row, _comment in entries:
        if eff is None:
            continue
        if best is None or eff > best[0]:
            best = (eff, row)

    if best is not None:
        return best[1]

    return entries[-1][1]


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    with contextlib.suppress(ValueError, AttributeError):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def _tracking_payload_effective_time(comment: dict[str, Any], payload: dict[str, Any]) -> datetime | None:
    """JSON ``timestamp`` preferred, else Linear ``createdAt`` on the comment."""
    return _parse_iso_datetime(payload.get("timestamp")) or _parse_iso_datetime(
        comment.get("createdAt")
    )


def _collect_tracking_entries(
    comments: list[dict],
) -> list[tuple[datetime | None, dict[str, Any], dict[str, Any]]]:
    """Each ``stokowski:state`` / ``stokowski:gate`` marker → (effective_time, row, comment)."""
    entries: list[tuple[datetime | None, dict[str, Any], dict[str, Any]]] = []

    for comment in comments:
        body = comment.get("body", "")

        state_match = STATE_PATTERN.search(body)
        if state_match:
            with contextlib.suppress(json.JSONDecodeError):
                raw = json.loads(state_match.group(1))
                row = dict(raw)
                row["type"] = "state"
                eff = _tracking_payload_effective_time(comment, raw)
                entries.append((eff, row, comment))

        gate_match = GATE_PATTERN.search(body)
        if gate_match:
            with contextlib.suppress(json.JSONDecodeError):
                raw = json.loads(gate_match.group(1))
                row = dict(raw)
                row["type"] = "gate"
                eff = _tracking_payload_effective_time(comment, raw)
                entries.append((eff, row, comment))

    return entries


def parse_latest_gate_waiting(comments: list[dict]) -> dict[str, Any] | None:
    """Return the most recent gate tracking payload with status "waiting".

    Chooses the candidate with the latest effective time: ``timestamp`` in the
    gate JSON (preferred), else the comment's ``createdAt``. This is correct
    regardless of whether the API returns comments oldest-first or newest-first.

    If no candidate has a parseable time, falls back to the last waiting gate
    in list order (legacy behavior).
    """
    best_time: datetime | None = None
    best_payload: dict[str, Any] | None = None
    fallback: dict[str, Any] | None = None

    for comment in comments:
        body = comment.get("body", "")
        gate_match = GATE_PATTERN.search(body)
        if not gate_match:
            continue
        try:
            data = json.loads(gate_match.group(1))
        except json.JSONDecodeError:
            continue
        if data.get("status") != "waiting":
            continue
        row = dict(data)
        row["type"] = "gate"
        fallback = row

        effective = _tracking_payload_effective_time(comment, data)
        if effective is None:
            continue
        if best_time is None or effective > best_time:
            best_time = effective
            best_payload = row

    if best_payload is not None:
        return best_payload
    return fallback


def get_last_tracking_timestamp(comments: list[dict]) -> str | None:
    """ISO timestamp string for the same tracking entry as :func:`parse_latest_tracking`.

    Prefers the payload's ``timestamp`` field; if missing, returns the
    comment's ``createdAt`` string for that entry.
    """
    entries = _collect_tracking_entries(comments)
    if not entries:
        return None

    best: tuple[datetime, dict[str, Any], dict[str, Any]] | None = None
    for eff, row, comment in entries:
        if eff is None:
            continue
        if best is None or eff > best[0]:
            best = (eff, row, comment)

    if best is not None:
        _, row, comment = best
    else:
        row, comment = entries[-1][1], entries[-1][2]

    ts = row.get("timestamp")
    if isinstance(ts, str) and ts.strip():
        return ts
    created = comment.get("createdAt")
    if isinstance(created, str) and created.strip():
        return created
    return None


def get_comments_since(comments: list[dict], since_timestamp: str | None) -> list[dict]:
    """Filter comments to only those after a given timestamp.

    Returns comments that are NOT stokowski tracking comments and
    were created after the given timestamp.
    """
    result = []
    since_dt = None
    if since_timestamp:
        with contextlib.suppress(ValueError, AttributeError):
            since_dt = datetime.fromisoformat(since_timestamp.replace("Z", "+00:00"))

    for comment in comments:
        body = comment.get("body", "")
        if "<!-- stokowski:" in body:
            continue

        if since_dt:
            created = comment.get("createdAt", "")
            if created:
                try:
                    created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                    if created_dt <= since_dt:
                        continue
                except (ValueError, AttributeError):
                    pass

        result.append(comment)

    return result
