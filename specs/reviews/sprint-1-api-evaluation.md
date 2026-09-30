# API evaluation — sprint-1

Checks passed: **11/11**

| ID | Description | Expected | Actual | ms | Result |
|---|---|---|---|---|---|
| api-101 | AC-01.1 questionnaire exposes active rule set v1 | 200 | 200 | 20 | PASS |
| api-102 | AC-01.2 score 16 → MODERATE | 201 | 201 | 29 | PASS |
| api-103 | AC-01.4 incomplete answers rejected | 422 | 422 | 16 | PASS |
| api-104 | AC-01.6 customer sees assigned band | 200 | 200 | 15 | PASS |
| api-105 | AC-04.5 recommendation requires a goal | 409 | 409 | 19 | PASS |
| api-106 | AC-03.1 goal created with string amount | 201 | 201 | 6 | PASS |
| api-107 | AC-03.3 / NFR-01 JSON number amount rejected | 422 | 422 | 4 | PASS |
| api-108 | AC-04.1 / AC-02.4 MODERATE + LONG, sums to 100.00 | 201 | 201 | 8 | PASS |
| api-109 | AC-04.4 identical inputs return existing recommendation | 200 | 200 | 6 | PASS |
| api-110 | AC-04.5 KYC stub blocks recommendation | 403 | 403 | 5 | PASS |
| api-111 | Seeded customer alpha has MODERATE/MEDIUM recommendation | 200 | 200 | 28 | PASS |
