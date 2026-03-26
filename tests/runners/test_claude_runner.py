"""Tests for ClaudeRunner."""
import pytest


def test_claude_runner_has_correct_name():
    """Test that ClaudeRunner reports correct name and resume support."""
    from stokowski.runners.claude_runner import ClaudeRunner
    
    mock_config = {"command": "claude"}
    runner = ClaudeRunner(mock_config)
    
    assert runner.get_name() == "claude"
    assert runner.supports_resume() is True


def test_claude_runner_builds_command():
    """Test that ClaudeRunner builds CLI command correctly."""
    from stokowski.runners.claude_runner import ClaudeRunner
    
    mock_config = {"command": "claude"}
    runner = ClaudeRunner(mock_config)
    
    cmd = runner._build_command("test prompt", session_id=None)
    
    assert "claude" in cmd
    assert "-p" in cmd
    assert "test prompt" in cmd


def test_claude_runner_adds_resume_flag():
    """Test that ClaudeRunner adds --resume flag for multi-turn sessions."""
    from stokowski.runners.claude_runner import ClaudeRunner
    
    mock_config = {"command": "claude"}
    runner = ClaudeRunner(mock_config)
    
    cmd = runner._build_command("test", session_id="abc-123")
    
    assert "--resume" in cmd
    assert "abc-123" in cmd