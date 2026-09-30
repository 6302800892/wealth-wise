-- 0001: users, sessions, customers, asset classes and the audit log.
-- APPEND-ONLY FILE: never edit after it has been applied (NFR-05). Add a new migration instead.

CREATE TABLE customers (
    id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    date_of_birth TEXT NOT NULL,
    kyc_verified INTEGER NOT NULL CHECK (kyc_verified IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('CUSTOMER', 'ADVISOR', 'ADMIN')),
    customer_id TEXT REFERENCES customers (id),
    display_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK ((role = 'CUSTOMER' AND customer_id IS NOT NULL) OR (role <> 'CUSTOMER' AND customer_id IS NULL))
);

CREATE TABLE sessions (
    token_hash TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users (id),
    expires_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE asset_classes (
    code TEXT PRIMARY KEY CHECK (code GLOB '[A-Z]*'),
    name TEXT NOT NULL,
    display_order INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    actor_user_id TEXT REFERENCES users (id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    correlation_id TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX idx_audit_log_entity ON audit_log (entity_type, entity_id);

CREATE TRIGGER trg_audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'append-only table: audit_log'); END;
CREATE TRIGGER trg_audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'append-only table: audit_log'); END;
