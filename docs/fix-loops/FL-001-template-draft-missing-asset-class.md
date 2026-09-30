# FL-001 — New asset class made every template draft unpublishable

| Field | Value |
|---|---|
| Loop | Detect → Reproduce → Fix → Validate → MR |
| Branch / MR | `fix/FL-001-template-draft-new-asset-class` → MR !7 (`--no-ff`) |
| Rules touched | AC-02 (sum = 100 per row), AC-10 (versioned templates), BR-22 (publish validation) |
| Agents | evaluator (detected), generator (fixed), test-engineer (regression test) |
| Date | 2026-09-30 |

## 1. Detect
The evaluator was reviewing the admin template editor for Sprint 5. `TemplatesPage.jsx` builds its columns from `Object.keys(rows[0].allocations)`, the asset classes present in the draft. BR-22, meanwhile, requires every **active** asset class to appear in every row before publishing. The two rules conflict: an asset class added after the active version was published could never be supplied through the UI.

## 2. Reproduce (failing test first)
`tests/integration/api/test_admin_versioning_api.py::test_new_asset_class_appears_in_next_draft_so_it_can_be_published`

Steps:
1. The admin creates asset class `REIT`.
2. The admin creates template draft v2, cloned from v1.
3. The admin publishes it.

Observed before the fix (captured from a live app instance):
```
422 ALLOCATION_SUM_INVALID CONSERVATIVE/SHORT: must list exactly ['CASH', 'DEBT', 'EQUITY', 'GOLD', 'REIT']; CONSERVATIVE/MEDIUM: …
```
All 9 rows failed. Committed red as `test(FL-001): reproduce unpublishable draft after adding an asset class (red)`.

## 3. Root cause
`policy_admin_service.create_template_draft` copied the active version's rows verbatim, so asset classes missing from the active version stayed missing from the draft. The invariant check (`check_publishable`) was correct. The draft was simply created in a state that no edit in the UI could fix.

## 4. Fix
`_with_active_classes()` adds every active asset class missing from a row, at `0.00`, when a draft is created. The draft still sums to 100.00 per row, because adding zeros changes nothing. The admin can now see REIT and re-allocate it in the editor. Published versions are untouched (immutability triggers). In-flight customers keep their recommendation's version (AC-10.3).

## 5. Validate
- The regression test passes.
- Full suite: **296 passed** (was 295 + 1 new).
- Architecture tests are unchanged and green: allocation-sum invariant and published immutability.

## 6. Knowledge deposit
Recorded as **KD-07**: *"Drafts must be created publishable-in-principle: every active asset class present."* This was encoded in two places:
- The `policy-version-validator` skill checklist.
- The `allocation-sum-invariant-check` hook message, which reminds authors that seeded template rows must cover every active asset class.
