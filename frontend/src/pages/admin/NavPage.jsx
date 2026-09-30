import { useState } from "react";
import DataTable from "../../components/DataTable.jsx";
import { Card, ErrorNotice, Loading, Notice } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";
import { formatInr } from "../../lib/format.js";

export default function NavPage({ api }) {
  const state = useResource(() => api.get("/api/v1/admin/nav/latest"), [api]);
  const [summary, setSummary] = useState(null);
  const { run, error, busy } = useAction();
  const refresh = async () => {
    const result = await run(() => api.post("/api/v1/admin/nav/refresh"));
    if (result) {
      setSummary(result);
      state.reload();
    }
  };
  const rows = state.data ? Object.entries(state.data.navs).map(([code, nav]) => ({ code, nav })) : [];
  return (
    <div className="page">
      <h1>NAV feed (stub)</h1>
      <ErrorNotice error={error} />
      {summary && (
        <Notice tone="success" testId="refresh-summary">
          Ingested {summary.nav_date}: {summary.goal_snapshots} goal snapshots, {summary.rebalancing_evaluated} customers
          evaluated, {summary.rebalancing_created} rebalancing proposals.
        </Notice>
      )}
      <Card title={`Latest NAV — ${state.data ? state.data.nav_date : "…"}`}
            actions={<button type="button" className="primary" onClick={refresh} disabled={busy} data-testid="run-refresh">Run daily refresh</button>}>
        {state.data ? (
          <DataTable columns={[{ key: "code", label: "Asset class" }, { key: "nav", label: "NAV", numeric: true, render: (r) => formatInr(r.nav) }]}
                     rows={rows} rowKey={(r) => r.code} testId="nav-table" />
        ) : <Loading state={state} />}
      </Card>
    </div>
  );
}
