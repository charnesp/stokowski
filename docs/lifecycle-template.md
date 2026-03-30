# Custom Lifecycle Template

Stokowski supports custom lifecycle injection templates via the `prompts.lifecycle_prompt` configuration option. When set, this file is rendered as a Jinja2 template and used instead of the default hardcoded lifecycle section.

## Configuration

```yaml
prompts:
  global_prompt: prompts/global.md
  lifecycle_prompt: prompts/lifecycle.md  # Custom lifecycle template
```

## Available Variables

Custom lifecycle templates receive all standard template variables plus lifecycle-specific ones:

### Standard Variables (from `build_template_context`)

| Variable | Description |
|----------|-------------|
| `issue_id` | Linear issue UUID |
| `issue_identifier` | e.g. `ENG-42` |
| `issue_title` | Issue title |
| `issue_description` | Full issue description |
| `issue_url` | Linear issue URL |
| `issue_priority` | Priority number (0-4) |
| `issue_state` | Current Linear state name |
| `issue_branch` | Suggested git branch name |
| `issue_labels` | List of label names |
| `state_name` | Current state machine state |
| `run` | Run number for this state |
| `attempt` | Retry attempt within this run |
| `last_run_at` | ISO timestamp of last run |

### Lifecycle-Specific Variables

| Variable | Description |
|----------|-------------|
| `previous_error` | Error message from previous failed attempt (empty string if none) |
| `is_rework` | Boolean indicating if this is a rework run after gate rejection |
| `recent_comments` | List of comment dicts with `body` and `createdAt` keys |
| `transitions` | Dict mapping trigger names to target state names |
| `has_gate_transition` | Boolean if any transition leads to a gate state |
| `gate_targets` | List of `(trigger, target)` tuples for gate transitions |
| `issue` | The full Issue dataclass instance |

## Example Template

```markdown
---
<!-- Custom lifecycle injection -->

## Required Report Format

When you complete your work, include a structured report:

```xml
<stokowski:report>
## Summary
- What was accomplished
- Key decisions made

## Files Changed
- `path/to/file.py` - brief description
</stokowski:report>
```

{% if previous_error %}
## Previous Error

> {{ previous_error }}

Please fix this issue in your response.
{% endif %}

{% if is_rework %}
## Rework Feedback

{% for comment in recent_comments %}
- {{ comment.body }}
{% endfor %}
{% endif %}

{% if transitions %}
## Available Transitions

{% for trigger, target in transitions.items() %}
- `{{ trigger }}` → {{ target }}
{% endfor %}
{% endif %}
```

## Important Notes

- The `stokowski:report` XML tag is **required** — tracking.py depends on it
- Missing variables render as empty strings (no errors)
- Template syntax errors fall back to the default hardcoded section
- If the rendered template doesn't contain `<stokowski:report>`, a warning is logged
