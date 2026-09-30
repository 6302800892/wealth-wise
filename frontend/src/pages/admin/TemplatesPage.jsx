import { useEffect, useState } from "react";
import DataTable from "../../components/DataTable.jsx";
import { Badge, Card, ErrorNotice, Loading, Notice } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";
import { sumPct } from "../../lib/format.js";

const VERSION_COLUMNS = [
  { key: "version", label: "Version" },
  { key: "status", label: "Status", render: (v) => <Badge tone={v.status === "DRAFT" ? "warn" : "success"}>{v.status}</Badge> },
  { key: "published_at", label: "Published", render: (v) => v.published_at || "—" },
];

async function load(api) {
  const list = await api.get("/api/v1/admin/allocation-templates");
  const draftMeta = list.items.find((v) => v.status === "DRAFT");
  const draft = draftMeta ? await api.get(`/api/v1/admin/allocation-templates/${draftMeta.version}`) : null;
  return { list, draft };
}

function RowEditor({ row, codes, onChange }) {
  const total = sumPct(codes.map((code) => row.allocations[code] ?? ""));
  const valid = total === "100.00";
  const key = `${row.risk_band}-${row.horizon_bucket}`;
  return (
    <tr data-testid={`template-row-${key}`}>
      <th scope="row">{row.risk_band} / {row.horizon_bucket}</th>
      {codes.map((code) => (
        <td key={code} data-label={code}>
          <input className="pct-input" value={row.allocations[code] ?? ""} inputMode="decimal"
                 onChange={(e) => onChange({ ...row, allocations: { ...row.allocations, [code]: e.target.value } })}
                 data-testid={`cell-${key}-${code}`} aria-label={`${key} ${code}`} />
        </td>
      ))}
      <td data-label="Sum" className="numeric">
        <Badge tone={valid ? "success" : "danger"} testId={`sum-${key}`}>{total ?? "invalid"}</Badge>
      </td>
    </tr>
  );
}

export default function TemplatesPage({ api }) {
  const state = useResource(() => load(api), [api]);
  const [rows, setRows] = useState(null);
  const { run, error, busy } = useAction();
  const [message, setMessage] = useState(null);
  useEffect(() => setRows(state.data && state.data.draft ? state.data.draft.rows : null), [state.data]);
  if (!state.data) return <Loading state={state} />;
  const { list, draft } = state.data;
  const codes = rows && rows.length ? Object.keys(rows[0].allocations) : [];

  const act = async (action, done) => {
    setMessage(null);
    if (await run(action)) {
      setMessage(done);
      state.reload();
    }
  };
  const base = "/api/v1/admin/allocation-templates";

  return (
    <div className="page">
      <h1>Allocation templates</h1>
      <Card title={`Versions (active v${list.active_version})`}
            actions={!draft && <button type="button" className="primary" onClick={() => act(() => api.post(base), "Draft created")} data-testid="create-draft">New draft</button>}>
        <DataTable columns={VERSION_COLUMNS} rows={list.items} rowKey={(v) => v.version} testId="template-versions" />
      </Card>
      <ErrorNotice error={error} />
      {message && <Notice tone="success" testId="template-message">{message}</Notice>}
      {draft && rows && (
        <Card title={`Draft v${draft.version}`} testId="template-editor">
          <div className="table-scroll">
            <table className="data-table editor-table">
              <thead><tr><th>Band / horizon</th>{codes.map((c) => <th key={c}>{c}</th>)}<th>Sum</th></tr></thead>
              <tbody>
                {rows.map((row, index) => (
                  <RowEditor key={`${row.risk_band}-${row.horizon_bucket}`} row={row} codes={codes}
                             onChange={(next) => setRows(rows.map((r, i) => (i === index ? next : r)))} />
                ))}
              </tbody>
            </table>
          </div>
          <div className="decision-row">
            <button type="button" onClick={() => act(() => api.put(`${base}/${draft.version}`, { rows }), "Draft saved")} disabled={busy} data-testid="save-draft">Save draft</button>
            <button type="button" className="primary" onClick={() => act(() => api.post(`${base}/${draft.version}/publish`), `Published v${draft.version}`)} disabled={busy} data-testid="publish-draft">Publish</button>
          </div>
        </Card>
      )}
    </div>
  );
}
