# API evaluation — sprint-4

Checks passed: **9/9**

| ID | Description | Expected | Actual | ms | Result |
|---|---|---|---|---|---|
| api-401 | Advisor lists customers | 200 | 200 | 53 | PASS |
| api-402 | NFR-04 customers cannot use the advisor workbench | 403 | 403 | 5 | PASS |
| api-403 | AC-10 v1 active | 200 | 200 | 25 | PASS |
| api-404 | AC-10 draft v2 cloned from active | 201 | 201 | 9 | PASS |
| api-405 | BR-21 only one draft at a time | 409 | 409 | 25 | PASS |
| api-406 | AC-10.2 published v1 is immutable | 409 | 409 | 16 | PASS |
| api-407 | AC-10.1 publish v2 | 200 | 200 | 26 | PASS |
| api-408 | AC-10.3 in-flight customer stays on v1 | 200 | 200 | 8 | PASS |
| api-409 | Asset class in the active template cannot be deactivated | 409 | 409 | 26 | PASS |
