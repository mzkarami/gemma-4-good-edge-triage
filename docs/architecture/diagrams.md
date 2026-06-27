# Edge-Triage Architecture Diagrams

Status: current overview.

## Product and research split

```text
+----------------------+        +--------------------------+
| Field volunteer      |        | Research / response lead |
+----------+-----------+        +-------------+------------+
           |                                  |
           v                                  v
+----------------------+        +--------------------------+
| site/ or CLI         |        | triage_sandbox.py        |
+----------+-----------+        +-------------+------------+
           |                                  |
           v                                  v
+----------------------+        +--------------------------+
| edge_triage_core     |<-------| shared prompt contract   |
+----------+-----------+        +-------------+------------+
           |                                  |
           v                                  v
+----------------------+        +--------------------------+
| label + next action  |        | results.tsv + frontier   |
+----------------------+        +--------------------------+
```

## Runtime boundary

```text
edge_triage_core
  prompts / labels / config / results
        ^              ^              ^
        |              |              |
CLI field tool     Live API      Research sandbox
lazy model load    HTTP guards   benchmark lifecycle
```

## Public deployment

```text
Internet
  -> HTTPS reverse proxy
  -> localhost-bound static site
  -> optional localhost-bound Live API under /api/*
  -> local model files mounted read-only when live mode is enabled
```
