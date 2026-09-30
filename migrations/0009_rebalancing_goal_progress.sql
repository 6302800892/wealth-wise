-- 0009: goal progress snapshots and rebalancing (proposals, lines, decisions, stub orders) — all append-only.
-- APPEND-ONLY FILE (NFR-05).

CREATE TABLE goal_progress_snapshots (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL REFERENCES goals (id),
    nav_date TEXT NOT NULL,
    current_value_paise INTEGER NOT NULL CHECK (current_value_paise >= 0),
    target_amount_paise INTEGER NOT NULL CHECK (target_amount_paise > 0),
    percent_complete_bp INTEGER NOT NULL CHECK (percent_complete_bp >= 0),
    created_at TEXT NOT NULL,
    UNIQUE (goal_id, nav_date)
);

CREATE TABLE rebalancing_recommendations (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (id),
    portfolio_recommendation_id TEXT NOT NULL REFERENCES portfolio_recommendations (id),
    template_version INTEGER NOT NULL REFERENCES allocation_template_set_versions (version),
    nav_date TEXT NOT NULL,
    threshold_bp INTEGER NOT NULL,
    total_value_paise INTEGER NOT NULL,
    max_drift_bp INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX idx_rebalancing_customer ON rebalancing_recommendations (customer_id, created_at);

CREATE TABLE rebalancing_lines (
    rebalancing_id TEXT NOT NULL REFERENCES rebalancing_recommendations (id),
    asset_class_code TEXT NOT NULL REFERENCES asset_classes (code),
    current_bp INTEGER NOT NULL,
    target_bp INTEGER NOT NULL,
    drift_bp INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL', 'HOLD')),
    units_scaled INTEGER NOT NULL CHECK (units_scaled >= 0),
    trade_value_paise INTEGER NOT NULL CHECK (trade_value_paise >= 0),
    PRIMARY KEY (rebalancing_id, asset_class_code)
);

-- One terminal decision per proposal (BR-18): a second decision violates the UNIQUE constraint.
CREATE TABLE rebalancing_decisions (
    id TEXT PRIMARY KEY,
    rebalancing_id TEXT NOT NULL UNIQUE REFERENCES rebalancing_recommendations (id),
    status TEXT NOT NULL CHECK (status IN ('ACCEPTED', 'DISMISSED', 'SUPERSEDED')),
    reason TEXT CHECK (reason IS NULL OR length(reason) <= 500),
    actor_user_id TEXT REFERENCES users (id),
    decided_at TEXT NOT NULL
);

CREATE TABLE stub_orders (
    id TEXT PRIMARY KEY,
    rebalancing_id TEXT NOT NULL REFERENCES rebalancing_recommendations (id),
    asset_class_code TEXT NOT NULL REFERENCES asset_classes (code),
    action TEXT NOT NULL CHECK (action IN ('BUY', 'SELL')),
    units_scaled INTEGER NOT NULL CHECK (units_scaled > 0),
    status TEXT NOT NULL CHECK (status IN ('STUB_SUBMITTED')),
    created_at TEXT NOT NULL
);

CREATE TRIGGER trg_goal_progress_snapshots_no_update BEFORE UPDATE ON goal_progress_snapshots
BEGIN SELECT RAISE(ABORT, 'append-only table: goal_progress_snapshots'); END;
CREATE TRIGGER trg_goal_progress_snapshots_no_delete BEFORE DELETE ON goal_progress_snapshots
BEGIN SELECT RAISE(ABORT, 'append-only table: goal_progress_snapshots'); END;
CREATE TRIGGER trg_rebalancing_recommendations_no_update BEFORE UPDATE ON rebalancing_recommendations
BEGIN SELECT RAISE(ABORT, 'append-only table: rebalancing_recommendations'); END;
CREATE TRIGGER trg_rebalancing_recommendations_no_delete BEFORE DELETE ON rebalancing_recommendations
BEGIN SELECT RAISE(ABORT, 'append-only table: rebalancing_recommendations'); END;
CREATE TRIGGER trg_rebalancing_lines_no_update BEFORE UPDATE ON rebalancing_lines
BEGIN SELECT RAISE(ABORT, 'append-only table: rebalancing_lines'); END;
CREATE TRIGGER trg_rebalancing_lines_no_delete BEFORE DELETE ON rebalancing_lines
BEGIN SELECT RAISE(ABORT, 'append-only table: rebalancing_lines'); END;
CREATE TRIGGER trg_rebalancing_decisions_no_update BEFORE UPDATE ON rebalancing_decisions
BEGIN SELECT RAISE(ABORT, 'append-only table: rebalancing_decisions'); END;
CREATE TRIGGER trg_rebalancing_decisions_no_delete BEFORE DELETE ON rebalancing_decisions
BEGIN SELECT RAISE(ABORT, 'append-only table: rebalancing_decisions'); END;
CREATE TRIGGER trg_stub_orders_no_update BEFORE UPDATE ON stub_orders
BEGIN SELECT RAISE(ABORT, 'append-only table: stub_orders'); END;
CREATE TRIGGER trg_stub_orders_no_delete BEFORE DELETE ON stub_orders
BEGIN SELECT RAISE(ABORT, 'append-only table: stub_orders'); END;
