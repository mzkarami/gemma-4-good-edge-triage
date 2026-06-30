# Evaluation-Window Stability

Status: current operating posture while external judging may still be active.

## Context

The Gemma 4 Good Kaggle submission package is closed. The team cannot resubmit or change the submitted Kaggle form, but judges may still evaluate the submitted public links, including the repository and demo URL:

```text
https://kaggle.nelly.work/index.html#volunteer
```

This repository therefore continues as the maintained public project artifact while preserving a stable evaluation experience.

## Stability surfaces

Treat these as non-breaking surfaces during the evaluation window:

- public demo URL and anchors, especially `index.html#volunteer`;
- README quick-start and documentation entry points;
- `docs/CURRENT_FRONTIER.md` as the public benchmark-claims source;
- `docs/KAGGLE_SUBMISSION.md`, `docs/KAGGLE_SUBMISSION_FINAL.md`, `docs/KAGGLE_WRITEUP.md`, and `docs/VIDEO_SCRIPT.md` as submitted-package reference material;
- curated demo, guarded Live Gemma preview, metrics page, volunteer app, and judge walkthrough pages.

## Allowed changes

Prefer additive improvements that make the project clearer without contradicting the submitted package:

- safety wording and public/private boundary clarification;
- validation reports and checkers;
- docs-link, claims, and stability checks;
- private operator runbooks;
- non-breaking UI polish that preserves existing routes and fallback behavior;
- future product work that is clearly labeled as ongoing improvement, not a resubmission.

## Avoid during active evaluation

- deleting, renaming, or moving submitted docs or public pages;
- changing public demo anchors or headline route names;
- changing headline metrics unless correcting a verified error with a validation report;
- making the submitted work look obsolete, abandoned, or replaced;
- implying that a Kaggle resubmission is possible;
- exposing private host details, Tailscale-only operations, secrets, or raw incident material in the public repo.

## Public wording rule

Use wording like:

> The submission package is closed. This repository continues as the maintained public project artifact, and public claims remain anchored in `docs/CURRENT_FRONTIER.md`.

Avoid wording that marks submitted materials as obsolete while judges may still be evaluating them.

## Verification

Before pushing public-facing changes during the evaluation window, run:

```bash
python3 scripts/check_docs_links.py
uv run python scripts/check_public_claims.py
uv run python scripts/check_evaluation_window_stability.py
uv run python scripts/run_ci_tests.py
```
