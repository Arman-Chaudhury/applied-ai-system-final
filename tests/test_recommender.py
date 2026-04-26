import pytest

from src.recommender import (
    Recommender,
    Song,
    UserProfile,
    ProfileValidationError,
    validate_user_profile,
)


def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_recommend_with_confidence_returns_full_result():
    user = UserProfile("pop", "happy", 0.8, False)
    rec = make_small_recommender()
    result = rec.recommend_with_confidence(user, k=2)

    assert len(result.items) == 2
    assert result.items[0].song.genre == "pop"
    assert 0.0 <= result.overall_confidence <= 1.0
    assert result.top_score >= result.items[1].score
    assert result.margin == pytest.approx(result.items[0].score - result.items[1].score)


def test_recommend_with_confidence_flags_unknown_genre_as_warning():
    # k-pop is not in the known catalog vocabulary — should warn but not raise
    user = UserProfile("k-pop", "happy", 0.8, False)
    rec = make_small_recommender()
    result = rec.recommend_with_confidence(user, k=2)

    assert any("k-pop" in w for w in result.warnings)
    assert len(result.items) == 2  # still returns recommendations


def test_validate_user_profile_rejects_out_of_range_energy():
    with pytest.raises(ProfileValidationError):
        validate_user_profile(
            {"genre": "pop", "mood": "happy", "energy": 1.5, "likes_acoustic": False}
        )


def test_validate_user_profile_rejects_non_bool_likes_acoustic():
    with pytest.raises(ProfileValidationError):
        validate_user_profile(
            {"genre": "pop", "mood": "happy", "energy": 0.5, "likes_acoustic": "yes"}
        )


def test_validate_user_profile_rejects_missing_keys():
    with pytest.raises(ProfileValidationError):
        validate_user_profile({"genre": "pop", "mood": "happy"})


def test_recommend_with_confidence_rejects_zero_k():
    user = UserProfile("pop", "happy", 0.8, False)
    rec = make_small_recommender()
    with pytest.raises(ValueError):
        rec.recommend_with_confidence(user, k=0)
