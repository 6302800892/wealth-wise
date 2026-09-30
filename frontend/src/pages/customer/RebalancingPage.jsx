import { useState } from "react";
import DataTable from "../../components/DataTable.jsx";
import { Badge, Card, ErrorNotice, Loading, Notice } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";
import { formatInr, formatPct, formatUnits } from "../../lib/format.js";

const ACTION_TONE = { BUY: "success", SELL: "danger", HOLD: "neutral" };

const LINE_COLUMNS = [
  { key: "asset_class_code", label: "Asset class" },
  { key: "current_pct", label: "Current", numeric: true, render: (l) => formatPct(l.current_pct) },
  { key: "target_pct", label: "Target", numeric: true, render: (l) => formatPct(l.target_pct) },
  { key: "drift_pct", label: "Drift", numeric: true, render: (l) => formatPct(l.drift_pct) },
  { key: "action", label: "Action", render: (l) => <Badge tone={ACTION_TONE[l.action]}>{l.action}</Badge> },
  { key: "units", label: "Units", numeric: true, render: (l) => formatUnits(l.units) },
  { key: "trade_value", label: "Trade value", numeric: true, render: (l) => formatInr(l.trade_value) },
];

const HISTORY_COLUMNS = [
  { key: "created_at", label: "Proposed" },
  { key: "max_drift_pct", label: "Max drift", numeric: true, render: (r) => formatPct(r.max_drift_pct) },
  { key: "status", label: "Status", render: (r) => <Badge>{r.status}</Badge> },
];

export default function RebalancingPage({ api }) {
  const state = useResource(() => api.get("/api/v1/me/rebalancing"), [api]);
  const [reason, setReason] = useState("");
  const { run, error, busy } = useAction();
  if (!state.data) return <Loading state={state} />;
  const open = state.data.items.find((item) => item.status === "OPEN");
  const decide = async (verb, body) => {
    if (await run(() => api.post(`/api/v1/me/rebalancing/${open.recommendation_id}/${verb}`, body))) state.reload();
  };
  const evaluate = async () => {
    if (await run(() => api.post("/api/v1/me/rebalancing/evaluate"))) state.reload();
  };

  return (
    <div className="page">
      <h1>Rebalancing</h1>
      <ErrorNotice error={error} />
      <Card
        title="Open proposal"
        actions={<button type="button" onClick={evaluate} disabled={busy} data-testid="evaluate-drift">Check drift now</button>}
        testId="open-proposal"
      >
        {!open && <Notice testId="no-open-proposal">Your portfolio is within its drift threshold.</Notice>}
        {open && (
          <>
            <p className="meta">
              Max drift <strong>{formatPct(open.max_drift_pct)}</strong> (threshold {formatPct(open.threshold_pct)}) ·
              NAV {open.nav_date} · Template v{open.template_version}
            </p>
            <DataTable columns={LINE_COLUMNS} rows={open.lines} rowKey={(l) => l.asset_class_code} testId="proposal-lines" />
            <div className="decision-row">
              <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Reason for dismissing (optional)"
                     maxLength={500} data-testid="dismiss-reason" />
              <button type="button" onClick={() => decide("dismiss", { reason: reason || null })} disabled={busy}
                      data-testid="dismiss-proposal">Dismiss</button>
              <button type="button" className="primary" onClick={() => decide("accept")} disabled={busy}
                      data-testid="accept-proposal">Accept and place stub orders</button>
            </div>
          </>
        )}
      </Card>
      <Card title="History">
        <DataTable columns={HISTORY_COLUMNS} rows={state.data.items} rowKey={(r) => r.recommendation_id}
                   testId="rebalancing-history" />
      </Card>
    </div>
  );
}
