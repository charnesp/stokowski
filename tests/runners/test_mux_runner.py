"""Tests for MuxRunner."""
import pytest


def test_mux_runner_has_correct_name():
    """Test that MuxRunner reports correct name and resume support."""
    from stokowski.runners.mux_runner import MuxRunner
    
    mock_config = {"model": "gpt-4"}
    runner = MuxRunner(mock_config, endpoint="http://test:9988")
    
    assert runner.get_name() == "mux"
    assert runner.supports_resume() is True
    assert runner.endpoint == "http://test:9988"


def test_mux_runner_builds_payload():
    """Test that MuxRunner builds HTTP payload correctly."""
    from stokowski.runners.mux_runner import MuxRunner
    
    mock_config = {"model": "gpt-4"}
    runner = MuxRunner(mock_config, endpoint="http://test:9988")
    
    payload = runner._build_payload("test prompt", session_id="ws-123")
    
    assert payload["prompt"] == "test prompt"
    assert payload["parent_workspace_id"] == "ws-123"


def test_mux_runner_run_turn_is_async():
    """Test that MuxRunner.run_turn is an async method."""
    from stokowski.runners.mux_runner import MuxRunner
    import inspect
    
    mock_config = {"model": "gpt-4"}
    runner = MuxRunner(mock_config, endpoint="http://test:9988")
    
    assert inspect.iscoroutinefunction(runner.run_turn)