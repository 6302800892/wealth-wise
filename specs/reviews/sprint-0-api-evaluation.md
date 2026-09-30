# API evaluation — sprint-0

Checks passed: **5/5**

| ID | Description | Expected | Actual | ms | Result |
|---|---|---|---|---|---|
| api-001 | NFR-07 health returns 200 within 1 s | 200 | 200 | 25 | PASS |
| api-002 | NFR-04 seeded customer can log in | 200 | 200 | 77 | PASS |
| api-003 | NFR-04 wrong password rejected | 401 | 401 | 72 | PASS |
| api-004 | NFR-04 protected route requires a token | 401 | 401 | 11 | PASS |
| api-005 | NFR-04 token identifies the advisor role | 200 | 200 | 3 | PASS |
