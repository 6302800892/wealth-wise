-- 0003: versioned risk rule sets and allocation template sets (BR-21 – BR-23).
-- Published versions are immutable: triggers abort UPDATE/DELETE, and row inserts into published sets.
-- APPEND-ONLY FILE (NFR-05).

CREATE TABLE risk_rule_set_versions (
    version INTEGER PRIMARY KEY CHECK (version >= 1),
    status TEXT NOT NULL CHECK (status IN ('DRAFT', 'PUBLISHED')),
    definition_json TEXT NOT NULL,
    created_by TEXT REFERENCES users (id),
    created_at TEXT NOT NULL,
    published_by TEXT REFERENCES users (id),
    published_at TEXT,
    CHECK ((status = 'PUBLISHED') = (published_at IS NOT NULL))
);
CREATE UNIQUE INDEX uq_risk_rule_set_single_draft ON risk_rule_set_versions (status) WHERE status = 'DRAFT';

CREATE TRIGGER trg_rule_set_published_no_update BEFORE UPDATE ON risk_rule_set_versions
WHEN OLD.status = 'PUBLISHED'
BEGIN SELECT RAISE(ABORT, 'immutable: published risk rule set version'); END;
CREATE TRIGGER trg_rule_set_published_no_delete BEFORE DELETE ON risk_rule_set_versions
WHEN OLD.status = 'PUBLISHED'
BEGIN SELECT RAISE(ABORT, 'immutable: published risk rule set version'); END;

CREATE TABLE allocation_template_set_versions (
    version INTEGER PRIMARY KEY CHECK (version >= 1),
    status TEXT NOT NULL CHECK (status IN ('DRAFT', 'PUBLISHED')),
    created_by TEXT REFERENCES users (id),
    created_at TEXT NOT NULL,
    published_by TEXT REFERENCES users (id),
    published_at TEXT,
    CHECK ((status = 'PUBLISHED') = (published_at IS NOT NULL))
);
CREATE UNIQUE INDEX uq_template_set_single_draft ON allocation_template_set_versions (status) WHERE status = 'DRAFT';

CREATE TRIGGER trg_template_set_published_no_update BEFORE UPDATE ON allocation_template_set_versions
WHEN OLD.status = 'PUBLISHED'
BEGIN SELECT RAISE(ABORT, 'immutable: published allocation template version'); END;
CREATE TRIGGER trg_template_set_published_no_delete BEFORE DELETE ON allocation_template_set_versions
WHEN OLD.status = 'PUBLISHED'
BEGIN SELECT RAISE(ABORT, 'immutable: published allocation template version'); END;

CREATE TABLE allocation_template_rows (
    template_version INTEGER NOT NULL REFERENCES allocation_template_set_versions (version),
    risk_band TEXT NOT NULL CHECK (risk_band IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE')),
    horizon_bucket TEXT NOT NULL CHECK (horizon_bucket IN ('SHORT', 'MEDIUM', 'LONG')),
    asset_class_code TEXT NOT NULL REFERENCES asset_classes (code),
    target_bp INTEGER NOT NULL CHECK (target_bp BETWEEN 0 AND 10000),
    PRIMARY KEY (template_version, risk_band, horizon_bucket, asset_class_code)
);

CREATE TRIGGER trg_template_rows_published_no_insert BEFORE INSERT ON allocation_template_rows
WHEN (SELECT status FROM allocation_template_set_versions WHERE version = NEW.template_version) = 'PUBLISHED'
BEGIN SELECT RAISE(ABORT, 'immutable: rows of a published allocation template'); END;
CREATE TRIGGER trg_template_rows_published_no_update BEFORE UPDATE ON allocation_template_rows
WHEN (SELECT status FROM allocation_template_set_versions WHERE version = OLD.template_version) = 'PUBLISHED'
BEGIN SELECT RAISE(ABORT, 'immutable: rows of a published allocation template'); END;
CREATE TRIGGER trg_template_rows_published_no_delete BEFORE DELETE ON allocation_template_rows
WHEN (SELECT status FROM allocation_template_set_versions WHERE version = OLD.template_version) = 'PUBLISHED'
BEGIN SELECT RAISE(ABORT, 'immutable: rows of a published allocation template'); END;
