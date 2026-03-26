# Implementation Tasks: Add Mux Runner (TDD Strict)

## Phase 1: Write Tests (RED)

### Task 1: Test BaseRunner Interface

- [x] **Step 1.1: Write test for RunResult dataclass**
  ```python
  # tests/runners/test_base.py
  def test_run_result_creation():
      result = RunResult(result="test", session_id="123", 
                        input_tokens=100, output_tokens=50, total_tokens=150)
      assert result.total_tokens == 150
  ```
  Expected: Test fails (RunResult doesn't exist yet)

- [x] **Step 1.2: Write test for BaseRunner interface**
  ```python
  def test_base_runner_is_abstract():
      with pytest.raises(TypeError):
          BaseRunner(config=None)  # Cannot instantiate abstract class
  ```
  Expected: Test fails (BaseRunner doesn't exist yet)

- [x] **Step 1.3: Write test for RunnerError hierarchy**
  ```python
  def test_runner_error_subclasses():
      assert issubclass(RunnerTimeout, RunnerError)
      assert issubclass(RunnerConnectionError, RunnerError)
  ```
  Expected: Test fails (exceptions don't exist yet)

### Task 2: Test RunnerFactory

- [x] **Step 2.1: Write test for creating ClaudeRunner**
  ```python
  # tests/runners/test_factory.py
  def test_factory_creates_claude_runner():
      runner = RunnerFactory.create("claude", mock_config)
      assert isinstance(runner, ClaudeRunner)
  ```
  Expected: Test fails (Factory doesn't exist yet)

- [x] **Step 2.2: Write test for creating MuxRunner**
  ```python
  def test_factory_creates_mux_runner():
      runner = RunnerFactory.create("mux", mock_config, mux_endpoint="http://test:9988")
      assert isinstance(runner, MuxRunner)
      assert runner.endpoint == "http://test:9988"
  ```
  Expected: Test fails (Factory doesn't exist yet)

- [x] **Step 2.3: Write test for unknown runner rejection**
  ```python
  def test_factory_rejects_unknown_runner():
      with pytest.raises(ConfigError):
          RunnerFactory.create("unknown", mock_config)
  ```
  Expected: Test fails (Factory doesn't exist yet)

### Task 3: Test ClaudeRunner

- [ ] **Step 3.1: Write test for ClaudeRunner creation**
  ```python
  # tests/runners/test_claude_runner.py
  def test_claude_runner_has_correct_name():
      runner = ClaudeRunner(mock_config)
      assert runner.get_name() == "claude"
      assert runner.supports_resume() is True
  ```
  Expected: Test fails (ClaudeRunner doesn't exist yet)

- [ ] **Step 3.2: Write test for CLI command building**
  ```python
  def test_claude_runner_builds_command():
      runner = ClaudeRunner(mock_config)
      cmd = runner._build_command("test prompt", session_id=None)
      assert "claude" in cmd
      assert "-p" in cmd
  ```
  Expected: Test fails (ClaudeRunner doesn't exist yet)

- [ ] **Step 3.3: Write test for multi-turn command**
  ```python
  def test_claude_runner_adds_resume_flag():
      runner = ClaudeRunner(mock_config)
      cmd = runner._build_command("test", session_id="abc-123")
      assert "--resume" in cmd
      assert "abc-123" in cmd
  ```
  Expected: Test fails (ClaudeRunner doesn't exist yet)

### Task 4: Test MuxRunner

- [ ] **Step 4.1: Write test for MuxRunner creation**
  ```python
  # tests/runners/test_mux_runner.py
  def test_mux_runner_has_correct_name():
      runner = MuxRunner(mock_config, endpoint="http://test:9988")
      assert runner.get_name() == "mux"
      assert runner.supports_resume() is True
      assert runner.endpoint == "http://test:9988"
  ```
  Expected: Test fails (MuxRunner doesn't exist yet)

- [ ] **Step 4.2: Write test for HTTP payload building**
  ```python
  def test_mux_runner_builds_payload():
      runner = MuxRunner(mock_config, endpoint="http://test:9988")
      payload = runner._build_payload("test prompt", session_id="ws-123")
      assert payload["prompt"] == "test prompt"
      assert payload["parent_workspace_id"] == "ws-123"
  ```
  Expected: Test fails (MuxRunner doesn't exist yet)

- [ ] **Step 4.3: Write test for HTTP error handling**
  ```python
  @pytest.mark.asyncio
  async def test_mux_runner_raises_on_http_error(httpx_mock):
      httpx_mock.add_response(status_code=500, text="Server Error")
      runner = MuxRunner(mock_config, endpoint="http://test:9988")
      with pytest.raises(RunnerError):
          await runner.run_turn("test")
  ```
  Expected: Test fails (MuxRunner doesn't exist yet)

### Task 5: Test Configuration Extension

- [ ] **Step 5.1: Write test for runner field parsing**
  ```python
  # tests/test_config.py
  def test_config_parses_runner_field():
      yaml_content = """
      states:
        test:
          type: agent
          runner: mux
      """
      config = parse_workflow_file(yaml_content)
      assert config.states["test"].runner == "mux"
  ```
  Expected: Test fails (runner field not in config yet)

## Phase 2: Implement (GREEN)

### Task 6: Implement BaseRunner

- [ ] **Step 6.1: Implement RunResult dataclass**
  Create `stokowski/runners/base.py` with RunResult and exceptions
  Expected: Tests from Task 1 pass

- [ ] **Step 6.2: Implement BaseRunner abstract class**
  Add abstract methods: run_turn(), supports_resume(), get_name()
  Expected: Tests from Task 1 pass

### Task 7: Implement RunnerFactory

- [ ] **Step 7.1: Implement Factory with placeholder runners**
  Create `stokowski/runners/factory.py` with stubs
  Expected: Tests from Task 2 pass

- [ ] **Step 7.2: Export from runners package**
  Update `stokowski/runners/__init__.py`
  Expected: Import tests pass

### Task 8: Implement ClaudeRunner

- [ ] **Step 8.1: Implement ClaudeRunner class**
  Create `stokowski/runners/claude_runner.py`
  - Implement get_name(), supports_resume()
  - Implement _build_command()
  - Stub run_turn() with NotImplementedError
  Expected: Tests from Task 3 pass

- [ ] **Step 8.2: Move existing logic from runner.py**
  - Refactor _build_claude_args → _build_command
  - Keep run_turn implementation for later
  Expected: All Claude tests pass

### Task 9: Implement MuxRunner

- [ ] **Step 9.1: Implement MuxRunner class**
  Create `stokowski/runners/mux_runner.py`
  - Implement get_name(), supports_resume(), _build_payload()
  - Stub run_turn() with NotImplementedError
  Expected: Tests from Task 4 pass (except async test)

- [ ] **Step 9.2: Implement HTTP streaming logic**
  - Implement run_turn() with httpx streaming
  - Implement error handling
  Expected: All Mux tests pass

### Task 10: Implement Full run_turn Methods

- [ ] **Step 10.1: Implement ClaudeRunner.run_turn()**
  - Move full logic from runner.py
  - Ensure all tests pass
  Expected: ClaudeRunner fully functional

- [ ] **Step 10.2: Implement MuxRunner.run_turn()**
  - Complete HTTP implementation
  - Ensure all tests pass
  Expected: MuxRunner fully functional

### Task 11: Update Configuration

- [ ] **Step 11.1: Add runner field to StateConfig**
  Update `stokowski/config.py`
  Expected: Config tests pass

- [ ] **Step 11.2: Parse runner from workflow.yaml**
  Update parsing logic
  Expected: YAML parsing tests pass

### Task 12: Update Orchestrator

- [ ] **Step 12.1: Import and use factory**
  Update `stokowski/orchestrator.py`
  Expected: Import succeeds

- [ ] **Step 12.2: Replace runner calls with factory pattern**
  Get runner type from state config, create via factory
  Expected: Orchestrator uses new runner system

## Phase 3: Refactor (REFACTOR)

### Task 13: Code Quality

- [ ] **Step 13.1: Remove duplication**
  - Extract common streaming logic if possible
  - Extract common error handling
  Expected: All tests still pass

- [ ] **Step 13.2: Improve naming and documentation**
  - Add comprehensive docstrings
  - Ensure type hints throughout
  Expected: All tests still pass

### Task 14: Integration Testing

- [ ] **Step 14.1: Test workflow with Claude runner**
  - End-to-end test with real workflow
  Expected: Workflow completes successfully

- [ ] **Step 14.2: Test workflow with Mux runner**
  - End-to-end test with real workflow
  Expected: Workflow completes successfully

- [ ] **Step 14.3: Test backward compatibility**
  - Ensure existing Claude-only configs still work
  Expected: Default runner is "claude"

## Phase 4: Documentation

### Task 15: Final Documentation

- [ ] **Step 15.1: Update docstrings**
  - Document BaseRunner interface
  - Document each runner class
  - Document factory usage
  Expected: All public APIs documented

- [ ] **Step 15.2: Update README/example**
  - Add example with runner selection
  - Document mux endpoint config
  Expected: Documentation complete