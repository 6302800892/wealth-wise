-- 0010: advisor-logged manual recommendations (append-only). APPEND-ONLY FILE (NFR-05).

CREATE TABLE manual_recommendations (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (id),
    advisor_user_id TEXT NOT NULL REFERENCES users (id),
    note TEXT NOT NULL CHECK (length(trim(note)) BETWEEN 1 AND 1000),
    created_at TEXT NOT NULL
);

CREATE TRIGGER trg_manual_recommendations_no_update BEFORE UPDATE ON manual_recommendations
BEGIN SELECT RAISE(ABORT, 'append-only table: manual_recommendations'); END;
CREATE TRIGGER trg_manual_recommendations_no_delete BEFORE DELETE ON manual_recommendations
BEGIN SELECT RAISE(ABORT, 'append-only table: manual_recommendations'); END;
