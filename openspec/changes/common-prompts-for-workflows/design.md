# Design: `common_prompts` Implementation

## Overview

The implementation adds a `common_prompts` field to `ServiceConfig` and modifies the workflow parsing logic to merge common prompts with workflow-specific prompts.

## Changes Required

### 1. Config Data Model (`stokowski/config.py`)

**Add to `ServiceConfig` dataclass:**
```python
@dataclass
class ServiceConfig:
    # ... existing fields ...
    common_prompts: PromptsConfig = field(default_factory=PromptsConfig)
    prompts: PromptsConfig = field(default_factory=PromptsConfig)
    # ... rest of fields ...
```

**Add merge helper to `PromptsConfig`:**
```python
def merge_with_defaults(self, defaults: PromptsConfig) -> PromptsConfig:
    """Return new PromptsConfig with values from self overriding defaults."""
    return PromptsConfig(
        global_prompt=self.global_prompt if self.global_prompt is not None else defaults.global_prompt,
        lifecycle_prompt=self.lifecycle_prompt if self.lifecycle_prompt != "prompts/lifecycle.md" or defaults.lifecycle_prompt == "prompts/lifecycle.md" else defaults.lifecycle_prompt,
        lifecycle_post_run_prompt=self.lifecycle_post_run_prompt if self.lifecycle_post_run_prompt is not None else defaults.lifecycle_post_run_prompt,
    )
```

### 2. Parsing Logic (`stokowski/config.py`)

**In `parse_workflow_file()`:**

1. Parse `common_prompts` section (if present) into `PromptsConfig`
2. When parsing each workflow, merge workflow's `prompts` with `common_prompts`:
   ```python
   wf_prompts_raw = wf_data.get("prompts", {}) or {}
   wf_prompts = PromptsConfig(
       global_prompt=wf_prompts_raw.get("global_prompt"),
       lifecycle_prompt=wf_prompts_raw.get("lifecycle_prompt", "prompts/lifecycle.md"),
       lifecycle_post_run_prompt=wf_prompts_raw.get("lifecycle_post_run_prompt"),
   )
   # Merge with common_prompts - workflow takes precedence
   final_prompts = wf_prompts.merge_with_defaults(common_prompts)
   ```

### 3. Prompt Resolution Order

The effective prompt resolution follows this priority (highest to lowest):

1. **Workflow-specific `prompts`**: Values explicitly set in the workflow
2. **`common_prompts`**: Values defined in the root-level common section
3. **Built-in defaults**: Current hardcoded defaults in `PromptsConfig`

### 4. Example Configurations

**Full common prompts with partial workflow override:**
```yaml
common_prompts:
  global_prompt: prompts/global.md
  lifecycle_prompt: prompts/lifecycle.md
  lifecycle_post_run_prompt: prompts/lifecycle-post-run.md

workflows:
  feature:
    label: feature
    prompts:
      global_prompt: prompts/feature/global.md  # Override
      # lifecycle_prompt and lifecycle_post_run_prompt inherited
```

**No common_prompts (backwards compatibility):**
```yaml
workflows:
  feature:
    label: feature
    prompts:
      global_prompt: prompts/feature/global.md
      lifecycle_prompt: prompts/lifecycle.md
      lifecycle_post_run_prompt: prompts/lifecycle-post-run.md
```

**Common prompts only, no workflow prompts:**
```yaml
common_prompts:
  lifecycle_prompt: prompts/lifecycle.md
  lifecycle_post_run_prompt: prompts/lifecycle-post-run.md

workflows:
  feature:
    label: feature
    # All prompts inherited from common_prompts
```

### 5. Validation Considerations

- No additional validation required
- Existing validation for prompt file existence continues to work
- Empty `common_prompts` is valid (equivalent to not having the section)

## Files Modified

- `stokowski/config.py`: Add parsing and merge logic

## Testing Strategy

1. Unit tests for `PromptsConfig.merge_with_defaults()`
2. Integration tests for `parse_workflow_file()` with various configurations
3. Backwards compatibility tests for existing configs
