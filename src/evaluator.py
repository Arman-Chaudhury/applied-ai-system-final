"""
Evaluation harness for the Music Recommender.

Runs the recommender against a fixed set of expected outcomes (the "evaluation
suite") and reports a pass/fail summary along with confidence statistics. This
is the AI-feature backbone of the project: it converts a hand-rolled scoring
rule into something whose reliability we can measure and report on.

Two kinds of expectations are supported per case:
  - top_song_id:        the song id we expect at rank 1
  - confidence_below:   for adversarial inputs we expect the system to *know*
                        it is unsure, so overall_confidence must stay below
                        this threshold
"""

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from src.recommender import (
    Recommender,
    UserProfile,
    RecommendationResult,
    load_songs_as_dataclass,
)

logger = logging.getLogger(__name__)


@dataclass
class EvalCase:
    name: str
    profile: UserProfile
    top_song_id: Optional[int] = None
    confidence_below: Optional[float] = None
    confidence_above: Optional[float] = None
    notes: str = ""


@dataclass
class EvalOutcome:
    case: EvalCase
    result: RecommendationResult
    passed: bool
    failure_reasons: List[str] = field(default_factory=list)


@dataclass
class EvalReport:
    outcomes: List[EvalOutcome]

    @property
    def total(self) -> int:
        return len(self.outcomes)

    @property
    def passed(self) -> int:
        return sum(1 for o in self.outcomes if o.passed)

    @property
    def failed(self) -> int:
        return self.total - self.passed

    @property
    def average_confidence(self) -> float:
        if not self.outcomes:
            return 0.0
        return sum(o.result.overall_confidence for o in self.outcomes) / self.total


def default_eval_suite() -> List[EvalCase]:
    """
    The standing evaluation suite. Three "happy path" cases assert the top
    recommendation; two adversarial cases assert that the system reports low
    confidence rather than pretending to know.
    """
    return [
        EvalCase(
            name="pop / happy / 0.8 — strong match",
            profile=UserProfile("pop", "happy", 0.8, False),
            top_song_id=1,
            confidence_above=0.6,
            notes="Sunrise City should win on all three signals.",
        ),
        EvalCase(
            name="lofi / chill / 0.4 / acoustic — strong match",
            profile=UserProfile("lofi", "chill", 0.4, True),
            top_song_id=2,
            confidence_above=0.65,
            notes=(
                "Midnight Coding wins narrowly over Library Rain on energy "
                "proximity — small margin pulls overall confidence down despite high top score."
            ),
        ),
        EvalCase(
            name="rock / intense / 0.9 — strong match",
            profile=UserProfile("rock", "intense", 0.9, False),
            top_song_id=3,
            confidence_above=0.6,
            notes="Storm Runner is the only rock song and aligns on mood + energy.",
        ),
        EvalCase(
            name="jazz / intense / 0.9 — adversarial (no intense jazz exists)",
            profile=UserProfile("jazz", "intense", 0.9, False),
            confidence_below=0.55,
            notes="System should report low confidence — top two contenders nearly tie.",
        ),
        EvalCase(
            name="ambient / relaxed / 0.9 / acoustic — adversarial energy clash",
            profile=UserProfile("ambient", "relaxed", 0.9, True),
            confidence_below=0.65,
            notes="Only ambient song is very low energy; confidence must reflect the mismatch.",
        ),
    ]


def evaluate_case(recommender: Recommender, case: EvalCase, k: int = 5) -> EvalOutcome:
    """Run a single evaluation case and decide pass/fail."""
    result = recommender.recommend_with_confidence(case.profile, k=k)
    failures: List[str] = []

    if case.top_song_id is not None:
        if not result.items:
            failures.append("no recommendations returned")
        elif result.items[0].song.id != case.top_song_id:
            failures.append(
                f"expected top song id={case.top_song_id}, "
                f"got id={result.items[0].song.id} ({result.items[0].song.title})"
            )

    if case.confidence_above is not None and result.overall_confidence < case.confidence_above:
        failures.append(
            f"confidence {result.overall_confidence:.2f} below required floor "
            f"{case.confidence_above:.2f}"
        )

    if case.confidence_below is not None and result.overall_confidence > case.confidence_below:
        failures.append(
            f"confidence {result.overall_confidence:.2f} above required ceiling "
            f"{case.confidence_below:.2f} — system is overconfident on an adversarial input"
        )

    return EvalOutcome(case=case, result=result, passed=not failures, failure_reasons=failures)


def run_eval(
    songs_csv: str = "data/songs.csv",
    cases: Optional[List[EvalCase]] = None,
    k: int = 5,
) -> EvalReport:
    """Load the catalog, build a Recommender, and run every case in the suite."""
    songs = load_songs_as_dataclass(songs_csv)
    recommender = Recommender(songs)
    cases = cases if cases is not None else default_eval_suite()
    outcomes = [evaluate_case(recommender, case, k=k) for case in cases]
    report = EvalReport(outcomes=outcomes)
    logger.info(
        "evaluation done: %d/%d passed, avg confidence %.2f",
        report.passed, report.total, report.average_confidence,
    )
    return report


def format_report(report: EvalReport) -> str:
    """Render a human-readable summary of an EvalReport."""
    lines = []
    lines.append("=" * 64)
    lines.append("  EVALUATION REPORT")
    lines.append("=" * 64)
    for i, outcome in enumerate(report.outcomes, start=1):
        status = "PASS" if outcome.passed else "FAIL"
        top = outcome.result.items[0] if outcome.result.items else None
        top_str = f"{top.song.title} (id={top.song.id}, score={top.score:.2f})" if top else "—"
        lines.append(f"\n[{i}] {status}  {outcome.case.name}")
        lines.append(f"     top:        {top_str}")
        lines.append(
            f"     confidence: {outcome.result.overall_confidence:.2f}  "
            f"(top_score={outcome.result.top_score:.2f}, margin={outcome.result.margin:.2f})"
        )
        if outcome.case.notes:
            lines.append(f"     note:       {outcome.case.notes}")
        for w in outcome.result.warnings:
            lines.append(f"     warning:    {w}")
        for f in outcome.failure_reasons:
            lines.append(f"     failure:    {f}")
    lines.append("\n" + "=" * 64)
    lines.append(
        f"  SUMMARY: {report.passed}/{report.total} passed   "
        f"avg confidence: {report.average_confidence:.2f}"
    )
    lines.append("=" * 64)
    return "\n".join(lines)
