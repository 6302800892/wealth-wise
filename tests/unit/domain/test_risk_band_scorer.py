"""AC-01: deterministic questionnaire scoring and risk-band assignment (BR-01 – BR-04)."""

import itertools

import pytest

from src.domain.risk_band_scorer import assess, band_for_score, score_answers
from src.types.enums import RiskBand
from src.types.errors import WealthWiseError
from tests.factories import answers_for_scores, rule_set_v1

RULES = rule_set_v1()


@pytest.mark.ac("AC-01")
def test_total_score_is_sum_of_option_scores():
    """AC-01.2: options scoring 3,3,3,3,2,2 total 16 and map to MODERATE."""
    result = assess(RULES, answers_for_scores(3, 3, 3, 3, 2, 2))
    assert result.total_score == 16
    assert result.risk_band is RiskBand.MODERATE


@pytest.mark.ac("AC-01")
@pytest.mark.parametrize(
    ("score", "band"),
    [(6, RiskBand.CONSERVATIVE), (13, RiskBand.CONSERVATIVE), (14, RiskBand.MODERATE),
     (22, RiskBand.MODERATE), (23, RiskBand.AGGRESSIVE), (30, RiskBand.AGGRESSIVE)],
)
def test_band_thresholds_at_boundaries(score, band):
    """AC-01.3: inclusive band boundaries 6-13 / 14-22 / 23-30."""
    assert band_for_score(RULES, score) is band


@pytest.mark.ac("AC-01")
def test_missing_question_is_rejected():
    """AC-01.4: a submission missing Q6 is rejected with INVALID_ANSWERS."""
    with pytest.raises(WealthWiseError) as exc:
        score_answers(RULES, answers_for_scores(3, 3, 3, 3, 2))
    assert exc.value.code == "INVALID_ANSWERS"
    assert "Q6" in exc.value.details["missing"]


@pytest.mark.ac("AC-01")
def test_duplicate_answer_is_rejected():
    """AC-01.4: answering Q1 twice is rejected."""
    answers = answers_for_scores(3, 3, 3, 3, 2, 2) + [("Q1", "Q1_A")]
    with pytest.raises(WealthWiseError) as exc:
        score_answers(RULES, answers)
    assert exc.value.code == "INVALID_ANSWERS"


@pytest.mark.ac("AC-01")
def test_option_from_another_question_is_rejected():
    """AC-01.4: Q1 answered with an option belonging to Q2 is rejected."""
    answers = answers_for_scores(3, 3, 3, 3, 2, 2)
    answers[0] = ("Q1", "Q2_A")
    with pytest.raises(WealthWiseError) as exc:
        score_answers(RULES, answers)
    assert exc.value.code == "INVALID_ANSWERS"


@pytest.mark.ac("AC-01")
def test_unknown_question_is_rejected():
    """AC-01.4: an answer for a question outside the rule set is rejected."""
    with pytest.raises(WealthWiseError):
        score_answers(RULES, answers_for_scores(3, 3, 3, 3, 2, 2) + [("Q9", "Q9_A")])


@pytest.mark.ac("AC-01")
def test_every_answer_combination_maps_to_exactly_one_band_deterministically():
    """AC-01.5: all 5^6 = 15,625 combinations map to exactly one band, identically on re-run."""
    seen_bands = set()
    for combo in itertools.product(range(1, 6), repeat=6):
        first = assess(RULES, answers_for_scores(*combo))
        second = assess(RULES, answers_for_scores(*combo))
        assert first == second
        assert first.total_score == sum(combo)
        seen_bands.add(first.risk_band)
    assert seen_bands == set(RiskBand)


def test_score_outside_any_band_is_an_error():
    with pytest.raises(WealthWiseError):
        band_for_score(RULES, 31)
