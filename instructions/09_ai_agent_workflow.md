# AI Agent Workflow

## Before changing files

1. Pull latest if network/remote state matters.
2. Check `git status --short`.
3. Read relevant `instructions/` and `docs/architecture/` docs.
4. Fill the coding-agent acceptance gate for non-trivial changes.
5. Identify whether the change affects public repo, private repo, or both.

## During implementation

- Prefer small commits and frequent verification.
- Keep protected artifacts and private data out of public git.
- Update docs and user stories in the same slice when behavior or architecture changes.
- Do not turn target/future ideas into current claims.

## Before reporting success

- Run the required tests/checks.
- Read back git status and remote branch head if pushed.
- Watch GitHub Actions when workflows are triggered.
- Report blockers honestly instead of inventing deploy or benchmark success.
