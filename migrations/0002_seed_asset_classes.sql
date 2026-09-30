-- 0002: asset-class master seed (spec §14). APPEND-ONLY FILE (NFR-05).

INSERT INTO asset_classes (code, name, display_order, is_active, created_at, updated_at) VALUES
    ('EQUITY', 'Equity', 1, 1, '2026-09-30T00:00:00Z', '2026-09-30T00:00:00Z'),
    ('DEBT', 'Debt', 2, 1, '2026-09-30T00:00:00Z', '2026-09-30T00:00:00Z'),
    ('GOLD', 'Gold', 3, 1, '2026-09-30T00:00:00Z', '2026-09-30T00:00:00Z'),
    ('CASH', 'Cash', 4, 1, '2026-09-30T00:00:00Z', '2026-09-30T00:00:00Z');
