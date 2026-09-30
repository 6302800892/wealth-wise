-- 0008: customer holdings (mutable positions, optionally tagged to a goal) and daily NAV prices (append-only).
-- Units and NAV are stored scaled by 10 000 (NFR-01). APPEND-ONLY FILE (NFR-05).

CREATE TABLE holdings (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (id),
    goal_id TEXT REFERENCES goals (id),
    asset_class_code TEXT NOT NULL REFERENCES asset_classes (code),
    units_scaled INTEGER NOT NULL CHECK (units_scaled >= 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX uq_holdings_position ON holdings (customer_id, COALESCE(goal_id, ''), asset_class_code);

CREATE TABLE nav_prices (
    nav_date TEXT NOT NULL,
    asset_class_code TEXT NOT NULL REFERENCES asset_classes (code),
    nav_scaled INTEGER NOT NULL CHECK (nav_scaled > 0),
    created_at TEXT NOT NULL,
    PRIMARY KEY (nav_date, asset_class_code)
);

CREATE TRIGGER trg_nav_prices_no_update BEFORE UPDATE ON nav_prices
BEGIN SELECT RAISE(ABORT, 'append-only table: nav_prices'); END;
CREATE TRIGGER trg_nav_prices_no_delete BEFORE DELETE ON nav_prices
BEGIN SELECT RAISE(ABORT, 'append-only table: nav_prices'); END;
