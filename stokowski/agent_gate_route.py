"""Parse agent-gate routing markers from runner output."""

from __future__ import annotations

import base64
import json
from typing import TYPE_CHECKING

__all__ = ["ROUTE_END", "ROUTE_START", "decide_agent_gate_transition", "format_route_error_comment"]

if TYPE_CHECKING:
    from .config import StateConfig

ROUTE_START = "<<<STOKOWSKI_ROUTE>>>"
ROUTE_END = "<<<END_STOKOWSKI_ROUTE>>>"

_MAX_ROUTE_ERR_DETAIL = 500
_MAX_TRANSITION_PREVIEW = 120


def decide_agent_gate_transition(
    full_output: str, state_cfg: StateConfig
) -> tuple[str, str | None]:
    """Choose the transition key from runner output and optional human-facing error text.

    On any parse failure or unknown transition name, returns ``(default_transition, error_message)``.
    On success returns ``(chosen_key, None)``.
    """
    default_key = (state_cfg.default_transition or "").strip() or None
    if not default_key:
        keys = list(state_cfg.transitions.keys())
        if keys:
            default_key = keys[0]
        else:
            return "complete", (
                "agent-gate state has no default_transition and no transitions (config error)"
            )

    if ROUTE_START not in full_output:
        return (
            default_key,
            f"Routing block missing (expected {ROUTE_START} ... {ROUTE_END})",
        )

    start_idx = full_output.index(ROUTE_START) + len(ROUTE_START)
    try:
        end_idx = full_output.index(ROUTE_END, start_idx)
    except ValueError:
        return (
            default_key,
            f"Routing block missing end marker ({ROUTE_END}) after {ROUTE_START}",
        )

    inner = full_output[start_idx:end_idx].strip()

    try:
        data = json.loads(inner)
    except json.JSONDecodeError as e:
        return default_key, f"Invalid JSON in routing block: {e}"

    if not isinstance(data, dict):
        return default_key, "Routing JSON must be a JSON object with a 'transition' field"

    tr = data.get("transition")
    if not isinstance(tr, str) or not tr.strip():
        return default_key, "Routing JSON 'transition' must be a non-empty string"

    tr = tr.strip()
    if tr not in state_cfg.transitions:
        preview = tr[:_MAX_TRANSITION_PREVIEW] + ("…" if len(tr) > _MAX_TRANSITION_PREVIEW else "")
        return default_key, f"Unknown transition key {preview!r} in routing output"

    return tr, None


def format_route_error_comment(detail: str) -> str:
    """Build a Linear comment when automatic agent-gate routing failed."""
    safe = detail.strip()
    if len(safe) > _MAX_ROUTE_ERR_DETAIL:
        safe = safe[:_MAX_ROUTE_ERR_DETAIL] + "…"
    payload = json.dumps({"type": "route_error", "detail": safe}, separators=(",", ":"))
    b64 = base64.standard_b64encode(payload.encode("utf-8")).decode("ascii")
    return (
        f"<!-- stokowski:route-error b64:{b64} -->\n\n"
        f"**[Stokowski] Agent-gate routing fallback.**\n\n{safe}"
    )
