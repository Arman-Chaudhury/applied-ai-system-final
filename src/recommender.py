import csv
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

MAX_SCORE = 8.0

KNOWN_GENRES = {"pop", "lofi", "rock", "ambient", "jazz", "synthwave", "indie pop"}
KNOWN_MOODS = {"happy", "chill", "intense", "relaxed", "focused", "moody"}


class ProfileValidationError(ValueError):
    """Raised when a user profile fails the hard guardrails (bad types or out-of-range values)."""


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


@dataclass
class Recommendation:
    """A single ranked recommendation with its score, reasons, and per-item confidence."""
    song: Song
    score: float
    reasons: List[str]
    confidence: float


@dataclass
class RecommendationResult:
    """Full result of a recommend call: ranked items + a confidence summary for the whole list."""
    items: List[Recommendation]
    top_score: float
    margin: float
    overall_confidence: float
    warnings: List[str]


def validate_user_profile(prefs: Dict) -> List[str]:
    """
    Hard + soft guardrails for a user profile dict.

    Hard failures (raise ProfileValidationError):
      - missing required keys
      - target energy not numeric or outside [0, 1]
      - likes_acoustic not a bool

    Soft warnings (returned as a list):
      - genre not in KNOWN_GENRES (recommendation will fall back to non-genre signals)
      - mood not in KNOWN_MOODS
    """
    required = {"genre", "mood", "energy", "likes_acoustic"}
    missing = required - prefs.keys()
    if missing:
        raise ProfileValidationError(f"user profile missing required keys: {sorted(missing)}")

    energy = prefs["energy"]
    if not isinstance(energy, (int, float)) or isinstance(energy, bool):
        raise ProfileValidationError(f"energy must be a number in [0, 1], got {energy!r}")
    if not 0.0 <= float(energy) <= 1.0:
        raise ProfileValidationError(f"energy must be within [0, 1], got {energy}")

    if not isinstance(prefs["likes_acoustic"], bool):
        raise ProfileValidationError(
            f"likes_acoustic must be a bool, got {type(prefs['likes_acoustic']).__name__}"
        )

    warnings: List[str] = []
    if prefs["genre"] not in KNOWN_GENRES:
        warnings.append(
            f"genre {prefs['genre']!r} not in catalog vocabulary {sorted(KNOWN_GENRES)} — "
            "recommendations will rely on mood + energy only"
        )
    if prefs["mood"] not in KNOWN_MOODS:
        warnings.append(
            f"mood {prefs['mood']!r} not in catalog vocabulary {sorted(KNOWN_MOODS)} — "
            "no mood points will be awarded"
        )
    return warnings


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs ranked by score for the given user profile."""
        user_prefs = _profile_to_prefs(user)
        scored = []
        for song in self.songs:
            score, _ = score_song(user_prefs, _song_to_dict(song))
            scored.append((score, song))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [song for _, song in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended for the user."""
        user_prefs = _profile_to_prefs(user)
        _, reasons = score_song(user_prefs, _song_to_dict(song))
        if reasons:
            return "Recommended because: " + ", ".join(reasons)
        return f"This song has a similar energy level ({song.energy:.2f}) to your preference"

    def recommend_with_confidence(self, user: UserProfile, k: int = 5) -> RecommendationResult:
        """
        Run recommendation with input validation + confidence scoring.

        Confidence is computed two ways:
          - per-item: score / MAX_SCORE
          - overall: blends top score (weight 0.7) with the margin between #1 and #2
            (weight 0.3). A high top score with a clear margin yields high confidence.
        """
        user_prefs = _profile_to_prefs(user)
        warnings = validate_user_profile(user_prefs)
        for w in warnings:
            logger.warning("profile guardrail: %s", w)

        if k <= 0:
            raise ValueError(f"k must be positive, got {k}")
        if not self.songs:
            logger.error("recommend_with_confidence called with empty catalog")
            return RecommendationResult([], 0.0, 0.0, 0.0, warnings)

        scored: List[Tuple[float, List[str], Song]] = []
        for song in self.songs:
            score, reasons = score_song(user_prefs, _song_to_dict(song))
            scored.append((score, reasons, song))
        scored.sort(key=lambda x: x[0], reverse=True)

        top_k = scored[:k]
        items = [
            Recommendation(song=s, score=score, reasons=reasons, confidence=score / MAX_SCORE)
            for score, reasons, s in top_k
        ]

        top_score = scored[0][0] if scored else 0.0
        second_score = scored[1][0] if len(scored) > 1 else 0.0
        margin = top_score - second_score
        overall_confidence = 0.7 * (top_score / MAX_SCORE) + 0.3 * min(margin / MAX_SCORE, 1.0)

        logger.info(
            "recommended %d songs: top_score=%.2f margin=%.2f confidence=%.2f",
            len(items), top_score, margin, overall_confidence,
        )
        return RecommendationResult(
            items=items,
            top_score=top_score,
            margin=margin,
            overall_confidence=overall_confidence,
            warnings=warnings,
        )


def _profile_to_prefs(user: UserProfile) -> Dict:
    return {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "energy": user.target_energy,
        "likes_acoustic": user.likes_acoustic,
    }


def _song_to_dict(song: Song) -> Dict:
    return {
        "genre": song.genre,
        "mood": song.mood,
        "energy": song.energy,
        "acousticness": song.acousticness,
    }


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    try:
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                songs.append({
                    "id": int(row["id"]),
                    "title": row["title"],
                    "artist": row["artist"],
                    "genre": row["genre"],
                    "mood": row["mood"],
                    "energy": float(row["energy"]),
                    "tempo_bpm": float(row["tempo_bpm"]),
                    "valence": float(row["valence"]),
                    "danceability": float(row["danceability"]),
                    "acousticness": float(row["acousticness"]),
                })
    except FileNotFoundError:
        logger.error("song catalog not found at %s", csv_path)
        raise
    logger.info("loaded %d songs from %s", len(songs), csv_path)
    return songs


def load_songs_as_dataclass(csv_path: str) -> List[Song]:
    """Same as load_songs but returns Song dataclasses (used by the evaluator)."""
    return [Song(**row) for row in load_songs(csv_path)]


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.

    Scoring Rule (Algorithm Recipe):
      - Genre match:      +3.0 pts  (strongest signal — defines the broad taste category)
      - Mood match:       +2.0 pts  (second strongest — captures the user's emotional context)
      - Energy proximity: up to +2.0 pts  calculated as (1 - |song_energy - target_energy|) * 2
      - Acoustic bonus:   +1.0 pts  if user likes acoustic AND song acousticness > 0.6

    Genre is worth more than mood because two songs in the same genre share
    production style, instrumentation, and cultural context — even when the
    moods differ. Energy is continuous, so it contributes a sliding reward
    rather than a binary one.

    Required by recommend_songs() and src/main.py
    """
    score = 0.0
    reasons = []

    if song.get("genre") == user_prefs.get("genre"):
        score += 3.0
        reasons.append(f"genre matches ({song['genre']})")

    if song.get("mood") == user_prefs.get("mood"):
        score += 2.0
        reasons.append(f"mood matches ({song['mood']})")

    target_energy = user_prefs.get("energy", 0.5)
    energy_diff = abs(song.get("energy", 0.5) - target_energy)
    energy_score = (1.0 - energy_diff) * 2.0
    score += energy_score
    if energy_diff < 0.1:
        reasons.append(f"energy closely matches ({song['energy']:.2f})")

    if user_prefs.get("likes_acoustic", False) and song.get("acousticness", 0.0) > 0.6:
        score += 1.0
        reasons.append(f"acoustic vibe ({song['acousticness']:.2f})")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.

    Ranking Rule: score every song with score_song(), then return the top-k
    by descending score.  Ties are broken by the original catalog order.

    Required by src/main.py
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = ", ".join(reasons) if reasons else "general energy match"
        scored.append((song, score, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]
