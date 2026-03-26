# Agent Instructions for Stokowski

## Important Notes

### Package Management
- **Use uv for Python package management**: Always use `uv add` and `uv run` for managing Python packages in this project.
  - `uv add <package>` - Add production dependency
  - `uv add --dev <package>` - Add development dependency
  - `uv run python ...` - Run Python with project dependencies

### Development Workflow  
- **Never stop before task completion**: Always complete all tasks in a phase before asking if you should continue.
  - Complete Phase 1 (tests) before stopping
  - Complete Phase 2 (implementation) before stopping
  - Complete Phase 3 (refactor) before stopping
  - Complete Phase 4 (documentation) before stopping

### TDD Strict Mode
- Write failing test first (RED)
- Implement minimal code to pass (GREEN)
- Refactor while keeping tests green (REFACTOR)
- Commit after each working cycle

## Architecture Notes

### Runner Abstraction
The project now supports multiple runners:
- `ClaudeRunner` - CLI-based execution via subprocess
- `MuxRunner` - HTTP API-based execution

Runner selection is configured per-state in workflow.yaml:
```yaml
states:
  coding:
    type: agent
    runner: mux  # or "claude"
```

### Mux Configuration
To use Mux as a runner, configure the `mux` section in `workflow.yaml`:

```yaml
# Mux HTTP API configuration
mux:
  endpoint: http://localhost:9988  # Mux API server URL
  api_key: ""                      # Optional API key for authentication
  model: ollama:kimi-k2.5:cloud    # Format: provider:model
                                   # Examples:
                                   #   anthropic:claude-sonnet-4-6
                                   #   ollama:kimi-k2.5:cloud
                                   #   openai:gpt-4
```

Then configure states to use `runner: mux`:
```yaml
states:
  code-review:
    type: agent
    runner: mux
    prompt: prompts/review.md
```

**Note:** The `workflow.yaml` file is gitignored (operator-local config). Copy from `workflow.example.yaml` and customize.

### Key Files
- `stokowski/runners/base.py` - BaseRunner abstract class
- `stokowski/runners/claude_runner.py` - Claude CLI implementation
- `stokowski/runners/mux_runner.py` - Mux HTTP implementation
- `stokowski/runners/factory.py` - RunnerFactory for instantiation
- `stokowski/runner.py` - Legacy integration layer