-- 0007: goals (mutable, soft delete) and portfolio recommendations (append-only, BR-11).
-- APPEND-ONLY FILE (NFR-05).

CREATE TABLE goals (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (id),
    name TEXT NOT NULL,
    goal_type TEXT NOT NULL CHECK (goal_type IN ('RETIREMENT', 'EDUCATION', 'HOME', 'OTHER')),
    target_amount_paise INTEGER NOT NULL CHECK (target_amount_paise > 0),
    target_date TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    archived_at TEXT
);
CREATE INDEX idx_goals_customer ON goals (customer_id);

CREATE TABLE portfolio_recommendations (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (id),
    goal_id TEXT NOT NULL REFERENCES goals (id),
    risk_band_assignment_id TEXT NOT NULL REFERENCES risk_band_assignments (id),
    risk_band TEXT NOT NULL CHECK (risk_band IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE')),
    horizon_bucket TEXT NOT NULL CHECK (horizon_bucket IN ('SHORT', 'MEDIUM', 'LONG')),
    template_version INTEGER NOT NULL REFERENCES allocation_template_set_versions (version),
    as_of_date TEXT NOT NULL,
    input_fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_portfolio_recommendations_customer ON portfolio_recommendations (customer_id, created_at);

CREATE TABLE portfolio_recommendation_lines (
    recommendation_id TEXT NOT NULL REFERENCES portfolio_recommendations (id),
    asset_class_code TEXT NOT NULL REFERENCES asset_classes (code),
    target_bp INTEGER NOT NULL CHECK (target_bp BETWEEN 0 AND 10000),
    PRIMARY KEY (recommendation_id, asset_class_code)
);

CREATE TRIGGER trg_portfolio_recommendations_no_update BEFORE UPDATE ON portfolio_recommendations
BEGIN SELECT RAISE(ABORT, 'append-only table: portfolio_recommendations'); END;
CREATE TRIGGER trg_portfolio_recommendations_no_delete BEFORE DELETE ON portfolio_recommendations
BEGIN SELECT RAISE(ABORT, 'append-only table: portfolio_recommendations'); END;
CREATE TRIGGER trg_portfolio_recommendation_lines_no_update BEFORE UPDATE ON portfolio_recommendation_lines
BEGIN SELECT RAISE(ABORT, 'append-only table: portfolio_recommendation_lines'); END;
CREATE TRIGGER trg_portfolio_recommendation_lines_no_delete BEFORE DELETE ON portfolio_recommendation_lines
BEGIN SELECT RAISE(ABORT, 'append-only table: portfolio_recommendation_lines'); END;
