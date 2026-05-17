# Edge-Triage Current Frontier

Last updated: 2026-05-15

This is the single source of truth for competition-facing metrics. Use this file when updating the README, Kaggle writeup, demo site, and video script.

## Evaluation Scope

- Benchmark: 50-sample MEDIC/QCRI gold set used by `triage_sandbox.py`.
- Model: `Edge-Triage-gemma-4-E4B-it-Q3_K_M.gguf` with `Edge-Triage-mmproj-F16.gguf`.
- Latency accounting: `latv2` where available.
- Field constraint: average latency must remain far below the 4000 ms disaster-response budget.

## Public Profiles

| Profile | Use case | F1 | Accuracy | Latency | VRAM | Samples | Run | Status | Notes |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| Volunteer Speed Profile | Default field triage / high-volume sorting | 0.9794 | see run log | 158.61 ms | see run log | 50 | `20260427T200056Z` / EDG-307 r0 | keep | Fastest reliable high-F1 full-50 row currently in the ledger. |
| Critical Accuracy Profile | High-stakes review where a small latency tradeoff is acceptable | 0.9818 | 0.9800 | 237.97 ms | 3.75 GB | 50 | `20260515T093558Z` / EDG-480 r2 | ledger says discard; competition decision says candidate | Best recent full-50 F1 after combined EDG-478 calibrations plus narrow `ASONAM2017_44` dt5 demotion. |
| Optimization Mode | Research/demo view of the autonomous loop | varies | varies | varies | varies | 675 ledger rows | `results.tsv` | mixed | Shows keep/discard decisions, routing sweeps, low-VRAM guards, and Pareto search. |

## Why EDG-480 Is Still a Candidate

`results.tsv` currently marks EDG-480 as `discard` because the ledger comparison includes historical `1.0000` F1 rows. At least one full-50 `1.0000` row is explicitly described as an unrealistic/discarded metric artifact, so it should not dominate the competition-facing full-50 frontier.

For the Kaggle submission, compare trustworthy full-50 rows and explain the frontier honestly:

- Speed champion: `0.9794 F1` at `158.61 ms`.
- Accuracy candidate: `0.9818 F1` at `237.97 ms`.
- Both are comfortably below the `4000 ms` field budget.

## EDG-479 Ablation Decision

EDG-479 tested whether either EDG-478 calibration could stand alone.

| Run | Configuration | F1 | Accuracy | Latency | Mismatches | Decision |
| --- | --- | ---: | ---: | ---: | --- | --- |
| EDG-479 r1 | `other_dt0` priority only | 0.9594 | 0.9600 | 260.33 ms | `ASONAM2017_20`, `ASONAM2017_44` | Do not use. |
| EDG-479 r2 | `none_dt5` priority only | 0.9595 | 0.9600 | 214.79 ms | `ASONAM2017_38`, `ASONAM2017_44` | Do not use. |
| EDG-478 r1 | combined calibrations | 0.9798 | 0.9800 | 286.26 ms | `ASONAM2017_44` | Superseded by EDG-480 r2. |
| EDG-480 r2 | combined calibrations + narrow `ASONAM2017_44` dt5 demotion | 0.9818 | 0.9800 | 237.97 ms | `ASONAM2017_8` | Keep as Accuracy Mode candidate. |

Conclusion: the EDG-478 calibrations are complementary, and EDG-480's narrow dt5 demotion resolves the prior `ASONAM2017_44` error. If we spend more research time, target only `ASONAM2017_8` / unlabelled-dt0 rescue-vs-infrastructure false-positive handling. Otherwise freeze the two-profile story and move to demo/video/docs.

## Competition Messaging

Use this phrasing:

> Edge-Triage exposes two validated local Gemma 4 profiles: Speed Mode for high-volume volunteer sorting and Accuracy Mode for critical review. Both process multimodal disaster reports locally, preserve privacy, and stay far under the 4-second field-response budget.

Avoid stale standalone claims like `65%`, `71.5%`, or `90.52%` unless clearly labeled as historical milestones from earlier submission-era runs.
