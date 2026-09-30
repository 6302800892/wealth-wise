# API evaluation — sprint-2

Checks passed: **8/8**

| ID | Description | Expected | Actual | ms | Result |
|---|---|---|---|---|---|
| api-201 | AC-05.1/05.2 portfolio E1 valued at 1,000,000.00 with max drift 10.00 | 200 | 200 | 46 | PASS |
| api-202 | AC-05.4 no holdings → total 0.00, no drift | 200 | 200 | 30 | PASS |
| api-203 | NFR-01 float units rejected | 422 | 422 | 5 | PASS |
| api-204 | AC-05 recorded holding is valued | 200 | 200 | 8 | PASS |
| api-205 | BR-25 day-0 NAV seeded; CASH fixed at 1.0000 | 200 | 200 | 20 | PASS |
| api-206 | BR-25 refresh ingests the next feed day | 200 | 200 | 32 | PASS |
| api-207 | AC-05 valuation follows the latest NAV | 200 | 200 | 5 | PASS |
| api-208 | NFR-04 customers cannot trigger NAV refresh | 403 | 403 | 5 | PASS |
