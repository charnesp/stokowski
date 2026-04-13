"""parse_latest_tracking and get_last_tracking_timestamp use max(effective time), not list order."""

from __future__ import annotations

from stokowski.tracking import get_last_tracking_timestamp, parse_latest_tracking


def test_parse_latest_tracking_picks_newest_state_by_json_timestamp_not_list_order():
    older = (
        '<!-- stokowski:state {"state": "investigate", "run": 1, '
        '"timestamp": "2026-04-01T10:00:00+00:00", "workflow": "feature"} -->'
    )
    newer = (
        '<!-- stokowski:state {"state": "implement", "run": 1, '
        '"timestamp": "2026-04-13T08:00:00+00:00", "workflow": "feature"} -->'
    )
    comments = [
        {"body": newer, "createdAt": "2026-04-13T08:00:01.000Z"},
        {"body": older, "createdAt": "2026-04-01T10:00:01.000Z"},
    ]
    got = parse_latest_tracking(comments)
    assert got is not None
    assert got["type"] == "state"
    assert got["state"] == "implement"


def test_parse_latest_tracking_state_vs_gate_wins_by_newer_timestamp():
    gate_body = (
        '<!-- stokowski:gate {"state": "merge-review", "status": "waiting", "run": 2, '
        '"timestamp": "2026-04-12T21:20:50+00:00", "workflow": "feature"} -->'
    )
    state_body = (
        '<!-- stokowski:state {"state": "investigate", "run": 2, '
        '"timestamp": "2026-04-13T10:00:00+00:00", "workflow": "feature"} -->'
    )
    # Newest-first: state comment listed before older gate
    comments = [
        {"body": state_body, "createdAt": "2026-04-13T10:00:01.000Z"},
        {"body": gate_body, "createdAt": "2026-04-12T21:20:51.000Z"},
    ]
    got = parse_latest_tracking(comments)
    assert got is not None
    assert got["type"] == "state"
    assert got["state"] == "investigate"


def test_parse_latest_tracking_fallback_last_candidate_when_no_parseable_time():
    """No JSON timestamp and no createdAt: preserve legacy last-in-order among markers."""
    b1 = '<!-- stokowski:state {"state": "a", "run": 1} -->'
    b2 = '<!-- stokowski:state {"state": "b", "run": 1} -->'
    comments = [{"body": b1}, {"body": b2}]
    got = parse_latest_tracking(comments)
    assert got is not None
    assert got["state"] == "b"


def test_get_last_tracking_timestamp_matches_parse_latest_effective_time():
    gate_body = (
        '<!-- stokowski:gate {"state": "g", "status": "waiting", "run": 1, '
        '"timestamp": "2026-01-02T00:00:00+00:00"} -->'
    )
    state_body = (
        '<!-- stokowski:state {"state": "s", "run": 1, '
        '"timestamp": "2026-01-03T00:00:00+00:00"} -->'
    )
    comments = [
        {"body": gate_body, "createdAt": "2026-01-02T12:00:00Z"},
        {"body": state_body, "createdAt": "2026-01-03T12:00:00Z"},
    ]
    assert parse_latest_tracking(comments)["state"] == "s"
    assert get_last_tracking_timestamp(comments) == "2026-01-03T00:00:00+00:00"
