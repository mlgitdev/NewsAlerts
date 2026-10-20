# Contributing to NewsAlerts

Thank you for your interest in contributing to NewsAlerts! We welcome bug fixes, performance improvements, documentation updates, and new momentum strategies.

---

## 1. Governance & Permissions

- **Branch Protection**: The `main` branch is protected. Direct pushes to `main` are strictly prohibited.
- **Code Reviews & Ownership**: All contributions must be submitted as Pull Requests (PRs). Explicit code ownership across all components is governed by [`.github/CODEOWNERS`](.github/CODEOWNERS).
- **Approval Gate**: Only the designated code owner and repository maintainer (`@mlgitdev`) can approve and merge PRs into `main`.
- **Status Checks**: All automated checks (Secret Scanning, PR Validator, Multi-OS CI) must pass before a PR can be merged.

---

## 2. Issue-First Protocol & Lifecycle

Before writing code or spawning a worktree, **every contribution must have an active GitHub Issue**:
1. **Search Existing Issues**: Run `gh issue list` or search the repository to ensure the topic is not already tracked.
2. **Create an Issue**: If no issue exists, create one via the appropriate template:
   - **Bug Report** (`fix:`): For errors, unexpected behavior, or platform crashes.
   - **Feature Request** (`feat:`): For new filters, data sources, audio alerts, or UI capabilities.
   - **Task / Enhancement** (`task:`): For refactoring, testing, documentation, or CI/CD work.
3. **Correlate with PR**: The resolving PR must explicitly reference the issue in its body (`Resolves #<issue#>`).

---

## 3. Development Workflow (Git Worktrees)

To preserve the integrity of the root `main` branch and support clean parallel feature development, **all development work must take place inside an isolated Git Worktree**.

### Step 1: Clone the repository
```bash
git clone https://github.com/mlgitdev/NewsAlerts.git
cd NewsAlerts
```

### Step 2: Spawn a dedicated Worktree referencing the Issue
All worktrees are created under the ignored `.worktrees/` directory and should append the issue number:

```powershell
# Windows PowerShell
.\build.ps1 -Task worktree-new -Branch feat/your-feature-name-28 -Base main
# Or using the direct helper:
.\scripts\worktree.ps1 new feat/your-feature-name-28 main
```

```bash
# Linux / macOS Bash
./scripts/worktree.sh new feat/your-feature-name-28 main
```

*(Native git alternative: `git worktree add -b feat/your-feature-name-28 .worktrees/feat-your-feature-name-28 main`)*

### Step 3: Enter your worktree and develop
```bash
cd .worktrees/feat-your-feature-name
```
Worktrees automatically inherit the shared repository virtual environment (`.venv`) from the root directory.

### Step 4: Sub-Tasks & Parallel Worktrees (Optional)
If working on multi-phase tasks or parallel sub-features, branch from your feature branch:
```powershell
.\build.ps1 -Task worktree-new -Branch sub/feature/tests -Base feat/your-feature-name
```
When complete, merge back into your parent feature branch:
```powershell
.\build.ps1 -Task worktree-merge -Branch sub/feature/tests -Base feat/your-feature-name
.\build.ps1 -Task worktree-remove -Branch sub/feature/tests
```

### Step 5: Verify your changes
```powershell
# Windows
.\build.ps1 -Task build
.\build.ps1 -Task check
.\build.ps1 -Task verify-packages
```
```bash
# Linux / macOS
./run.sh
python3 -m unittest discover -s tests -p "test_*.py"
```

> **Important**: All PRs must pass the Package Verification Gate. If verification fails, the PR cannot be merged. In production, any failed package verification on `main` triggers automated tag deletion, branch rollback, and an incident issue.

### Step 6: Push your branch and open a Pull Request
```bash
git push -u origin feat/your-feature-name
gh pr create
```

### Step 7: Clean up your worktree after PR merge
```powershell
.\build.ps1 -Task worktree-remove -Branch feat/your-feature-name
```

---

## 4. Commit Conventions

We strictly enforce **Conventional Commits**:
`<type>(<scope>): <subject>`

### Allowed Types:
- `feat`: A new feature or capability.
- `fix`: A bug fix.
- `docs`: Documentation changes only.
- `style`: Changes that do not affect the meaning of the code (formatting, CSS tweaks).
- `refactor`: A code change that neither fixes a bug nor adds a feature.
- `perf`: A code change that improves performance.
- `test`: Adding or correcting tests.
- `build`: Changes that affect the build system or external dependencies.
- `ci`: Changes to CI/CD configuration files and scripts.
- `chore`: Miscellaneous housekeeping.

### Examples:
- `feat(tape): add momentum volume surge filter`
- `fix(sounds): prevent audio clipping during rapid alerts`
- `docs(install): update linux dependencies for fedora`

---

## 5. Pull Request Requirements

When creating a PR:
1. Title must conform to Conventional Commits.
2. Description must use the template defined in `.github/pull_request_template.md`.
3. Provide clear testing and verification steps.
4. Reference the resolving issue (`Resolves #<issue#>`).
5. Guarantee that zero credentials, secrets, or keys are committed.

---

## 6. Security & Secret Protection

- **Never** commit `keys.toml`, `secrets.toml`, `.env`, API keys, tokens, or passwords.
- Secret scanning bots automatically audit every PR. PRs containing sensitive patterns will be immediately rejected.
