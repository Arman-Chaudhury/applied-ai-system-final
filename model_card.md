# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

VibeFinder suggests up to 5 songs from a small 10-song catalog that best match a listener's current taste. It is built for classroom exploration only — not for real users. The system assumes the user can describe their mood, preferred genre, and energy level in advance, and that those preferences apply uniformly to every song being scored.

---

## 3. How the Model Works

Every song in the catalog is described by a handful of audio traits — most importantly its genre (like pop or lofi), its mood (happy, chill, intense…), how energetic it feels on a scale from 0 to 1, and how acoustic it sounds. A listener profile captures the same four signals from the user's side: preferred genre, preferred mood, a target energy level, and whether they like acoustic sounds.

To rank songs, the model gives each one a score:
- It adds 3 points if the genre matches — the strongest signal because genre ties together production style and cultural context.
- It adds 2 points if the mood matches — capturing the emotional atmosphere the listener wants right now.
- It awards up to 2 more points based on how close the song's energy is to the user's target — a sliding reward so songs that are "almost there" still get partial credit.
- It adds 1 bonus point if the user likes acoustic music and the song is highly acoustic.

The maximum possible score is 8 points. After scoring all songs, the system returns the top 5 in order from highest to lowest score.

---

## 4. Data

The catalog contains 10 songs stored in `data/songs.csv`. Each song has: id, title, artist, genre, mood, energy (0–1), tempo_bpm, valence (musical positiveness, 0–1), danceability (0–1), and acousticness (0–1).

Genres represented: pop, lofi, rock, ambient, jazz, synthwave, indie pop. Moods represented: happy, chill, intense, relaxed, focused, moody. The catalog skews toward Western, English-language music. Genres like hip-hop, classical, R&B, and K-pop are absent, so users with those preferences will receive poor recommendations. No songs were added or removed from the starter set.

---

## 5. Strengths

- Works well for pop and lofi listeners — those genres have multiple catalog entries with varied moods and energies, giving the scorer real options to differentiate.
- The energy proximity signal means the system never gives a zero-value score, so it always finds something reasonable even when genre and mood are both wrong.
- The scoring logic is fully transparent: every point awarded has a named reason, and `explain_recommendation` surfaces those reasons to the user.
- Simple to audit — the entire decision process fits in one short function with no hidden parameters.

---

## 6. Limitations and Bias

- The catalog is tiny (10 songs). Any genre with only one representative (rock, ambient, jazz, synthwave, indie pop) is practically guaranteed to rank near the bottom for users who prefer a different genre, even if the energy and mood are perfect.
- Tempo, valence, and danceability are stored but ignored by the scorer, so two songs in the same genre with very different "feel" can end up tied.
- The system treats all users as having a single, fixed taste. It cannot model people who want variety, who cycle between moods, or who like a genre in some contexts but not others.
- Genre and mood weights (3 and 2 points) are hard-coded. Users outside the represented genres are systematically under-served compared to pop or lofi listeners who have multiple catalog matches.
- `likes_acoustic` is a binary flag. Listeners who enjoy both acoustic and electric sounds have no way to express that nuance.

---

## 7. Evaluation

Five user profiles were tested manually, including two adversarial / edge-case profiles designed to expose weaknesses.

### Standard profiles

| Profile | Top pick | Score | Intuitive? |
|---|---|---|---|
| pop, happy, energy 0.8 | Sunrise City by Neon Echo | 6.96 / 8.00 | Yes — genre + mood + energy all align |
| lofi, chill, energy 0.4, acoustic | Midnight Coding by LoRoom | 7.96 / 8.00 | Mostly — Midnight Coding edges Library Rain because its energy (0.42) is 0.02 closer to target, even though Library Rain is more acoustic (0.86 vs 0.71) |
| rock, intense, energy 0.9 | Storm Runner by Voltline | 6.98 / 8.00 | Yes — only rock song, perfect mood and energy match |

### Adversarial / edge-case profiles

**Profile 4 — Jazz + Intense + High Energy (0.9)**

No catalog song has both jazz genre and intense mood. The top two results were nearly tied:
- Storm Runner (rock/intense, 0.91): scored 3.98 — earned by mood + energy match, not genre
- Coffee Shop Stories (jazz/relaxed, 0.37): scored 3.94 — earned by genre alone despite totally wrong mood and energy

A user wanting "high-energy, intense jazz" gets one jazz song that is slow and relaxed, and one intense song that is rock. Neither is what they asked for, and the scores are nearly identical — the system has no way to break this tie meaningfully.

**Profile 5 — Ambient + High Energy (0.9) + Acoustic**

Spacewalk Thoughts ranked first at 4.76 purely because it is the only ambient song — but its energy is 0.28, the exact opposite of the user's stated 0.9 target. Genre weight (3 pts) overwhelmed the large energy penalty. A user asking for "high-energy ambient" gets the most low-energy song in the catalog as their top recommendation.

### Weight-shift experiment

Doubled energy weight (up to 4.0 pts) and halved genre weight (1.5 pts) for the pop/happy/0.8 profile:

| Rank | Standard weights | Experimental weights |
|---|---|---|
| 1 | Sunrise City (6.96) | Sunrise City (7.42) — unchanged |
| 2 | Gym Hero (4.74) | Rooftop Lights (5.84) — jumped from #3 |
| 3 | Rooftop Lights (3.92) | Gym Hero (4.98) — dropped from #2 |

Gym Hero (energy 0.93, diff = 0.13 from target 0.80) dropped behind Rooftop Lights (energy 0.76, diff = 0.04) once energy was worth more than genre. This confirms that in the standard model, a genre match can compensate for a poor energy fit — which may not match what users actually want.

The pytest suite covers sort order and explanation output.

---

## 8. Future Work

- Add tempo range preferences (`min_bpm`, `max_bpm`) so users who want slow ballads vs. fast workout tracks can express that.
- Include valence and danceability in the score to capture the "upbeat vs. melancholy" axis that mood alone doesn't fully represent.
- Introduce a diversity penalty so the top 5 don't all come from the same genre when the catalog grows.
- Support multiple users and blend their profiles for group listening recommendations.
- Replace the hard-coded weights with learned values derived from user feedback (thumbs up / thumbs down).

---

## 9. Personal Reflection

Building this made the abstraction behind real recommenders concrete: Spotify's "Discover Weekly" is, at its core, the same loop — score songs, sort, return top-k — just with millions of users providing implicit feedback that refines the weights continuously. The most surprising part was how much the genre bonus (3 points out of 8) dominates: a perfect energy and mood match in the wrong genre still scores lower than a genre hit with mediocre energy. That's probably realistic, but it also means the system has almost no path to surprising a user with something outside their stated genre, which is exactly the kind of serendipity that makes a real playlist feel fresh. That tension between relevance and discovery is where human judgment — a curator deciding to break the pattern — still matters even when the model seems to be working well.
