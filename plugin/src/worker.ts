/**
 * Paperclip Plugin Worker (Optional Sidecar)
 *
 * This worker acts as a capability-gated bridge between the core CLI project
 * and the Paperclip visual dashboard.
 */

type RunRow = Record<string, string>;

function parseResults(raw: string): RunRow[] {
  const lines = raw.trim().split('\n').filter(Boolean);
  if (lines.length < 2) return [];

  const headers: string[] = lines[0].split('\t');
  return lines.slice(1).map((line: string) => {
    const values: string[] = line.split('\t');
    const obj: RunRow = {};
    headers.forEach((header: string, index: number) => {
      obj[header] = values[index] ?? '';
    });
    return obj;
  });
}

export default {
  /**
   * Returns the last benchmark results from results.tsv.
   */
  async getMetrics(ctx: any) {
    try {
      const raw = await ctx.fs.readFile('results.tsv', 'utf-8');
      const data = parseResults(raw);
      const kept = data.filter((row) => row.status === 'keep' || row.status === 'candidate');
      const best = kept.length ? kept[kept.length - 1] : data[data.length - 1];

      return {
        success: true,
        data: data.slice(-50),
        stats: {
          current_f1: best?.f1_score || 0,
          current_latency: best?.latency_ms || 0,
          total_runs: data.length,
        },
      };
    } catch (e: any) {
      return { success: false, error: e.message };
    }
  },

  /**
   * Triggers a local optimization pulse from the UI.
   * Only enable this in trusted local workspaces because it requires shell capability.
   */
  async runPulse(ctx: any) {
    try {
      const result = await ctx.shell.run(
        'mkdir -p logs && uv run triage_sandbox.py --description "paperclip manual pulse" > logs/paperclip-pulse.log 2>&1'
      );
      return { success: true, output: result.stdout };
    } catch (e: any) {
      return { success: false, error: e.message };
    }
  },
};
