# Optional Paperclip Plugin

This is a lightweight, optional Paperclip-style plugin skeleton for visualizing the Edge-Triage research loop.

It is not required for the public demo or the CLI. It is included so teams can see how to connect the benchmark ledger to an NGO/research workspace.

What it does:

- reads `results.tsv`;
- shows recent F1/latency/status rows;
- provides a local manual pulse button that runs `uv run triage_sandbox.py --description "paperclip manual pulse"` when the host platform grants shell capability.

Safety notes:

- The plugin is local/opt-in. Do not expose shell-capable automation to untrusted users.
- Keep generated logs under `logs/` and do not commit them.
- Keep uploaded images, private reports, and dataset shards out of git.
- Treat pull requests or human review as the promotion gate before agent-discovered changes become deployment defaults.
