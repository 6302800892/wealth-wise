---
name: new-template-version
description: Guided creation of a new allocation-template version (draft → edit → validate → publish) without breaking immutability or in-flight customers.
argument-hint: "<short description of the allocation change>"
---

# /new-template-version — $ARGUMENTS

1. Load the `policy-version-validator` skill.
2. **Spec first.** Propose the new 3×3 table for `specs/app_spec.md` §8.4. Show the user every row with its sum, and wait for approval. Rows must total exactly 100.00.
3. **Choose the delivery path:**
   - *Runtime change* (admin operation): `POST /api/v1/admin/allocation-templates` → `PUT …/{version}` with the approved rows → `POST …/{version}/publish`.
   - *Seeded policy* (ships with the code): add `migrations/NNNN_seed_template_set_vN.sql` that inserts the version as `DRAFT`, inserts the rows, then publishes. **Never** edit an existing migration.
4. **Tests, red first.** Add a test that publishing the new version succeeds and that a customer recommended under the previous version keeps those targets until they request a new recommendation (AC-10.3 pattern in `tests/integration/api/test_admin_versioning_api.py`).
5. **Validate.** Run the `policy-version-validator-agent`. Its verdict must be PASS before the MR.
6. **Record.** Add a changelog row to `specs/app_spec.md` and a note in the sprint review.
