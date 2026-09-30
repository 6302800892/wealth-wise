import { BandBadge, Card, Loading, Notice, Stat } from "../../components/ui.jsx";
import { useResource } from "../../hooks/useResource.js";
import { capPct, formatInr, formatPct } from "../../lib/format.js";

async function loadDashboard(api) {
  const [profile, goals, holdings, rebalancing] = await Promise.all([
    api.get("/api/v1/me/risk-profile"),
    api.get("/api/v1/me/goals"),
    api.get("/api/v1/me/holdings"),
    api.get("/api/v1/me/rebalancing"),
  ]);
  const progress = await Promise.all(goals.items.map((g) => api.get(`/api/v1/me/goals/${g.goal_id}/progress`)));
  return { profile, holdings, progress, open: rebalancing.items.filter((r) => r.status === "OPEN") };
}

export default function DashboardPage({ api, session }) {
  const state = useResource(() => loadDashboard(api), [api]);
  if (!state.data) return <Loading state={state} />;
  const { profile, holdings, progress, open } = state.data;
  return (
    <div className="page">
      <h1>Hello, {session.display_name}</h1>
      {open.length > 0 && (
        <Notice tone="warn" testId="rebalancing-alert">
          Your portfolio has drifted {formatPct(open[0].max_drift_pct)} from target.{" "}
          <a href="#/rebalancing">Review the rebalancing proposal</a>
        </Notice>
      )}
      <div className="grid-3">
        <Card title="Risk profile">
          <BandBadge band={profile.risk_band} />
          {!profile.risk_band && <p><a href="#/risk-profile">Take the questionnaire</a></p>}
        </Card>
        <Card title="Portfolio value">
          <Stat label={`NAV date ${holdings.nav_date || "—"}`} value={formatInr(holdings.total_value)} testId="portfolio-total" />
        </Card>
        <Card title="Largest drift">
          <Stat label={`Threshold ${formatPct(holdings.threshold_pct)}`} value={formatPct(holdings.max_drift_pct)} />
        </Card>
      </div>
      <Card title="Goal progress" testId="goal-progress">
        {progress.length === 0 && <p className="muted">No goals yet. <a href="#/goals">Add a goal</a></p>}
        {progress.map((goal) => (
          <div key={goal.goal_id} className="progress-row">
            <div className="progress-label">
              <strong>{goal.name}</strong>
              <span className="muted">
                {formatInr(goal.current_value)} of {formatInr(goal.target_amount)} · {goal.status}
              </span>
            </div>
            <div className="progress-track" aria-label={`${goal.name} ${goal.percent_complete}%`}>
              <span className="progress-fill" style={{ width: `${capPct(goal.percent_complete)}%` }} />
            </div>
            <span className="numeric">{formatPct(goal.percent_complete)}</span>
          </div>
        ))}
      </Card>
    </div>
  );
}
