"""Tests for agent-gate YAML parsing and validation (OpenSpec agent-gate-routing)."""

from __future__ import annotations

import textwrap

from stokowski.config import (
    ServiceConfig,
    StateConfig,
    parse_workflow_file,
    validate_config,
)

TRACKER = """
tracker:
  project_slug: test-project
"""


def _parse(tmp_path, yaml_body: str):
    p = tmp_path / "workflow.yaml"
    p.write_text(textwrap.dedent(yaml_body).strip() + "\n")
    return parse_workflow_file(p).config


def _valid_legacy_states() -> str:
    return """
states:
  start:
    type: agent
    prompt: prompts/start.md
    transitions:
      complete: route
  route:
    type: agent-gate
    prompt: prompts/route.md
    default_transition: escalate
    transitions:
      findings: fix
      clean: done
      escalate: human
  fix:
    type: agent
    prompt: prompts/fix.md
    transitions:
      complete: route
  human:
    type: gate
    linear_state: review
    rework_to: start
    transitions:
      approve: done
  done:
    type: terminal
"""


class TestAgentGateParsing:
    """YAML fragments: parsed StateConfig must expose agent-gate fields."""

    def test_parse_preserves_type_default_transition_and_transitions(self, tmp_path):
        cfg = _parse(tmp_path, TRACKER + _valid_legacy_states())
        route = cfg.states["route"]
        assert route.type == "agent-gate"
        assert route.default_transition == "escalate"
        assert route.transitions == {
            "findings": "fix",
            "clean": "done",
            "escalate": "human",
        }
        assert route.prompt == "prompts/route.md"


class TestAgentGateValidationLegacy:
    """Legacy root states: validate_config accepts a coherent agent-gate machine."""

    def test_valid_legacy_agent_gate_machine_has_no_errors(self, tmp_path):
        cfg = _parse(tmp_path, TRACKER + _valid_legacy_states())
        errors = validate_config(cfg, skip_secrets_check=True)
        assert errors == [], f"unexpected errors: {errors}"

    def test_missing_default_transition_rejected(self, tmp_path):
        yaml = (
            TRACKER
            + """
states:
  start:
    type: agent
    prompt: prompts/start.md
    transitions:
      complete: route
  route:
    type: agent-gate
    prompt: prompts/route.md
    transitions:
      a: human
  human:
    type: gate
    linear_state: review
    rework_to: start
    transitions:
      approve: done
  done:
    type: terminal
"""
        )
        cfg = _parse(tmp_path, yaml)
        errors = validate_config(cfg, skip_secrets_check=True)
        assert any("default_transition" in e.lower() for e in errors), errors

    def test_default_transition_target_must_be_gate(self, tmp_path):
        yaml = (
            TRACKER
            + """
states:
  start:
    type: agent
    prompt: prompts/start.md
    transitions:
      complete: route
  route:
    type: agent-gate
    prompt: prompts/route.md
    default_transition: to_fix
    transitions:
      to_fix: fix
      to_human: human
  fix:
    type: agent
    prompt: prompts/fix.md
    transitions:
      complete: start
  human:
    type: gate
    linear_state: review
    rework_to: start
    transitions:
      approve: done
  done:
    type: terminal
"""
        )
        cfg = _parse(tmp_path, yaml)
        errors = validate_config(cfg, skip_secrets_check=True)
        assert any("gate" in e.lower() and "default" in e.lower() for e in errors), errors

    def test_rework_to_forbidden_on_agent_gate(self, tmp_path):
        yaml = (
            TRACKER
            + """
states:
  start:
    type: agent
    prompt: prompts/start.md
    transitions:
      complete: route
  route:
    type: agent-gate
    prompt: prompts/route.md
    default_transition: human
    rework_to: start
    transitions:
      x: human
  human:
    type: gate
    linear_state: review
    rework_to: start
    transitions:
      approve: done
  done:
    type: terminal
"""
        )
        cfg = _parse(tmp_path, yaml)
        errors = validate_config(cfg, skip_secrets_check=True)
        assert any("rework" in e.lower() for e in errors), errors

    def test_unknown_transition_target_rejected(self, tmp_path):
        yaml = (
            TRACKER
            + """
states:
  start:
    type: agent
    prompt: prompts/start.md
    transitions:
      complete: route
  route:
    type: agent-gate
    prompt: prompts/route.md
    default_transition: human
    transitions:
      bad: nonexistent
      human: human
  human:
    type: gate
    linear_state: review
    rework_to: start
    transitions:
      approve: done
  done:
    type: terminal
"""
        )
        cfg = _parse(tmp_path, yaml)
        errors = validate_config(cfg, skip_secrets_check=True)
        assert any("nonexistent" in e or "unknown" in e.lower() for e in errors), errors

    def test_default_transition_must_be_a_declared_transition_key(self, tmp_path):
        yaml = (
            TRACKER
            + """
states:
  start:
    type: agent
    prompt: prompts/start.md
    transitions:
      complete: route
  route:
    type: agent-gate
    prompt: prompts/route.md
    default_transition: missing_key
    transitions:
      ok: human
  human:
    type: gate
    linear_state: review
    rework_to: start
    transitions:
      approve: done
  done:
    type: terminal
"""
        )
        cfg = _parse(tmp_path, yaml)
        errors = validate_config(cfg, skip_secrets_check=True)
        assert any("default_transition" in e.lower() for e in errors), errors


class TestAgentGateValidationMultiWorkflow:
    """Multi-workflow: each workflow validated independently."""

    def test_multi_workflow_agent_gate_valid(self, tmp_path):
        yaml = (
            TRACKER
            + """
workflows:
  wf_a:
    label: a
    default: true
    prompts:
      global_prompt: prompts/g.md
    states:
      start:
        type: agent
        prompt: prompts/s.md
        transitions:
          complete: route
      route:
        type: agent-gate
        prompt: prompts/r.md
        default_transition: to_human
        transitions:
          to_human: human
      human:
        type: gate
        linear_state: review
        rework_to: start
        transitions:
          approve: done
      done:
        type: terminal

  wf_b:
    label: b
    prompts:
      global_prompt: prompts/g2.md
    states:
      s2:
        type: agent
        prompt: prompts/s2.md
        transitions:
          complete: ag
      ag:
        type: agent-gate
        prompt: prompts/ag.md
        default_transition: to_gate
        transitions:
          to_gate: g2
      g2:
        type: gate
        linear_state: review
        rework_to: s2
        transitions:
          approve: t2
      t2:
        type: terminal
"""
        )
        cfg = _parse(tmp_path, yaml)
        errors = validate_config(cfg, skip_secrets_check=True)
        assert errors == [], f"unexpected errors: {errors}"


class TestAgentGateProgrammaticValidation:
    """Edge cases without full YAML."""

    def test_max_rework_forbidden_on_agent_gate(self):
        human = StateConfig(
            name="human",
            type="gate",
            prompt=None,
            linear_state="review",
            rework_to="start",
            transitions={"approve": "done"},
        )
        start = StateConfig(
            name="start",
            type="agent",
            prompt="p.md",
            transitions={"complete": "route"},
        )
        route = StateConfig(
            name="route",
            type="agent-gate",
            prompt="r.md",
            default_transition="human",
            transitions={"x": "human"},
            max_rework=3,
        )
        done = StateConfig(name="done", type="terminal")
        cfg = ServiceConfig(
            states={
                "start": start,
                "route": route,
                "human": human,
                "done": done,
            }
        )
        errors = validate_config(cfg, skip_secrets_check=True)
        assert any("max_rework" in e.lower() or "rework" in e.lower() for e in errors), errors

    def test_agent_gate_requires_prompt(self):
        human = StateConfig(
            name="human",
            type="gate",
            linear_state="review",
            rework_to="start",
            transitions={"approve": "done"},
        )
        start = StateConfig(
            name="start",
            type="agent",
            prompt="p.md",
            transitions={"complete": "route"},
        )
        route = StateConfig(
            name="route",
            type="agent-gate",
            prompt=None,
            default_transition="human",
            transitions={"x": "human"},
        )
        done = StateConfig(name="done", type="terminal")
        cfg = ServiceConfig(
            states={
                "start": start,
                "route": route,
                "human": human,
                "done": done,
            }
        )
        errors = validate_config(cfg, skip_secrets_check=True)
        assert any("prompt" in e.lower() for e in errors), errors
