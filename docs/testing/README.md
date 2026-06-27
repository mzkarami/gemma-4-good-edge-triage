# Edge-Triage Testing and Evaluation

Status: testing documentation index.

## Start here

- [Test strategy](test-strategy.md)
- [Validation reports](validation-reports/README.md)
- [Performance evidence](performance/README.md)

## Standard local verification

```bash
python3 scripts/check_docs_links.py
git diff --check
uv run python -m unittest discover tests/
uv run python edge-triage-cli.py --help
uv run python triage_sandbox.py --help
```

## Evidence hierarchy

- Unit tests and import-boundary tests prove local contracts.
- GitHub Actions proves fresh-checkout viability.
- Validation reports explain substantial changes.
- `results.tsv` and `docs/CURRENT_FRONTIER.md` define benchmark claims.
