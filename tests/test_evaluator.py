from src.evaluator import (
    EvalCase,
    default_eval_suite,
    evaluate_case,
    format_report,
    run_eval,
)
from src.recommender import Recommender, UserProfile, load_songs_as_dataclass


def _real_recommender() -> Recommender:
    return Recommender(load_songs_as_dataclass("data/songs.csv"))


def test_default_eval_suite_all_pass_against_real_catalog():
    report = run_eval()
    failed_names = [o.case.name for o in report.outcomes if not o.passed]
    assert report.failed == 0, f"failing cases: {failed_names}"


def test_strong_match_case_has_high_confidence():
    rec = _real_recommender()
    case = EvalCase(
        name="pop / happy / 0.8",
        profile=UserProfile("pop", "happy", 0.8, False),
        top_song_id=1,
    )
    outcome = evaluate_case(rec, case)
    assert outcome.passed
    assert outcome.result.overall_confidence > 0.6


def test_adversarial_case_has_low_confidence():
    rec = _real_recommender()
    case = EvalCase(
        name="jazz / intense / 0.9 — adversarial",
        profile=UserProfile("jazz", "intense", 0.9, False),
        confidence_below=0.55,
    )
    outcome = evaluate_case(rec, case)
    assert outcome.passed, f"unexpectedly high confidence: {outcome.failure_reasons}"


def test_format_report_includes_summary_line():
    report = run_eval()
    text = format_report(report)
    assert "EVALUATION REPORT" in text
    assert "SUMMARY" in text
    assert f"{report.passed}/{report.total}" in text


def test_default_suite_covers_happy_and_adversarial_paths():
    suite = default_eval_suite()
    assert any(c.top_song_id is not None for c in suite), "missing happy-path assertions"
    assert any(c.confidence_below is not None for c in suite), "missing adversarial assertions"
