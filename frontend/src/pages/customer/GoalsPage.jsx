import { useState } from "react";
import DataTable from "../../components/DataTable.jsx";
import { Card, ErrorNotice, Loading } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";
import { formatInr, titleCase } from "../../lib/format.js";

const EMPTY = { name: "", goal_type: "RETIREMENT", target_amount: "", target_date: "", priority: "HIGH" };

const COLUMNS = [
  { key: "name", label: "Goal" },
  { key: "goal_type", label: "Type", render: (g) => titleCase(g.goal_type) },
  { key: "priority", label: "Priority", render: (g) => titleCase(g.priority) },
  { key: "target_date", label: "Target date" },
  { key: "target_amount", label: "Target", numeric: true, render: (g) => formatInr(g.target_amount) },
];

export default function GoalsPage({ api }) {
  const state = useResource(() => api.get("/api/v1/me/goals"), [api]);
  const [form, setForm] = useState(EMPTY);
  const { run, error, busy } = useAction();
  const set = (field) => (event) => setForm({ ...form, [field]: event.target.value });

  const submit = async (event) => {
    event.preventDefault();
    if (await run(() => api.post("/api/v1/me/goals", form))) {
      setForm(EMPTY);
      state.reload();
    }
  };

  return (
    <div className="page">
      <h1>Financial goals</h1>
      <Card title="Your goals">
        {state.data ? (
          <DataTable columns={COLUMNS} rows={state.data.items} rowKey={(g) => g.goal_id} testId="goals-table" />
        ) : (
          <Loading state={state} />
        )}
      </Card>
      <form className="card form-grid" onSubmit={submit} data-testid="goal-form">
        <h2>Add a goal</h2>
        <label>
          Name
          <input value={form.name} onChange={set("name")} required data-testid="goal-name" />
        </label>
        <label>
          Type
          <select value={form.goal_type} onChange={set("goal_type")} data-testid="goal-type">
            {["RETIREMENT", "EDUCATION", "HOME", "OTHER"].map((t) => <option key={t} value={t}>{titleCase(t)}</option>)}
          </select>
        </label>
        <label>
          Target amount (₹)
          <input value={form.target_amount} onChange={set("target_amount")} inputMode="decimal" placeholder="500000.00"
                 required data-testid="goal-amount" />
        </label>
        <label>
          Target date
          <input type="date" value={form.target_date} onChange={set("target_date")} required data-testid="goal-date" />
        </label>
        <label>
          Priority
          <select value={form.priority} onChange={set("priority")} data-testid="goal-priority">
            {["HIGH", "MEDIUM", "LOW"].map((p) => <option key={p} value={p}>{titleCase(p)}</option>)}
          </select>
        </label>
        <ErrorNotice error={error} />
        <button type="submit" className="primary" disabled={busy} data-testid="goal-submit">
          Save goal
        </button>
      </form>
    </div>
  );
}
