import { useState } from "react";
import DataTable from "../../components/DataTable.jsx";
import { BandBadge, Card, ErrorNotice, Loading, Stat } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";
import { formatInr, formatPct, titleCase } from "../../lib/format.js";

const REASONS = ["CHANGE_IN_CIRCUMSTANCES", "QUESTIONNAIRE_MISUNDERSTOOD", "ADVISOR_ASSESSMENT", "CUSTOMER_REQUEST"];

const HOLDING_COLUMNS = [
  { key: "asset_class_code", label: "Asset class" },
  { key: "value", label: "Value", numeric: true, render: (l) => formatInr(l.value) },
  { key: "current_pct", label: "Current", numeric: true, render: (l) => formatPct(l.current_pct) },
  { key: "target_pct", label: "Target", numeric: true, render: (l) => formatPct(l.target_pct) },
  { key: "drift_pct", label: "Drift", numeric: true, render: (l) => formatPct(l.drift_pct) },
];

const OVERRIDE_COLUMNS = [
  { key: "created_at", label: "When" },
  { key: "change", label: "Change", render: (o) => `${o.previous_band || "—"} → ${o.new_band}` },
  { key: "reason_code", label: "Reason", render: (o) => titleCase(o.reason_code) },
  { key: "note", label: "Note" },
];

async function load(api, id) {
  const [portfolio, audit] = await Promise.all([
    api.get(`/api/v1/advisor/customers/${id}/portfolio`),
    api.get(`/api/v1/advisor/customers/${id}/audit`),
  ]);
  return { portfolio, audit };
}

export default function CustomerDetailPage({ api, params }) {
  const state = useResource(() => load(api, params.id), [api, params.id]);
  const [override, setOverride] = useState({ new_band: "CONSERVATIVE", reason_code: REASONS[0], note: "" });
  const [note, setNote] = useState("");
  const { run, error, busy } = useAction();
  if (!state.data) return <Loading state={state} />;
  const { portfolio, audit } = state.data;

  const submitOverride = async (event) => {
    event.preventDefault();
    if (await run(() => api.post(`/api/v1/advisor/customers/${params.id}/risk-band-overrides`, override))) {
      setOverride({ ...override, note: "" });
      state.reload();
    }
  };
  const submitNote = async (event) => {
    event.preventDefault();
    if (await run(() => api.post(`/api/v1/advisor/customers/${params.id}/manual-recommendations`, { note }))) {
      setNote("");
      state.reload();
    }
  };

  return (
    <div className="page">
      <p><a href="#/advisor/customers">← All customers</a></p>
      <h1 data-testid="customer-name">{portfolio.customer.display_name}</h1>
      <div className="grid-3">
        <Card title="Risk band"><BandBadge band={portfolio.risk_profile.risk_band} /> <span className="muted">{titleCase(portfolio.risk_profile.source || "")}</span></Card>
        <Card title="Portfolio"><Stat label="Total value" value={formatInr(portfolio.holdings.total_value)} /></Card>
        <Card title="Goals"><Stat label="Active goals" value={String(portfolio.goals.length)} /></Card>
      </div>
      <Card title="Holdings and drift">
        <DataTable columns={HOLDING_COLUMNS} rows={portfolio.holdings.lines} rowKey={(l) => l.asset_class_code} testId="advisor-holdings" />
      </Card>
      <ErrorNotice error={error} />
      <div className="grid-2">
        <form className="card form-grid" onSubmit={submitOverride} data-testid="override-form">
          <h2>Override risk band</h2>
          <label>New band
            <select value={override.new_band} onChange={(e) => setOverride({ ...override, new_band: e.target.value })} data-testid="override-band">
              {["CONSERVATIVE", "MODERATE", "AGGRESSIVE"].map((b) => <option key={b} value={b}>{b}</option>)}
            </select>
          </label>
          <label>Reason
            <select value={override.reason_code} onChange={(e) => setOverride({ ...override, reason_code: e.target.value })} data-testid="override-reason">
              {REASONS.map((r) => <option key={r} value={r}>{titleCase(r)}</option>)}
            </select>
          </label>
          <label>Supporting note
            <textarea value={override.note} onChange={(e) => setOverride({ ...override, note: e.target.value })} maxLength={1000} required data-testid="override-note" />
          </label>
          <button type="submit" className="primary" disabled={busy} data-testid="override-submit">Record override</button>
        </form>
        <form className="card form-grid" onSubmit={submitNote} data-testid="manual-form">
          <h2>Log manual recommendation</h2>
          <label>Recommendation
            <textarea value={note} onChange={(e) => setNote(e.target.value)} maxLength={1000} required data-testid="manual-note" />
          </label>
          <button type="submit" disabled={busy} data-testid="manual-submit">Log recommendation</button>
        </form>
      </div>
      <Card title="Override audit trail" testId="override-audit">
        <DataTable columns={OVERRIDE_COLUMNS} rows={audit.overrides} rowKey={(o) => o.override_id} testId="override-table" empty="No overrides recorded." />
      </Card>
    </div>
  );
}
