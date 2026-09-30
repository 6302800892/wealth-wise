// Small presentational building blocks shared by every page.

export function Card({ title, actions, children, testId }) {
  return (
    <section className="card" data-testid={testId}>
      {(title || actions) && (
        <header className="card-header">
          {title && <h2>{title}</h2>}
          {actions && <div className="card-actions">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}

export function ErrorNotice({ error }) {
  if (!error) return null;
  return (
    <div className="notice notice-error" role="alert" data-testid="error-notice">
      <strong>{error.code || "Error"}</strong> {error.message}
    </div>
  );
}

export function Notice({ tone = "info", children, testId }) {
  return (
    <div className={`notice notice-${tone}`} data-testid={testId}>
      {children}
    </div>
  );
}

export function Badge({ tone = "neutral", children, testId }) {
  return (
    <span className={`badge badge-${tone}`} data-testid={testId}>
      {children}
    </span>
  );
}

export function Stat({ label, value, testId }) {
  return (
    <div className="stat">
      <span className="stat-label">{label}</span>
      <span className="stat-value" data-testid={testId}>
        {value}
      </span>
    </div>
  );
}

export function Loading({ state }) {
  if (state.loading && !state.data) return <p className="muted">Loading…</p>;
  return <ErrorNotice error={state.error} />;
}

const BAND_TONE = { CONSERVATIVE: "info", MODERATE: "warn", AGGRESSIVE: "danger" };

export function BandBadge({ band }) {
  if (!band) return <Badge>Not profiled</Badge>;
  return (
    <Badge tone={BAND_TONE[band]} testId="risk-band">
      {band}
    </Badge>
  );
}
