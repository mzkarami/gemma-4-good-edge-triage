# Evaluation-Window Stability Alignment

Date: 2026-06-30
Change: documented and guarded the current operating posture for a closed Kaggle submission while judges may still evaluate submitted public links.

## Context

The Kaggle submission package is closed, so this work is not a resubmission path. The public repository and demo may still be reviewed through submitted links, so public-facing changes should preserve route stability, metric consistency, and non-contradictory submission-era material.

## What changed

- Added `docs/product/evaluation-window-stability.md` as the current stability posture.
- Updated roadmap/backlog/product docs so continuing improvement is framed as maintained-project work, not resubmission.
- Kept submission docs as submitted-package reference material rather than archive/obsolete material.
- Added `scripts/check_evaluation_window_stability.py` and `tests/test_evaluation_window_stability.py`.
- Added the stability checker to `scripts/run_ci_tests.py`.
- Aligned public/private boundary language with the private incident-queue runbook.

## Stability surfaces preserved

- `https://kaggle.nelly.work/index.html#volunteer`
- `site/index.html`
- `site/app.html`
- `site/judge.html`
- `site/metrics.html`
- `docs/CURRENT_FRONTIER.md`
- `docs/KAGGLE_SUBMISSION.md`
- `docs/KAGGLE_SUBMISSION_FINAL.md`
- `docs/KAGGLE_WRITEUP.md`
- `docs/VIDEO_SCRIPT.md`

## Commands run

```bash
python3 scripts/check_docs_links.py
uv run python scripts/check_public_claims.py
uv run python scripts/check_evaluation_window_stability.py
uv run python scripts/run_ci_tests.py
```

## Results

Local verification passed in both public and private repos:

```text
Markdown link check passed.
Public claims check passed.
Evaluation-window stability check passed.
Ran 66 tests
OK
```

GitHub Actions was checked after push from the session handoff.

## Risks

- Judges may still evaluate links at unpredictable times, so avoid disruptive public route or metric changes until judging is known to be complete.
- Live smoke during this session confirmed `/`, `/index.html`, `/index.html#volunteer`, `/app.html`, `/metrics.html`, and `/data.json` returned 200. `/judge.html` returned 404 on the current deployed host, so treat that as a source-repo page until a deliberate low-risk deployment updates the public site.
- Private operator runbooks may improve faster than public docs; keep public docs generic and sanitized.

## Follow-up

- Keep the public demo route smoke-tested before public pushes.
- Continue private operator workflow polish without exposing host-specific details.
- Consider optional TTS only after the text radio-script workflow remains stable.
