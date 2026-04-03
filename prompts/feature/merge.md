# Merge State

You are in the merge state. The PR has been approved and is ready to be merged into the main branch. Your task is to complete the merge process, clean up resources, and finalize the issue.

## Merge Requirements

Use **squash merge** for a clean history:
```bash
gh pr merge --squash --delete-branch
```

Or if squash is disabled, use rebase:
```bash
gh pr merge --rebase --delete-branch
```

**Always delete the feature branch** after merge. Do not skip this step.

## Pre-Merge Verification

Before merging, verify:
1. PR status shows "Approved" in GitHub
2. All CI checks are passing (green)
3. No merge conflicts exist
4. Branch is up to date with main

If checks are failing, **stop** and transition to `rework` state. Do not merge a broken PR.

## Merge Steps

1. Switch to the PR branch:
   ```bash
   gh pr checkout <branch-name>
   ```

2. Pull latest changes:
   ```bash
   git pull origin main
   ```

3. Merge using squash strategy:
   ```bash
   gh pr merge --squash --delete-branch
   ```

4. If prompted, confirm merge or use `--auto` flag

## Post-Merge Verification

After merging, verify success:
```bash
gh pr view <pr-number> --json state,merged
```

Confirm:
- State shows "MERGED"
- Merged flag is true

## Linear Issue Update

Move the Linear issue to the "Done" state:
```bash
gh issue edit <issue-url> --state done
```

Or if using Linear CLI:
```bash
linear issue update <identifier> --state Done
```

Add a closing comment:
```
Merged via PR #<number>. Feature branch deleted. Issue complete.
```

## Cleanup

1. Delete the local feature branch if still present:
   ```bash
   git branch -d <branch-name>
   ```

2. Prune remote tracking branches:
   ```bash
   git fetch --prune
   ```

3. Verify workspace is clean (`git status` shows no uncommitted changes)

## Completion Criteria

Mark this state complete when:
- PR is merged into main
- Feature branch is deleted (local and remote)
- Linear issue is in "Done" state
- Closing comment is posted
- Workspace has no uncommitted changes

If any step fails, report the error and remain in this state. Do not proceed until merge is fully complete.
