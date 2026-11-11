---
name: netflix-dl-document-changes
description: Create or refresh CHANGES_FROM_MAIN.md when asked to document the Netflix-DL working tree compared with the local main branch.
---

# Document changes from main

Update `CHANGES_FROM_MAIN.md` in the repository root. Use the local `main` ref as the baseline. If it is missing, report that and leave the report untouched.

- Use `git diff main` for the net tracked changes, including staged and unstaged edits. Use `git status --short` and `git ls-files --others --exclude-standard` to identify new project source, configuration, and documentation. Use `git log --oneline main..HEAD` for context where needed.
- Cover the behavior and operational impact of every changed project file. Group related files by feature and use repository-relative Markdown links. Include setup commands, dependencies, behavior changes, and limitations supported by the diff. Identify the baseline commit and describe the working-tree scope.
- Exclude `CHANGES_FROM_MAIN.md` itself, generated downloads, local state, and secret values. Document changes to secret handling using variable and file names. Avoid opening credential files, cookie exports, and downloaded media.
- Edit only `CHANGES_FROM_MAIN.md`. Verify coverage against the changed-file inventory and check the report for stale claims. Keep the comparison local and leave the Git index and refs untouched.
