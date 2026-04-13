# 🎵 Music Recommender Simulation

## Project Summary

This project builds a small content-based music recommender that mirrors how real platforms like Spotify decide what to play next. Given a catalog of 10 songs (each described by genre, mood, energy, tempo, valence, danceability, and acousticness) and a user taste profile, the system scores every song and returns the top-k matches.

Real-world recommenders rely on two main strategies:
- **Collaborative filtering** — "users who liked what you liked also liked X" (needs many users and interaction data)
- **Content-based filtering** — "here are songs whose audio features match your stated preferences" (works from song attributes alone)

This simulation uses content-based filtering because we have rich song attributes but only one user.

---

## How The System Works

Real platforms like Spotify and YouTube process millions of users and hundreds of millions of songs. They connect user data (play history, skips, likes, playlists) to song data (audio features computed from the audio signal) using two main strategies: collaborative filtering identifies users with similar listening histories and recommends what those users liked next, while content-based filtering compares audio attributes of songs the user has played against the full catalog. At scale these are blended into a hybrid model. This simulation mirrors the content-based half: a `UserProfile` represents a listener's stated preferences, a `Song` stores its audio attributes, and a scoring function directly compares them to produce a ranked shortlist.

### Song features used

Each `Song` stores: `genre`, `mood`, `energy` (0–1), `tempo_bpm`, `valence` (musical positiveness, 0–1), `danceability` (0–1), and `acousticness` (0–1). The scoring rule currently uses `genre`, `mood`, `energy`, and `acousticness` — the features most directly tied to how a listener describes their taste in everyday language.

### UserProfile

A `UserProfile` stores:
- `favorite_genre` — the genre the user most often listens to
- `favorite_mood` — the emotional atmosphere the user wants right now
- `target_energy` — a 0–1 float representing how high-energy the user wants the music
- `likes_acoustic` — a boolean flag for users who prefer organic, instrument-driven sounds

### Scoring Rule (one song at a time)

| Signal | Points | Reasoning |
|---|---|---|
| Genre match | +3.0 | Genre captures production style and cultural context — the strongest taste signal |
| Mood match | +2.0 | Mood captures immediate emotional context — second strongest signal |
| Energy proximity | 0 – 2.0 | `(1 − |song_energy − target_energy|) × 2` — continuous reward, closer = higher |
| Acoustic bonus | +1.0 | Only awarded when `likes_acoustic=True` AND `acousticness > 0.6` |

Maximum possible score: **8.0**

### Ranking Rule (choosing what to recommend)

After scoring every song, the system sorts them by descending score and returns the top-k. This is a greedy ranking — the highest-scored song is always first. Ties fall back to catalog order.

A single score captures both binary matches (genre, mood) and a continuous proximity signal (energy), so the ranking naturally separates strong matches from partial ones.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

**Five user profiles tested** (see `src/main.py`, results captured in `model_card.md`):
1. Pop / happy / energy 0.8 — baseline, works well
2. Lofi / chill / energy 0.4 / acoustic — works best; data has 3 lofi songs
3. Rock / intense / energy 0.9 — works well; only one rock song but it dominates
4. Jazz / intense / energy 0.9 — adversarial: no intense jazz exists in catalog; two near-tied wrong answers
5. Ambient / relaxed / energy 0.9 / acoustic — edge case: genre bonus surfaces the lowest-energy song in the catalog

**Weight-shift experiment** (`src/main.py`, `score_song_experimental`): Doubled energy weight (0–4 pts) and halved genre weight (1.5 pts). For the pop/happy profile, Rooftop Lights jumped from #3 to #2 and Gym Hero dropped from #2 to #3. Gym Hero's genre match had compensated for its poor energy fit (0.93 vs target 0.80); with energy worth more, that compensation disappeared. Sunrise City stayed #1 regardless.

---

## Limitations and Risks

- **Genre dominance can actively mislead**: a genre match awards 3 points even when every other signal is wrong. In the ambient/high-energy edge case, the sole ambient song (energy 0.28) ranked first for a user who wanted energy 0.90.
- **Tiny catalog creates data bias**: lofi listeners get better results not because the algorithm is smarter for them, but because the catalog happens to have more matching lofi songs.
- **Independent additive scoring ignores interactions**: a genre match paired with a bad energy fit should arguably be worth less than a genre match where everything aligns, but the current model gives the same 3 genre points either way.
- **No representation for several major genres**: hip-hop, R&B, classical, K-pop, and country are all absent; users with these preferences get irrelevant genre-fallback recommendations.
- **Binary acoustic flag loses nuance**: a listener who enjoys both acoustic and electric sounds has no way to express that.

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

The biggest learning moment was seeing how a recommender doesn't "understand" music at all — it just compares numbers. Defining the scoring rule forced a concrete decision: how much is a genre match worth relative to an energy match? Assigning 3 points to genre and 2 to mood felt reasonable until the adversarial tests revealed the consequence: a genre hit with completely wrong energy still outscores a near-perfect energy match in the wrong genre. That gap between "the formula makes sense in isolation" and "the formula does the right thing on real inputs" only showed up by running it — which is exactly why evaluation with diverse profiles matters more than inspecting the code.

Bias in this system isn't subtle. Lofi listeners get three catalog entries to match against; jazz listeners get one. The algorithm is identical for both, but the lofi user gets better results purely because of how the dataset was assembled — not because the algorithm is smarter for them. That's the real lesson: data choices embed assumptions that compound through the scoring. A real platform with millions of songs would have the same structural issue at a larger scale: underrepresented genres produce worse recommendations, which leads to fewer plays, which produces less training signal, which keeps the recommendations worse. Fixing it requires intentional curation of the catalog, not just a better scoring function.


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

