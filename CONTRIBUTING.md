# Contributing to NewsAlerts

Thank you for your interest in contributing to NewsAlerts! We welcome bug fixes, performance improvements, documentation updates, and new momentum strategies.

---

## 1. Governance & Permissions

- **Branch Protection**: The `main` branch is protected. Direct pushes to `main` are strictly prohibited.
- **Code Reviews**: All contributions must be submitted as Pull Requests (PRs).
- **Approval Gate**: Only the repository owner (`@mlgitdev`) can approve and merge PRs into `main`.
- **Status Checks**: All automated checks (Secret Scanning, PR Validator, Multi-OS CI) must pass before a PR can be merged.

---

## 2. Development Workflow

1. Fork or clone the repository:
   ```bash
   git clone https://github.com/mlgitdev/NewsAlerts.git
   cd NewsAlerts
   ```
2. Create a dedicated feature branch from `main`:
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
3. Set up your local environment:
   ```powershell
   # Windows
   .\build.ps1 -Task run
   ```
   ```bash
   # Linux / macOS
   chmod +x run.sh
   ./run.sh
   ```

---

## 3. Commit Conventions

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

## 4. Pull Request Requirements

When creating a PR:
1. Title must conform to Conventional Commits.
2. Description must use the template defined in `.github/pull_request_template.md`.
3. Provide clear testing and verification steps.
4. Guarantee that zero credentials, secrets, or keys are committed.

---

## 5. Security & Secret Protection

- **Never** commit `keys.toml`, `secrets.toml`, `.env`, API keys, tokens, or passwords.
- Secret scanning bots automatically audit every PR. PRs containing sensitive patterns will be immediately rejected.
