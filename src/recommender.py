import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

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

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs ranked by score for the given user profile."""
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        scored = []
        for song in self.songs:
            song_dict = {
                "genre": song.genre,
                "mood": song.mood,
                "energy": song.energy,
                "acousticness": song.acousticness,
            }
            score, _ = score_song(user_prefs, song_dict)
            scored.append((score, song))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [song for _, song in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song was recommended for the user."""
        user_prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        song_dict = {
            "genre": song.genre,
            "mood": song.mood,
            "energy": song.energy,
            "acousticness": song.acousticness,
        }
        _, reasons = score_song(user_prefs, song_dict)
        if reasons:
            return "Recommended because: " + ", ".join(reasons)
        return f"This song has a similar energy level ({song.energy:.2f}) to your preference"


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
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
    return songs


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

    # Genre match: +3 points
    if song.get("genre") == user_prefs.get("genre"):
        score += 3.0
        reasons.append(f"genre matches ({song['genre']})")

    # Mood match: +2 points
    if song.get("mood") == user_prefs.get("mood"):
        score += 2.0
        reasons.append(f"mood matches ({song['mood']})")

    # Energy proximity: sliding 0–2 points
    target_energy = user_prefs.get("energy", 0.5)
    energy_diff = abs(song.get("energy", 0.5) - target_energy)
    energy_score = (1.0 - energy_diff) * 2.0
    score += energy_score
    if energy_diff < 0.1:
        reasons.append(f"energy closely matches ({song['energy']:.2f})")

    # Acoustic bonus: +1 point
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
