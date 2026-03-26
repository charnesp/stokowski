"""Tests for RunnerFactory."""
import pytest


def test_factory_creates_claude_runner():
    """Test that factory creates ClaudeRunner for 'claude' type."""
    from stokowski.runners.factory import RunnerFactory
    from stokowski.runners.claude_runner import ClaudeRunner
    
    mock_config = {"command": "claude"}
    runner = RunnerFactory.create("claude", mock_config)
    
    assert isinstance(runner, ClaudeRunner)