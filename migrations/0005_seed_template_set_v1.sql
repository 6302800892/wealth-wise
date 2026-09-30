-- 0005: policy migration — allocation template set v1 (spec §8.4, BR-09). Percentages in basis points.
-- Inserted as DRAFT, then published, so the immutability triggers apply from here on. APPEND-ONLY FILE (NFR-05).

INSERT INTO allocation_template_set_versions (version, status, created_by, created_at, published_by, published_at)
VALUES (1, 'DRAFT', NULL, '2026-09-30T00:00:00Z', NULL, NULL);

INSERT INTO allocation_template_rows (template_version, risk_band, horizon_bucket, asset_class_code, target_bp) VALUES
    (1, 'CONSERVATIVE', 'SHORT', 'EQUITY', 1000), (1, 'CONSERVATIVE', 'SHORT', 'DEBT', 6000),
    (1, 'CONSERVATIVE', 'SHORT', 'GOLD', 1000), (1, 'CONSERVATIVE', 'SHORT', 'CASH', 2000),
    (1, 'CONSERVATIVE', 'MEDIUM', 'EQUITY', 2000), (1, 'CONSERVATIVE', 'MEDIUM', 'DEBT', 6000),
    (1, 'CONSERVATIVE', 'MEDIUM', 'GOLD', 1000), (1, 'CONSERVATIVE', 'MEDIUM', 'CASH', 1000),
    (1, 'CONSERVATIVE', 'LONG', 'EQUITY', 3000), (1, 'CONSERVATIVE', 'LONG', 'DEBT', 5500),
    (1, 'CONSERVATIVE', 'LONG', 'GOLD', 1000), (1, 'CONSERVATIVE', 'LONG', 'CASH', 500),
    (1, 'MODERATE', 'SHORT', 'EQUITY', 3000), (1, 'MODERATE', 'SHORT', 'DEBT', 5000),
    (1, 'MODERATE', 'SHORT', 'GOLD', 1000), (1, 'MODERATE', 'SHORT', 'CASH', 1000),
    (1, 'MODERATE', 'MEDIUM', 'EQUITY', 5000), (1, 'MODERATE', 'MEDIUM', 'DEBT', 3500),
    (1, 'MODERATE', 'MEDIUM', 'GOLD', 1000), (1, 'MODERATE', 'MEDIUM', 'CASH', 500),
    (1, 'MODERATE', 'LONG', 'EQUITY', 6000), (1, 'MODERATE', 'LONG', 'DEBT', 2700),
    (1, 'MODERATE', 'LONG', 'GOLD', 1000), (1, 'MODERATE', 'LONG', 'CASH', 300),
    (1, 'AGGRESSIVE', 'SHORT', 'EQUITY', 4500), (1, 'AGGRESSIVE', 'SHORT', 'DEBT', 4000),
    (1, 'AGGRESSIVE', 'SHORT', 'GOLD', 1000), (1, 'AGGRESSIVE', 'SHORT', 'CASH', 500),
    (1, 'AGGRESSIVE', 'MEDIUM', 'EQUITY', 7000), (1, 'AGGRESSIVE', 'MEDIUM', 'DEBT', 2000),
    (1, 'AGGRESSIVE', 'MEDIUM', 'GOLD', 700), (1, 'AGGRESSIVE', 'MEDIUM', 'CASH', 300),
    (1, 'AGGRESSIVE', 'LONG', 'EQUITY', 8000), (1, 'AGGRESSIVE', 'LONG', 'DEBT', 1200),
    (1, 'AGGRESSIVE', 'LONG', 'GOLD', 500), (1, 'AGGRESSIVE', 'LONG', 'CASH', 300);

UPDATE allocation_template_set_versions
SET status = 'PUBLISHED', published_at = '2026-09-30T00:00:00Z'
WHERE version = 1;
