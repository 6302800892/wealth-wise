-- 0004: policy migration — risk questionnaire rule set v1 (spec §8.1, BR-01 – BR-03). APPEND-ONLY FILE (NFR-05).

INSERT INTO risk_rule_set_versions (version, status, definition_json, created_by, created_at, published_by, published_at)
VALUES (1, 'PUBLISHED', '{
  "questions": [
    {"id": "Q1", "text": "What is your age?", "options": [
      {"id": "Q1_A", "text": "60 or older", "score": 1}, {"id": "Q1_B", "text": "50 to 59", "score": 2},
      {"id": "Q1_C", "text": "40 to 49", "score": 3}, {"id": "Q1_D", "text": "30 to 39", "score": 4},
      {"id": "Q1_E", "text": "Under 30", "score": 5}]},
    {"id": "Q2", "text": "When will you need most of this money?", "options": [
      {"id": "Q2_A", "text": "Within 1 year", "score": 1}, {"id": "Q2_B", "text": "In 1 to 3 years", "score": 2},
      {"id": "Q2_C", "text": "In 3 to 5 years", "score": 3}, {"id": "Q2_D", "text": "In 5 to 10 years", "score": 4},
      {"id": "Q2_E", "text": "In more than 10 years", "score": 5}]},
    {"id": "Q3", "text": "How stable is your income?", "options": [
      {"id": "Q3_A", "text": "Very unstable", "score": 1}, {"id": "Q3_B", "text": "Unstable", "score": 2},
      {"id": "Q3_C", "text": "Moderately stable", "score": 3}, {"id": "Q3_D", "text": "Stable", "score": 4},
      {"id": "Q3_E", "text": "Very stable, with several sources", "score": 5}]},
    {"id": "Q4", "text": "Your portfolio falls 20% in a month. What do you do?", "options": [
      {"id": "Q4_A", "text": "Sell everything", "score": 1}, {"id": "Q4_B", "text": "Sell some", "score": 2},
      {"id": "Q4_C", "text": "Do nothing", "score": 3}, {"id": "Q4_D", "text": "Buy a little more", "score": 4},
      {"id": "Q4_E", "text": "Buy a lot more", "score": 5}]},
    {"id": "Q5", "text": "What is your investing experience?", "options": [
      {"id": "Q5_A", "text": "None", "score": 1}, {"id": "Q5_B", "text": "Savings and fixed deposits only", "score": 2},
      {"id": "Q5_C", "text": "Mutual funds", "score": 3}, {"id": "Q5_D", "text": "Stocks and mutual funds", "score": 4},
      {"id": "Q5_E", "text": "Advanced products", "score": 5}]},
    {"id": "Q6", "text": "What is your main investment objective?", "options": [
      {"id": "Q6_A", "text": "Protect my capital", "score": 1}, {"id": "Q6_B", "text": "Regular income", "score": 2},
      {"id": "Q6_C", "text": "Balanced income and growth", "score": 3}, {"id": "Q6_D", "text": "Growth", "score": 4},
      {"id": "Q6_E", "text": "Maximum growth", "score": 5}]}
  ],
  "bands": [
    {"band": "CONSERVATIVE", "min_score": 6, "max_score": 13},
    {"band": "MODERATE", "min_score": 14, "max_score": 22},
    {"band": "AGGRESSIVE", "min_score": 23, "max_score": 30}
  ]
}', NULL, '2026-09-30T00:00:00Z', NULL, '2026-09-30T00:00:00Z');
