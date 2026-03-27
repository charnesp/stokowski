# Workspace Creation Specification

## ADDED Requirements

### Requirement: Project Discovery
**Status:** NEW

**Scenarios:**

1. Project exists
   - Given a repository URL "https://github.com/Fission-AI/OpenSpec.git"
   And a project "OpenSpec" already exists in Mux
   When the workspace creation is requested
   Then the existing project path "/Users/charles/.mux/projects/OpenSpec" is used
   And no cloning occurs

2. Project does not exist
   - Given a repository URL "https://github.com/Fission-AI/NewRepo.git"
   And no project "NewRepo" exists in Mux
   When the workspace creation is requested
   Then the repository is cloned to "/Users/charles/.mux/projects/NewRepo"
   And the project is created and trusted

### Requirement: Repository Cloning
**Status:** NEW

**Scenarios:**

1. Clone new repository
   - Given a repository URL and cloneParentDir "/Users/charles/.mux/projects"
   When clone is initiated
   Then SSE events are streamed showing progress
   And on success, the normalizedPath is returned
   And the project configuration includes workspaces array

2. Clone fails
   - Given an invalid repository URL
   When clone is attempted
   Then an error event is received
   And the workspace creation fails gracefully

### Requirement: Workspace Naming
**Status:** NEW

**Scenarios:**

1. Workspace name format
   - Given a project name "OpenSpec"
   And current date "2026-03-26"
   When a workspace is created
   Then the branch name follows "openspec-20260326-{6-char-hash}"
   And the name is in lowercase
   And the format is "{repo_name}-{YYYYMMDD}-{hash}"

### Requirement: Runtime Configuration
**Status:** NEW

**Scenarios:**

1. Worktree runtime
   - Given default-project-dir "/Users/charles/.mux/projects"
   When workspace is created
   Then runtimeConfig.type is "worktree"
   And runtimeConfig.srcBaseDir is "/Users/charles/.mux/src"
   And trunkBranch is auto-detected (main or master)

2. Trunk branch detection
   - Given a cloned repository with "master" as default branch
   When workspace is created
   Then trunkBranch is "master"
   And workspace creation succeeds

### Requirement: Auto-Trust
**Status:** NEW

**Scenarios:**

1. Auto-trust enabled
   - Given mux.auto_trust is true in configuration
   When a new project is created
   Then the project is automatically trusted via /api/projects/setTrust
   And workspace creation proceeds

2. Auto-trust disabled
   - Given mux.auto_trust is false
   When a project is not trusted
   Then workspace creation fails with appropriate error