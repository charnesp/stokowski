# Proposal: Integrate Mux Workspace Creation into Stokowski

## Problem

Stokowski currently lacks integration with Mux as an agent provider. When using the Mux runner, workspaces must be created manually through the Mux UI or API. There is no automated workflow to:

1. Check if a project already exists in Mux
2. Clone a repository if needed
3. Create and trust projects automatically
4. Create workspaces with the correct runtime configuration (worktree)

This manual process is error-prone and prevents seamless operation of Stokowski with Mux as a runner.

## Solution

Integrate the validated Mux workspace creation workflow into Stokowski's MuxRunner. The workflow will:

1. List existing projects via `/api/projects/list`
2. Check if project exists by repository name
3. Clone repository via `/api/projects/clone` if not found
4. Create/trust project via `/api/projects/create` + `/api/projects/setTrust`
5. Create workspace in worktree mode via `/api/workspace/create`

## Scope

### In Scope
- Automatic project discovery and reuse
- Repository cloning when project doesn't exist
- Project creation and trust management
- Workspace creation with worktree runtime
- Configuration via workflow.yaml (endpoint, api_key, model, auto_trust)
- Workspace naming format: `{repo_name}-{YYYYMMDD}-{hash}`

### Out of Scope
- SSH runtime support (future enhancement)
- Docker/devcontainer runtime (future enhancement)
- Multi-project workspaces
- Workspace deletion/archival

## Success Criteria

- [ ] Workspaces are created automatically when running Mux agent
- [ ] Existing projects are reused without cloning
- [ ] New projects are cloned, created, and trusted automatically
- [ ] Workspaces use worktree runtime with correct srcBaseDir
- [ ] Workspace names follow `{repo_name}-{YYYYMMDD}-{hash}` format
- [ ] All existing tests pass
- [ ] New tests cover the workspace creation flow