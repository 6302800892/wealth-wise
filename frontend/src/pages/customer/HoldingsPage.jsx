import { useState } from "react";
import DataTable from "../../components/DataTable.jsx";
import { Badge, Card, ErrorNotice, Loading, Stat } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";
import { formatInr, formatPct, formatUnits } from "../../lib/format.js";

const COLUMNS = [
  { key: "asset_class_name", label: "Asset class" },
  { key: "units", label: "Units", numeric: true, render: (l) => formatUnits(l.units) },
  { key: "nav", label: "NAV", numeric: true, render: (l) => formatInr(l.nav) },
  { key: "value", label: "Value", numeric: true, render: (l) => formatInr(l.value) },
  { key: "current_pct", label: "Current", numeric: true, render: (l) => formatPct(l.current_pct) },
  { key: "target_pct", label: "Target", numeric: true, render: (l) => formatPct(l.target_pct) },
  {
    key: "drift_pct",
    label: "Drift",
    numeric: true,
    render: (l) =>
      l.exceeds_threshold ? <Badge tone="danger" testId={`drift-${l.asset_class_code}`}>{formatPct(l.drift_pct)}</Badge>
        : <span data-testid={`drift-${l.asset_class_code}`}>{formatPct(l.drift_pct)}</span>,
  },
];

export default function HoldingsPage({ api }) {
  const holdings = useResource(() => api.get("/api/v1/me/holdings"), [api]);
  const goals = useResource(() => api.get("/api/v1/me/goals"), [api]);
  const [form, setForm] = useState({ asset_class_code: "EQUITY", goal_id: "", units: "" });
  const { run, error, busy } = useAction();

  const submit = async (event) => {
    event.preventDefault();
    const body = { ...form, goal_id: form.goal_id || null };
    if (await run(() => api.post("/api/v1/me/holdings", body))) holdings.reload();
  };

  if (!holdings.data) return <Loading state={holdings} />;
  const data = holdings.data;
  return (
    <div className="page">
      <h1>Holdings and drift</h1>
      <div className="grid-3">
        <Stat label="Total value" value={formatInr(data.total_value)} testId="holdings-total" />
        <Stat label="Largest drift" value={formatPct(data.max_drift_pct)} testId="max-drift" />
        <Stat label="Rebalance threshold" value={formatPct(data.threshold_pct)} />
      </div>
      <Card title={`Positions (NAV ${data.nav_date || "—"}, template v${data.template_version || "—"})`}>
        <DataTable columns={COLUMNS} rows={data.lines} rowKey={(l) => l.asset_class_code} testId="holdings-table"
                   empty="No holdings recorded yet." />
      </Card>
      <form className="card form-grid" onSubmit={submit} data-testid="holding-form">
        <h2>Record a holding (simulated)</h2>
        <label>
          Asset class
          <select value={form.asset_class_code} onChange={(e) => setForm({ ...form, asset_class_code: e.target.value })}>
            {["EQUITY", "DEBT", "GOLD", "CASH"].map((code) => <option key={code} value={code}>{code}</option>)}
          </select>
        </label>
        <label>
          Goal
          <select value={form.goal_id} onChange={(e) => setForm({ ...form, goal_id: e.target.value })}>
            <option value="">Not linked to a goal</option>
            {(goals.data ? goals.data.items : []).map((g) => <option key={g.goal_id} value={g.goal_id}>{g.name}</option>)}
          </select>
        </label>
        <label>
          Units
          <input value={form.units} onChange={(e) => setForm({ ...form, units: e.target.value })} inputMode="decimal"
                 placeholder="10.0000" required data-testid="holding-units" />
        </label>
        <ErrorNotice error={error} />
        <button type="submit" className="primary" disabled={busy}>Save holding</button>
      </form>
    </div>
  );
}
