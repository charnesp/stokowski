# Proposal: Add `common_prompts` Section to workflow.yaml

## Summary

Add support for a `common_prompts` section at the root level of `workflow.yaml` that defines default prompt configurations shared across all workflows. This eliminates the repetitive declaration of identical `lifecycle_prompt` and `lifecycle_post_run_prompt` values in every workflow definition.

## Problem Statement

In multi-workflow configurations, the `prompts` section is duplicated in every workflow:

```yaml
workflows:
  debug:
    label: debug
    prompts:
      global_prompt: prompts/debug/global.md
      lifecycle_prompt: prompts/lifecycle.md              # Duplicated
      lifecycle_post_run_prompt: prompts/lifecycle-post-run.md  # Duplicated

  feature:
    label: feature
    prompts:
      global_prompt: prompts/feature/global.md
      lifecycle_prompt: prompts/lifecycle.md              # Same as debug
      lifecycle_post_run_prompt: prompts/lifecycle-post-run.md  # Same as debug

  docs:
    label: docs
    prompts:
      global_prompt: prompts/docs/global.md
      lifecycle_prompt: prompts/lifecycle.md              # Same again
      lifecycle_post_run_prompt: prompts/lifecycle-post-run.md  # Same again
```

This pattern:
- Creates unnecessary duplication
- Makes configuration files harder to read and maintain
- Increases risk of inconsistencies when updating shared prompts
- Adds visual noise that obscures workflow-specific differences

## Proposed Solution

Introduce a `common_prompts` section at the root level that serves as defaults for all workflows:

```yaml
# Common prompts shared across all workflows
common_prompts:
  global_prompt: prompts/global.md
  lifecycle_prompt: prompts/lifecycle.md
  lifecycle_post_run_prompt: prompts/lifecycle-post-run.md

workflows:
  debug:
    label: debug
    prompts:
      global_prompt: prompts/debug/global.md  # Override common
      # lifecycle_prompt and lifecycle_post_run_prompt inherited

  feature:
    label: feature
    prompts:
      global_prompt: prompts/feature/global.md  # Override common
      # lifecycle_prompt and lifecycle_post_run_prompt inherited
```

## Key Features

1. **Inheritance**: Workflows inherit prompts from `common_prompts` by default
2. **Override capability**: Workflow-specific `prompts` values take precedence
3. **Partial override**: Workflows can override only specific prompts while inheriting others
4. **Backwards compatibility**: Existing configurations without `common_prompts` continue to work
5. **Fallback defaults**: If neither `common_prompts` nor workflow `prompts` defines a value, use current hardcoded defaults

## Success Criteria

- [ ] `common_prompts` section can be defined at root level
- [ ] Workflows inherit unspecified prompts from `common_prompts`
- [ ] Workflow-specific prompts override `common_prompts` values
- [ ] Existing configs without `common_prompts` continue to work unchanged
- [ ] Configuration validation passes for new and existing formats
