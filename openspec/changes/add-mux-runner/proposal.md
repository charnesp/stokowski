# Proposal: Add Mux Runner

## Problem

Stokowski currently supports Claude Code via CLI subprocess. However, the architecture tightly couples CLI execution with the orchestration logic, making it difficult to add new agent providers. We need to support Mux as an alternative provider via its HTTP API.

## Solution

Create an abstraction layer with:
1. **BaseRunner** abstract class defining the common interface
2. **ClaudeRunner** implementation for CLI-based execution  
3. **MuxRunner** implementation for HTTP API-based execution
4. **RunnerFactory** to instantiate the appropriate runner based on configuration

## Scope

**In Scope:**
- BaseRunner abstract class with run_turn(), supports_resume(), get_name()
- ClaudeRunner refactored from existing runner.py logic
- MuxRunner with HTTP API calls to Mux server
- RunnerFactory for runner selection
- Config extension to support runner per state
- Orchestrator update to use factory

**Out of Scope:**
- Launching/managing Mux server (already running elsewhere)
- Web dashboard changes
- Other providers (GitHub Copilot, etc.)

## Success Criteria

- [ ] State configured with `runner: mux` executes via HTTP API
- [ ] State configured with `runner: claude` continues to work
- [ ] Multi-turn sessions work with Mux
- [ ] HTTP errors handled gracefully
- [ ] All existing tests pass