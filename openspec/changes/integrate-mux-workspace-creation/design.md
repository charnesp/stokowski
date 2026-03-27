# Technical Design: Integrate Mux Workspace Creation

## Overview

Integrate Mux workspace creation workflow into Stokowski's MuxRunner to enable automatic project discovery, cloning, and workspace creation with worktree runtime.

## Architecture

### Components

1. **MuxWorkspaceManager** (new class)
   - Manages Mux API interactions
   - Handles project lifecycle (list, clone, create, trust)
   - Creates workspaces with proper runtime configuration

2. **MuxRunner** (modified)
   - Integrates MuxWorkspaceManager
   - Uses automatic project discovery
   - Creates workspaces before running agents

3. **Configuration** (mux section in workflow.yaml)
   - endpoint: Mux API URL
   - api_key: Authentication token
   - model: Model identifier
   - auto_trust: Enable automatic project trust

## Data Flow

```
Stokowski Task
    ↓
MuxRunner.run_turn()
    ↓
MuxWorkspaceManager.create_workspace_for_repo(repo_url, title)
    ↓
1. List projects → Find existing?
    ↓
   YES → Use existing project_path
    ↓
   NO  → get_default_project_dir → clone → create_project → trust
    ↓
2. get_default_project_dir → calculate srcBaseDir
    ↓
3. detect_trunk_branch (git rev-parse)
    ↓
4. POST /api/workspace/create with worktree runtime
    ↓
Return workspace_id
```

## Components Detail

### MuxWorkspaceManager

```python
class MuxWorkspaceManager:
    def __init__(self, config: MuxConfig)
    
    async def list_projects() -> List[Tuple[str, dict]]
    
    async def get_default_project_dir() -> str
    
    async def clone_project(repo_url: str, parent_dir: str) -> AsyncGenerator[dict]
    
    async def create_project(project_path: str, auto_trust: bool) -> dict
    
    async def set_project_trust(project_path: str, trusted: bool) -> bool
    
    async def create_workspace(
        project_path: str,
        title: str,
        trunk_branch: str = "main"
    ) -> dict
    
    async def create_workspace_for_repo(
        repo_url: str,
        title: str
    ) -> dict:
        # Complete workflow:
        # 1. List and find project
        # 2. Clone if needed
        # 3. Create/trust project
        # 4. Create workspace
```

### MuxConfig Updates

```python
@dataclass
class MuxConfig:
    endpoint: str = "http://localhost:9988"
    api_key: str = ""
    model: str = "claude-sonnet-4-6"
    auto_trust: bool = False  # NEW: Enable auto-trust
```

## Error Handling

| Scenario | Response |
|----------|----------|
| Project not found | Clone and create |
| Clone fails | Raise RunnerError with details |
| Project exists but not trusted | Trust if auto_trust=True, else fail |
| Workspace create fails | Raise RunnerError |
| Invalid trunk branch | Default to "main" |

## Testing Strategy

1. Unit tests for MuxWorkspaceManager methods
2. Integration tests with mocked Mux API
3. End-to-end test with real Mux instance (localhost:9988)
4. Test both existing project reuse and new project cloning paths