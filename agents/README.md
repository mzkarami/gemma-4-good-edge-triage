# Edge-Triage Agent Templates

These templates describe the optional self-improving research loop behind Edge-Triage. They are not required to run the public demo or the field CLI.

Use them when you want to connect an NGO or research workspace, such as Paperclip, to the Edge-Triage benchmark loop:

1. Start with `AGENTS.md` to understand the agent roles.
2. Give the Researcher Agent the operating instructions in `SOUL.md`.
3. Give the agent the command allowlist and evaluation commands in `TOOLS.md`.
4. If your automation platform supports scheduled jobs, adapt `HEARTBEAT.md`.

The safe operating pattern is:

- keep `prepare.py` and the gold-set evaluation fixed;
- let agents propose small changes to `triage_sandbox.py` only;
- run the benchmark before accepting a change;
- record every run in `results.tsv`;
- require human review, or at least a protected pull request, before changes become deployment defaults.

The loop is inspired by Andrej Karpathy's AutoResearch-style idea: give an agent a sandbox, a fixed evaluation harness, and a keep/discard rule, then let measured experiments improve the system over time.
