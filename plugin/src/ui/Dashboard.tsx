/**
 * Edge-Triage Research Dashboard (Optional UI Slot)
 * 
 * A capability-gated dashboard that reads local metrics and 
 * provides a manual 'Pulse' trigger within the Paperclip UI.
 */

import React, { useEffect, useState } from 'react';

export default function Dashboard(ctx: any) {
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const fetchMetrics = async () => {
    setLoading(true);
    const result = await ctx.callWorker('getMetrics');
    if (result.success) {
      setMetrics(result);
    }
    setLoading(false);
  };

  const handlePulse = async () => {
    setLoading(true);
    await ctx.callWorker('runPulse');
    await fetchMetrics();
    setLoading(false);
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 60000); // Auto-refresh every minute
    return () => clearInterval(interval);
  }, []);

  if (!metrics) return <div style={{ padding: '20px' }}>Loading Dashboard...</div>;

  return (
    <div style={{ padding: '24px', fontFamily: 'monospace', color: '#e2e8f0', backgroundColor: '#0f172a', minHeight: '100vh' }}>
      <header style={{ marginBottom: '32px', borderBottom: '1px solid #334155', paddingBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '24px', margin: 0 }}>Edge-Triage Research</h1>
          <p style={{ color: '#94a3b8', marginTop: '4px' }}>Autonomous Optimization Dashboard</p>
        </div>
        <button 
          onClick={handlePulse}
          disabled={loading}
          style={{ padding: '8px 16px', backgroundColor: '#3b82f6', border: 'none', borderRadius: '4px', color: 'white', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading ? 'Processing...' : 'Manual Pulse'}
        </button>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
        <div style={{ padding: '20px', border: '1px solid #334155', borderRadius: '8px', backgroundColor: '#1e293b' }}>
          <h3 style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>F1-SCORE (Best)</h3>
          <p style={{ fontSize: '32px', color: '#10b981' }}>{Number(metrics.stats.current_f1).toFixed(4)}</p>
        </div>
        <div style={{ padding: '20px', border: '1px solid #334155', borderRadius: '8px', backgroundColor: '#1e293b' }}>
          <h3 style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>LATENCY (ms)</h3>
          <p style={{ fontSize: '32px', color: '#fbbf24' }}>{Number(metrics.stats.current_latency).toFixed(0)}</p>
        </div>
        <div style={{ padding: '20px', border: '1px solid #334155', borderRadius: '8px', backgroundColor: '#1e293b' }}>
          <h3 style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '8px' }}>TOTAL PULSES</h3>
          <p style={{ fontSize: '32px', color: '#3b82f6' }}>{metrics.stats.total_runs}</p>
        </div>
      </div>

      <div style={{ border: '1px solid #334155', borderRadius: '8px', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead style={{ backgroundColor: '#1e293b', color: '#94a3b8' }}>
            <tr>
              <th style={{ padding: '12px 16px' }}>Run</th>
              <th style={{ padding: '12px 16px' }}>F1-Score</th>
              <th style={{ padding: '12px 16px' }}>Latency</th>
              <th style={{ padding: '12px 16px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {metrics.data.map((run: any, idx: number) => (
              <tr key={idx} style={{ borderBottom: '1px solid #334155', color: run.status === 'keep' ? '#10b981' : '#f43f5e' }}>
                <td style={{ padding: '12px 16px' }}>{run.run_id || run.commit || 'local'}</td>
                <td style={{ padding: '12px 16px' }}>{Number(run.f1_score).toFixed(4)}</td>
                <td style={{ padding: '12px 16px' }}>{Number(run.latency_ms).toFixed(0)}ms</td>
                <td style={{ padding: '12px 16px' }}>{run.status.toUpperCase()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
