import DataTable from "../../components/DataTable.jsx";
import { Badge, BandBadge, Card, Loading } from "../../components/ui.jsx";
import { useResource } from "../../hooks/useResource.js";

const COLUMNS = [
  {
    key: "display_name",
    label: "Customer",
    render: (c) => <a href={`#/advisor/customers/${c.customer_id}`} data-testid="customer-link">{c.display_name}</a>,
  },
  { key: "risk_band", label: "Risk band", render: (c) => <BandBadge band={c.risk_band} /> },
  { key: "kyc_verified", label: "KYC", render: (c) => (c.kyc_verified ? <Badge tone="success">Verified</Badge> : <Badge tone="warn">Pending</Badge>) },
  { key: "open_rebalancing", label: "Open rebalancing", numeric: true },
];

export default function CustomersPage({ api }) {
  const state = useResource(() => api.get("/api/v1/advisor/customers"), [api]);
  return (
    <div className="page">
      <h1>Customers</h1>
      <Card>
        {state.data ? (
          <DataTable columns={COLUMNS} rows={state.data.items} rowKey={(c) => c.customer_id} testId="customers-table" />
        ) : (
          <Loading state={state} />
        )}
      </Card>
    </div>
  );
}
