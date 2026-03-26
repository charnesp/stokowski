"""Tests for BaseRunner and related classes."""
import pytest


def test_run_result_creation():
    """Test that RunResult dataclass can be created and accessed."""
    from stokowski.runners.base import RunResult
    
    result = RunResult(
        result="test output",
        session_id="123",
        input_tokens=100,
        output_tokens=50,
        total_tokens=150
    )
    
    assert result.result == "test output"
    assert result.session_id == "123"
    assert result.input_tokens == 100
    assert result.output_tokens == 50
    assert result.total_tokens == 150


def test_base_runner_is_abstract():
    """Test that BaseRunner cannot be instantiated directly."""
    from stokowski.runners.base import BaseRunner
    
    with pytest.raises(TypeError):
        BaseRunner(config=None)  # Cannot instantiate abstract class


def test_runner_error_hierarchy():
    """Test that RunnerError subclasses are properly defined."""
    from stokowski.runners.base import RunnerError, RunnerTimeout, RunnerConnectionError
    
    assert issubclass(RunnerTimeout, RunnerError)
    assert issubclass(RunnerConnectionError, RunnerError)