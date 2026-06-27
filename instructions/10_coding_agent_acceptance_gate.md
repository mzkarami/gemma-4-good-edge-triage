# Coding Agent Acceptance Gate

Status: mandatory pre-flight for non-trivial Edge-Triage code, docs, runtime, deployment, or benchmark work.

## Purpose

Agents must align each request with current implementation, humanitarian safety, public/private boundaries, and benchmark evidence before editing.

## Intake checklist

Record this in the working response or plan before substantial edits:

```text
Task classification:
- Area:
- Public repo, private repo, or both:
- Current, target/future, or historical/reference:
- User-visible behavior change: yes/no
- Safety/medical/incident-command impact: yes/no
- Data/privacy/deployment impact: yes/no
- Benchmark/frontier claim impact: yes/no
- Model/prompt/runtime boundary impact: yes/no
- Relevant docs read:
- Tests/checks required:
- Public/private artifact risk:
```

## Hard stops

Ask for explicit approval before work that would:

1. Add medical or incident-command authority claims.
2. Update public metrics without benchmark evidence and `docs/CURRENT_FRONTIER.md` alignment.
3. Expose model directories, `.env`, credentials, private deployment notes, raw sensitive disaster data, or Tailscale/server details in the public repo.
4. Weaken Live API guardrails to make a demo easier.
5. Couple field CLI startup to `triage_sandbox.py` or artifact bootstrap code.
6. Move private operator reality into public docs.
7. Publish generated logs/images/shards without a sanitization pass.

## Required verification matrix

### Docs-only changes

```bash
python3 scripts/check_docs_links.py
git diff --check
```

### Runtime or tests

```bash
uv run python -m unittest discover tests/
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

### GitHub/CI changes

After push, verify remote head and watch the relevant workflow to completion.
