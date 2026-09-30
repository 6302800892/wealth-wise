-- 0006: risk assessments, advisor overrides and band assignments — all append-only (NFR-02, BR-05 – BR-07).
-- APPEND-ONLY FILE (NFR-05).

CREATE TABLE risk_assessments (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (id),
    rule_set_version INTEGER NOT NULL REFERENCES risk_rule_set_versions (version),
    answers_json TEXT NOT NULL,
    total_score INTEGER NOT NULL,
    computed_band TEXT NOT NULL CHECK (computed_band IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE')),
    created_at TEXT NOT NULL
);

CREATE TABLE risk_band_overrides (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (id),
    previous_band TEXT CHECK (previous_band IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE')),
    new_band TEXT NOT NULL CHECK (new_band IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE')),
    reason_code TEXT NOT NULL CHECK (reason_code IN
        ('CHANGE_IN_CIRCUMSTANCES', 'QUESTIONNAIRE_MISUNDERSTOOD', 'ADVISOR_ASSESSMENT', 'CUSTOMER_REQUEST')),
    note TEXT NOT NULL CHECK (length(trim(note)) BETWEEN 1 AND 1000),
    actor_user_id TEXT NOT NULL REFERENCES users (id),
    created_at TEXT NOT NULL
);

-- BR-07 / NFR-08: an ADVISOR_OVERRIDE assignment must reference its override audit record.
CREATE TABLE risk_band_assignments (
    id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers (id),
    risk_band TEXT NOT NULL CHECK (risk_band IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE')),
    source TEXT NOT NULL CHECK (source IN ('QUESTIONNAIRE', 'ADVISOR_OVERRIDE')),
    assessment_id TEXT REFERENCES risk_assessments (id),
    override_id TEXT REFERENCES risk_band_overrides (id),
    rule_set_version INTEGER REFERENCES risk_rule_set_versions (version),
    assigned_by TEXT NOT NULL REFERENCES users (id),
    assigned_at TEXT NOT NULL,
    CHECK (
        (source = 'QUESTIONNAIRE' AND assessment_id IS NOT NULL AND override_id IS NULL)
        OR (source = 'ADVISOR_OVERRIDE' AND override_id IS NOT NULL AND assessment_id IS NULL)
    )
);
CREATE INDEX idx_risk_band_assignments_customer ON risk_band_assignments (customer_id, assigned_at);

CREATE TRIGGER trg_risk_assessments_no_update BEFORE UPDATE ON risk_assessments
BEGIN SELECT RAISE(ABORT, 'append-only table: risk_assessments'); END;
CREATE TRIGGER trg_risk_assessments_no_delete BEFORE DELETE ON risk_assessments
BEGIN SELECT RAISE(ABORT, 'append-only table: risk_assessments'); END;
CREATE TRIGGER trg_risk_band_overrides_no_update BEFORE UPDATE ON risk_band_overrides
BEGIN SELECT RAISE(ABORT, 'append-only table: risk_band_overrides'); END;
CREATE TRIGGER trg_risk_band_overrides_no_delete BEFORE DELETE ON risk_band_overrides
BEGIN SELECT RAISE(ABORT, 'append-only table: risk_band_overrides'); END;
CREATE TRIGGER trg_risk_band_assignments_no_update BEFORE UPDATE ON risk_band_assignments
BEGIN SELECT RAISE(ABORT, 'append-only table: risk_band_assignments'); END;
CREATE TRIGGER trg_risk_band_assignments_no_delete BEFORE DELETE ON risk_band_assignments
BEGIN SELECT RAISE(ABORT, 'append-only table: risk_band_assignments'); END;
