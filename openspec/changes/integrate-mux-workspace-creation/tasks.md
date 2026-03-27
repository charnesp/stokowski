# Implementation Tasks: Integrate Mux Workspace Creation

## Task 1: Create MuxWorkspaceManager Class

- [ ] **Step 1: RED - Write failing test**
  Create: `tests/runners/test_mux_workspace_manager.py`
  ```python
  async def test_list_projects_returns_list():
      manager = MuxWorkspaceManager(config)
      projects = await manager.list_projects()
      assert isinstance(projects, list)
  ```
  Run: `uv run pytest tests/runners/test_mux_workspace_manager.py -v`
  Expected: FAIL - MuxWorkspaceManager not defined

- [ ] **Step 2: Verify RED - Watch it fail**
  Confirm error: "MuxWorkspaceManager not defined"

- [ ] **Step 3: GREEN - Write minimal implementation**
  Create: `stokowski/runners/mux_workspace_manager.py`
  ```python
  class MuxWorkspaceManager:
      def __init__(self, config):
          self.config = config
          self.endpoint = config.endpoint
          self.headers = {"Authorization": f"Bearer {config.api_key}"}
      
      async def list_projects(self):
          pass
  ```

- [ ] **Step 4: Verify GREEN - Watch it pass**
  Run: `uv run pytest tests/runners/test_mux_workspace_manager.py -v`
  Expected: PASS

- [ ] **Step 5: REFACTOR - Clean up**
  Add proper error handling

- [ ] **Step 6: Commit**
  ```bash
  git add stokowski/runners/mux_workspace_manager.py tests/runners/test_mux_workspace_manager.py
  git commit -m "feat: add MuxWorkspaceManager skeleton"
  ```

## Task 2: Implement Project Discovery

- [ ] **Step 1: RED - Write failing test**
  ```python
  async def test_find_project_by_repo_name():
      manager = MuxWorkspaceManager(config)
      # Mock list_projects to return test data
      project_path = await manager.find_project_by_repo_name("OpenSpec")
      assert "/OpenSpec" in project_path
  ```

- [ ] **Step 2-6: TDD Cycle**
  Implement `find_project_by_repo_name()` method
  
- [ ] **Commit**
  ```bash
  git commit -m "feat: add project discovery by repo name"
  ```

## Task 3: Implement Repository Cloning

- [ ] **Step 1: RED - Write failing test**
  ```python
  async def test_clone_project_streams_events():
      manager = MuxWorkspaceManager(config)
      events = []
      async for event in manager.clone_project(repo_url, parent_dir):
          events.append(event)
      assert len(events) > 0
  ```

- [ ] **Step 2-6: TDD Cycle**
  Implement `clone_project()` with SSE parsing
  
- [ ] **Commit**
  ```bash
  git commit -m "feat: add repository cloning with SSE streaming"
  ```

## Task 4: Implement Project Creation and Trust

- [ ] **Step 1: RED - Write failing test**
  Test `create_project()` and `set_project_trust()`

- [ ] **Step 2-6: TDD Cycle**
  Implement both methods
  
- [ ] **Commit**
  ```bash
  git commit -m "feat: add project creation and trust management"
  ```

## Task 5: Implement Workspace Creation with Worktree

- [ ] **Step 1: RED - Write failing test**
  ```python
  async def test_create_workspace_uses_worktree():
      result = await manager.create_workspace(path, title)
      assert result["metadata"]["runtimeConfig"]["type"] == "worktree"
  ```

- [ ] **Step 2-6: TDD Cycle**
  - Implement `create_workspace()`
  - Calculate srcBaseDir from default-project-dir
  - Auto-detect trunk branch
  - Generate branch name with timestamp format
  
- [ ] **Commit**
  ```bash
  git commit -m "feat: add workspace creation with worktree runtime"
  ```

## Task 6: Integrate into MuxRunner

- [ ] **Step 1: RED - Write failing test**
  Update `test_mux_runner.py` to expect workspace creation

- [ ] **Step 2: Verify RED**
  
- [ ] **Step 3: GREEN - Modify MuxRunner.run_turn()**
  ```python
  async def run_turn(self, prompt, ...):
      # Get or create project
      # Get or create workspace
      # Send message to workspace
  ```

- [ ] **Step 4: Verify GREEN**

- [ ] **Step 5: REFACTOR**

- [ ] **Step 6: Commit**
  ```bash
  git commit -m "feat: integrate workspace creation into MuxRunner"
  ```

## Task 7: Update Configuration

- [ ] **Step 1: Update MuxConfig**
  Add `auto_trust: bool = False` field

- [ ] **Step 2: Update config.py parsing**
  Parse `auto_trust` from workflow.yaml

- [ ] **Step 3: Update workflow.example.yaml**
  Add documentation for `auto_trust`

- [ ] **Commit**
  ```bash
  git commit -m "feat: add auto_trust configuration option"
  ```

## Task 8: Final Integration Test

- [ ] **Run full test suite**
  ```bash
  uv run pytest tests/ -v
  ```
  Expected: All tests pass

- [ ] **Manual end-to-end test**
  ```bash
  # Test with existing project
  python tests-python.py create /Users/charles/.mux/projects/OpenSpec "Test"
  
  # Test with new project (cloning)
  # Clean up OpenSpec first, then retry
  ```

- [ ] **Commit**
  ```bash
  git commit -m "test: add integration tests for workspace creation"
  ```

## Completion Checklist

- [ ] All 8 tasks completed with TDD
- [ ] All tests pass
- [ ] Manual testing successful
- [ ] Documentation updated
- [ ] Ready for `/opsx:archive`