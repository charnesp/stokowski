"""Tests for RunnerFactory."""
import pytest


def test_factory_creates_claude_runner():
    """Test that factory creates ClaudeRunner for 'claude' type."""
    from stokowski.runners.factory import RunnerFactory
    from stokowski.runners.claude_runner import ClaudeRunner
    
    mock_config = {"command": "claude"}
    runner = RunnerFactory.create("claude", mock_config)
    
    assert isinstance(runner, ClaudeRunner)


def test_factory_creates_mux_runner():
    """Test that factory creates MuxRunner for 'mux' type."""
    from stokowski.runners.factory import RunnerFactory
    from stokowski.runners.mux_runner import MuxRunner
    
    mock_config = {"model": "gpt-4"}
    runner = RunnerFactory.create("mux", mock_config, mux_endpoint="http://test:9988")
    
    assert isinstance(runner, MuxRunner)
    assert runner.endpoint == "http://test:9988"


def test_factory_rejects_unknown_runner():
    """Test that factory raises error for unknown runner type."""
    from stokowski.runners.factory import RunnerFactory
    
    mock_config = {}
    with pytest.raises(ValueError, match="Unknown runner type: unknown"):
        RunnerFactory.create("unknown", mock_config)