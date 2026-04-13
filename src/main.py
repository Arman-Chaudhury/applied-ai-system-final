"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from src.recommender import load_songs, recommend_songs


# ---------------------------------------------------------------------------
# Experimental scoring: energy weight doubled (4.0), genre weight halved (1.5)
# ---------------------------------------------------------------------------

def score_song_experimental(user_prefs, song):
    """
    Variant of score_song with modified weights for the weight-shift experiment.
      - Genre match:      +1.5 pts  (halved from 3.0)
      - Mood match:       +2.0 pts  (unchanged)
      - Energy proximity: up to +4.0 pts  (doubled: (1 - |diff|) * 4)
      - Acoustic bonus:   +1.0 pts  (unchanged)
    Max possible: 8.5 pts
    """
    score = 0.0
    reasons = []

    if song.get("genre") == user_prefs.get("genre"):
        score += 1.5
        reasons.append(f"genre matches ({song['genre']})")

    if song.get("mood") == user_prefs.get("mood"):
        score += 2.0
        reasons.append(f"mood matches ({song['mood']})")

    target_energy = user_prefs.get("energy", 0.5)
    energy_diff = abs(song.get("energy", 0.5) - target_energy)
    energy_score = (1.0 - energy_diff) * 4.0
    score += energy_score
    if energy_diff < 0.1:
        reasons.append(f"energy closely matches ({song['energy']:.2f})")

    if user_prefs.get("likes_acoustic", False) and song.get("acousticness", 0.0) > 0.6:
        score += 1.0
        reasons.append(f"acoustic vibe ({song['acousticness']:.2f})")

    return score, reasons


def recommend_experimental(user_prefs, songs, k=5):
    scored = []
    for song in songs:
        score, reasons = score_song_experimental(user_prefs, song)
        explanation = ", ".join(reasons) if reasons else "general energy match"
        scored.append((song, score, explanation))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_profile(user_prefs, label="User Profile"):
    print("\n" + "=" * 50)
    print(f"  {label}")
    print("=" * 50)
    print(f"  Genre:    {user_prefs['genre']}")
    print(f"  Mood:     {user_prefs['mood']}")
    print(f"  Energy:   {user_prefs['energy']}")
    print(f"  Acoustic: {user_prefs['likes_acoustic']}")
    print("=" * 50)


def print_recommendations(recommendations, max_score=8.0):
    print(f"\n  Top {len(recommendations)} Recommendations\n")
    for i, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"  {i}. {song['title']} by {song['artist']}")
        print(f"     Score:   {score:.2f} / {max_score:.2f}")
        print(f"     Reasons: {explanation}")
        print()
    print("=" * 50)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # ------------------------------------------------------------------
    # Profile 1: High-Energy Pop (default "happy pop" listener)
    # ------------------------------------------------------------------
    profile_pop = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}
    print_profile(profile_pop, "Profile 1 — High-Energy Pop")
    print_recommendations(recommend_songs(profile_pop, songs, k=5))

    # ------------------------------------------------------------------
    # Profile 2: Chill Lofi Acoustic (study/focus listener)
    # ------------------------------------------------------------------
    profile_lofi = {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True}
    print_profile(profile_lofi, "Profile 2 — Chill Lofi Acoustic")
    print_recommendations(recommend_songs(profile_lofi, songs, k=5))

    # ------------------------------------------------------------------
    # Profile 3: Deep Intense Rock (workout listener)
    # ------------------------------------------------------------------
    profile_rock = {"genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False}
    print_profile(profile_rock, "Profile 3 — Deep Intense Rock")
    print_recommendations(recommend_songs(profile_rock, songs, k=5))

    # ------------------------------------------------------------------
    # Profile 4 (edge case): Jazz fan who wants high-energy intense music
    # Adversarial — the catalog has no intense jazz songs
    # ------------------------------------------------------------------
    profile_jazz_intense = {"genre": "jazz", "mood": "intense", "energy": 0.9, "likes_acoustic": False}
    print_profile(profile_jazz_intense, "Profile 4 — Adversarial: Jazz + Intense + High Energy")
    print_recommendations(recommend_songs(profile_jazz_intense, songs, k=5))

    # ------------------------------------------------------------------
    # Profile 5 (edge case): Conflicting energy — ambient lover who wants
    # high energy (e.g., 0.9), but ambient songs are all very low energy
    # ------------------------------------------------------------------
    profile_ambient_high = {"genre": "ambient", "mood": "relaxed", "energy": 0.9, "likes_acoustic": True}
    print_profile(profile_ambient_high, "Profile 5 — Edge Case: Ambient + High Energy")
    print_recommendations(recommend_songs(profile_ambient_high, songs, k=5))

    # ------------------------------------------------------------------
    # Experiment: Weight Shift — double energy importance, halve genre
    # Compare Profile 1 (pop/happy) under standard vs experimental weights
    # ------------------------------------------------------------------
    print("\n" + "#" * 50)
    print("  EXPERIMENT: Weight Shift")
    print("  Standard:     genre=3.0, energy up to 2.0")
    print("  Experimental: genre=1.5, energy up to 4.0")
    print("#" * 50)

    print("\n--- Standard weights (pop/happy, energy 0.8) ---")
    print_recommendations(recommend_songs(profile_pop, songs, k=5))

    print("\n--- Experimental weights (pop/happy, energy 0.8) ---")
    print_recommendations(recommend_experimental(profile_pop, songs, k=5), max_score=8.5)


if __name__ == "__main__":
    main()
