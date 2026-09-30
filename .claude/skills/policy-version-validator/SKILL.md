---
name: policy-version-validator
description: Checklist for creating, editing and publishing versioned allocation templates and rule sets, and for writing policy migrations (AC-02, AC-10, BR-21 – BR-23, NFR-05). Load before any change to migrations/ or policy_admin_service.py.
---

# Policy Version Validator Skill

## Lifecycle
```
active vN (PUBLISHED, immutable) ──clone──► vN+1 DRAFT ──PUT edits──► validate ──publish──► vN+1 PUBLISHED (active)
```
- At most **one DRAFT** per policy type. A partial unique index enforces it (`409 DRAFT_ALREADY_EXISTS`).
- A draft is cloned from the active version **plus every active asset class at 0.00** (FL-001 / KD-07).
- Saving a draft checks ranges only: 0.00–100.00, at most 2 dp, strings. Publishing checks everything else.

## Publish checklist (templates)
- [ ] All 9 rows are present: CONSERVATIVE, MODERATE, AGGRESSIVE × SHORT, MEDIUM, LONG.
- [ ] Each row lists **exactly** the active asset classes.
- [ ] Each row sums to **exactly 100.00** (10 000 bp). 99.99 and 100.01 are both rejected with `ALLOCATION_SUM_INVALID`.
- [ ] The spec table in `specs/app_spec.md` §8.4 is updated if the change is a seeded policy.

## Publish checklist (rule sets)
- [ ] At least 6 questions, unique question ids, and at least 2 options per question with unique ids.
- [ ] Bands are contiguous and non-overlapping, cover [min, max] score, and each band appears once.

## Migrations (NFR-05)
- Never edit or delete an applied file. The runner refuses to start on a checksum mismatch, and the `migration-append-only-check` hook blocks the edit.
- Seed a template as `DRAFT` → insert rows → `UPDATE … SET status = 'PUBLISHED'`. Inserting rows into an already published version is aborted by trigger.
- File names follow `NNNN_snake_case.sql`, with a strictly increasing number.

## Verify
```
pytest tests/architecture/test_allocation_sum_invariant.py tests/architecture/test_published_immutable.py \
       tests/integration/api/test_admin_versioning_api.py -q
```
