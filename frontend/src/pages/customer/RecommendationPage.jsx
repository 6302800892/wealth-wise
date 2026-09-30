import { useState } from "react";
import AllocationBar from "../../components/AllocationBar.jsx";
import DataTable from "../../components/DataTable.jsx";
import { BandBadge, Card, ErrorNotice, Notice } from "../../components/ui.jsx";
import { useAction, useResource } from "../../hooks/useResource.js";
import { formatPct, titleCase } from "../../lib/format.js";

const COLUMNS = [
  { key: "asset_class_name", label: "Asset class" },
  { key: "target_pct", label: "Target allocation", numeric: true, render: (a) => formatPct(a.target_pct) },
];

async function loadLatest(api) {
  try {
    return await api.get("/api/v1/me/recommendations/latest");
  } catch (error) {
    if (error.status === 404) return null;
    throw error;
  }
}

export default function RecommendationPage({ api }) {
  const state = useResource(() => loadLatest(api), [api]);
  const [fresh, setFresh] = useState(null);
  const { run, error, busy } = useAction();
  const recommendation = fresh || state.data;

  const generate = async () => {
    const result = await run(() => api.post("/api/v1/me/recommendations", {}));
    if (result) setFresh(result);
  };

  return (
    <div className="page">
      <h1>Recommended allocation</h1>
      <Card
        title="Portfolio recommendation"
        actions={
          <button type="button" className="primary" onClick={generate} disabled={busy} data-testid="generate-recommendation">
            Get recommendation
          </button>
        }
        testId="recommendation"
      >
        <ErrorNotice error={error || state.error} />
        {!recommendation && !error && <Notice>No recommendation yet. Complete your risk profile and add a goal.</Notice>}
        {recommendation && (
          <>
            <p className="meta">
              <BandBadge band={recommendation.risk_band} /> · Horizon{" "}
              <strong data-testid="horizon">{titleCase(recommendation.horizon_bucket)}</strong> · Template v
              {recommendation.template_version} · As of {recommendation.as_of_date}
            </p>
            <AllocationBar items={recommendation.allocation} />
            <DataTable columns={COLUMNS} rows={recommendation.allocation} rowKey={(a) => a.asset_class_code}
                       testId="allocation-table" />
            <p className="total">
              Total <strong data-testid="allocation-total">{formatPct(recommendation.total_pct)}</strong>
            </p>
          </>
        )}
      </Card>
    </div>
  );
}
