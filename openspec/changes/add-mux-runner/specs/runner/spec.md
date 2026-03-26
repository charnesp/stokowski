# Runner Specification

## ADDED Requirements

### Requirement: BaseRunner Interface
**Status:** NEW

**Scenarios:**
1. Abstract class defines common interface
   - Given a new provider needs to be added
   - When implementing BaseRunner
   - Then it must implement `run_turn()`, `supports_resume()`, `get_name()`

2. Type-safe configuration
   - Given a state config with runner field
   - When parsed by config.py
   - Then it validates against known runners

### Requirement: ClaudeRunner Implementation
**Status:** NEW

**Scenarios:**
1. CLI execution
   - Given a ClaudeRunner instance
   - When run_turn() is called with prompt
   - Then it executes `claude -p` subprocess

2. Multi-turn sessions
   - Given a session_id from previous turn
   - When run_turn() is called with resume
   - Then it adds `--resume <session_id>` to CLI

3. NDJSON streaming
   - Given stream-json format output
   - When processing events
   - Then it extracts result, session_id, token usage

### Requirement: MuxRunner Implementation
**Status:** NEW

**Scenarios:**
1. HTTP API call
   - Given a MuxRunner instance
   - When run_turn() is called
   - Then it POST to `/api/v1/tasks` with task payload

2. Session management
   - Given a previous turn with session_id
   - When run_turn() is called with resume
   - Then it uses the same parent_workspace_id

3. HTTP streaming
   - Given streaming enabled
   - When calling Mux API
   - Then it streams partial results via SSE or chunked response

4. Error handling
   - Given HTTP error (4xx/5xx)
   - When calling Mux API
   - Then it raises RunnerError with details

### Requirement: RunnerFactory
**Status:** NEW

**Scenarios:**
1. Factory creation
   - Given a runner type string ("claude" | "mux")
   - When calling RunnerFactory.create()
   - Then it returns the appropriate Runner instance

2. Unknown runner rejection
   - Given an unsupported runner type
   - When calling RunnerFactory.create()
   - Then it raises ConfigError

### Requirement: Configuration Extension
**Status:** NEW

**Scenarios:**
1. Per-state runner selection
   - Given workflow.yaml with `runner: mux` on a state
   - When config is parsed
   - Then state_config.runner == "mux"

2. Mux-specific config
   - Given mux API endpoint in config
   - When MuxRunner is instantiated
   - Then it uses the configured endpoint