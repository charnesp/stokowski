"""Tests for configuration parsing."""
import pytest


def test_config_parses_runner_field():
    """Test that workflow.yaml runner field is parsed correctly."""
    import tempfile
    import os
    from stokowski.config import parse_workflow_file
    
    yaml_content = """states:
  test:
    type: agent
    runner: mux
"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name
    
    try:
        workflow = parse_workflow_file(temp_path)
        assert workflow.config.states["test"].runner == "mux"
    finally:
        os.unlink(temp_path)