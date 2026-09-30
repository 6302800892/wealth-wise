import { useEffect, useState } from "react";
import DataTable from "../../components/DataTable.jsx";
import { Badge, Card, ErrorNotice, Loading, Notice } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";

const VERSION_COLUMNS = [
  { key: "version", label: "Version" },
  { key: "status", label: "Status", render: (v) => <Badge tone={v.status === "DRAFT" ? "warn" : "success"}>{v.status}</Badge> },
  { key: "published_at", label: "Published", render: (v) => v.published_at || "—" },
];

async function load(api) {
  const list = await api.get("/api/v1/admin/risk-rule-sets");
  const target = list.items.find((v) => v.status === "DRAFT") || list.items.find((v) => v.version === list.active_version);
  return { list, current: await api.get(`/api/v1/admin/risk-rule-sets/${target.version}`) };
}

export default function RuleSetsPage({ api }) {
  const state = useResource(() => load(api), [api]);
  const [bands, setBands] = useState(null);
  const [message, setMessage] = useState(null);
  const { run, error, busy } = useAction();
  useEffect(() => setBands(state.data ? state.data.current.definition.bands : null), [state.data]);
  if (!state.data || !bands) return <Loading state={state} />;
  const { list, current } = state.data;
  const editable = current.status === "DRAFT";
  const base = "/api/v1/admin/risk-rule-sets";
  const act = async (action, done) => {
    setMessage(null);
    if (await run(action)) {
      setMessage(done);
      state.reload();
    }
  };
  const setScore = (index, field, value) =>
    setBands(bands.map((b, i) => (i === index ? { ...b, [field]: Number.parseInt(value, 10) || 0 } : b)));

  return (
    <div className="page">
      <h1>Risk rule sets</h1>
      <Card title={`Versions (active v${list.active_version})`}
            actions={!editable && <button type="button" className="primary" onClick={() => act(() => api.post(base), "Draft created")} data-testid="create-rule-draft">New draft</button>}>
        <DataTable columns={VERSION_COLUMNS} rows={list.items} rowKey={(v) => v.version} testId="rule-set-versions" />
      </Card>
      <ErrorNotice error={error} />
      {message && <Notice tone="success">{message}</Notice>}
      <Card title={`${editable ? "Draft" : "Published"} v${current.version}: band thresholds`} testId="band-editor">
        <table className="data-table">
          <thead><tr><th>Band</th><th>Min score</th><th>Max score</th></tr></thead>
          <tbody>
            {bands.map((band, index) => (
              <tr key={band.band}>
                <td data-label="Band">{band.band}</td>
                {["min_score", "max_score"].map((field) => (
                  <td key={field} data-label={field}>
                    <input type="number" value={band[field]} disabled={!editable}
                           onChange={(e) => setScore(index, field, e.target.value)} data-testid={`${band.band}-${field}`} />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <p className="muted">{current.definition.questions.length} questions. Published versions are read-only.</p>
        {editable && (
          <div className="decision-row">
            <button type="button" disabled={busy} data-testid="save-rule-draft"
                    onClick={() => act(() => api.put(`${base}/${current.version}`, { ...current.definition, bands }), "Draft saved")}>Save draft</button>
            <button type="button" className="primary" disabled={busy} data-testid="publish-rule-draft"
                    onClick={() => act(() => api.post(`${base}/${current.version}/publish`), `Published v${current.version}`)}>Publish</button>
          </div>
        )}
      </Card>
    </div>
  );
}
