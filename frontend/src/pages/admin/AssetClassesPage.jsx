import { useState } from "react";
import DataTable from "../../components/DataTable.jsx";
import { Badge, Card, ErrorNotice, Loading } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";

export default function AssetClassesPage({ api }) {
  const state = useResource(() => api.get("/api/v1/admin/asset-classes"), [api]);
  const [form, setForm] = useState({ code: "", name: "", display_order: "5" });
  const { run, error, busy } = useAction();
  const toggle = async (item) => {
    if (await run(() => api.patch(`/api/v1/admin/asset-classes/${item.code}`, { is_active: !item.is_active }))) state.reload();
  };
  const submit = async (event) => {
    event.preventDefault();
    const body = { ...form, display_order: Number.parseInt(form.display_order, 10) };
    if (await run(() => api.post("/api/v1/admin/asset-classes", body))) state.reload();
  };
  const columns = [
    { key: "code", label: "Code" },
    { key: "name", label: "Name" },
    { key: "display_order", label: "Order", numeric: true },
    { key: "is_active", label: "Status", render: (a) => <Badge tone={a.is_active ? "success" : "neutral"}>{a.is_active ? "Active" : "Inactive"}</Badge> },
    { key: "toggle", label: "", render: (a) => <button type="button" onClick={() => toggle(a)} disabled={busy}>{a.is_active ? "Deactivate" : "Activate"}</button> },
  ];
  return (
    <div className="page">
      <h1>Asset classes</h1>
      <ErrorNotice error={error} />
      <Card>
        {state.data ? <DataTable columns={columns} rows={state.data.items} rowKey={(a) => a.code} testId="asset-classes" /> : <Loading state={state} />}
      </Card>
      <form className="card form-grid" onSubmit={submit}>
        <h2>Add asset class</h2>
        <label>Code<input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} required /></label>
        <label>Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
        <label>Display order<input type="number" min="1" value={form.display_order} onChange={(e) => setForm({ ...form, display_order: e.target.value })} /></label>
        <button type="submit" className="primary" disabled={busy}>Add</button>
      </form>
    </div>
  );
}
