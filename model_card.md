# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Goal / Task

Suggest up to 5 songs from a small 10-song catalog that best match a listener's stated genre, mood, and energy preferences.

---

## 3. Intended and Non-Intended Use

**Intended use:** Classroom exploration of how content-based filtering works. The system is designed for a single user who can articulate their preferences in advance.

**Not intended for:** Real product deployment, users with evolving or context-dependent taste, genres absent from the catalog (hip-hop, R&B, classical, K-pop, country), or any situation where fairness across diverse listener populations matters. Hard-coded weights and a 10-song catalog make this unsuitable for production.

---

## 4. Algorithm Summary

Every song in the catalog is described by a handful of audio traits — most importantly its genre (like pop or lofi), its mood (happy, chill, intense…), how energetic it feels on a scale from 0 to 1, and how acoustic it sounds. A listener profile captures the same four signals from the user's side: preferred genre, preferred mood, a target energy level, and whether they like acoustic sounds.

To rank songs, the model gives each one a score:
- It adds 3 points if the genre matches — the strongest signal because genre ties together production style and cultural context.
- It adds 2 points if the mood matches — capturing the emotional atmosphere the listener wants right now.
- It awards up to 2 more points based on how close the song's energy is to the user's target — a sliding reward so songs that are "almost there" still get partial credit.
- It adds 1 bonus point if the user likes acoustic music and the song is highly acoustic.

The maximum possible score is 8 points. After scoring all songs, the system returns the top 5 in order from highest to lowest score.

---

## 5. Data

The catalog contains 10 songs stored in `data/songs.csv`. Each song has: id, title, artist, genre, mood, energy (0–1), tempo_bpm, valence (musical positiveness, 0–1), danceability (0–1), and acousticness (0–1).

Genres represented: pop, lofi, rock, ambient, jazz, synthwave, indie pop. Moods represented: happy, chill, intense, relaxed, focused, moody. The catalog skews toward Western, English-language music. Genres like hip-hop, classical, R&B, and K-pop are absent, so users with those preferences will receive poor recommendations. No songs were added or removed from the starter set.

---

## 6. Strengths

- Works well for pop and lofi listeners — those genres have multiple catalog entries with varied moods and energies, giving the scorer real options to differentiate.
- The energy proximity signal means the system never gives a zero-value score, so it always finds something reasonable even when genre and mood are both wrong.
- The scoring logic is fully transparent: every point awarded has a named reason, and `explain_recommendation` surfaces those reasons to the user.
- Simple to audit — the entire decision process fits in one short function with no hidden parameters.

---

## 7. Observed Behavior / Biases

- The catalog is tiny (10 songs). Any genre with only one representative (rock, ambient, jazz, synthwave, indie pop) is practically guaranteed to rank near the bottom for users who prefer a different genre, even if the energy and mood are perfect.
- Tempo, valence, and danceability are stored but ignored by the scorer, so two songs in the same genre with very different "feel" can end up tied.
- The system treats all users as having a single, fixed taste. It cannot model people who want variety, who cycle between moods, or who like a genre in some contexts but not others.
- Genre and mood weights (3 and 2 points) are hard-coded. Users outside the represented genres are systematically under-served compared to pop or lofi listeners who have multiple catalog matches.
- `likes_acoustic` is a binary flag. Listeners who enjoy both acoustic and electric sounds have no way to express that nuance.

---

## 8. Evaluation Process

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

## 9. Ideas for Improvement

- Add tempo range preferences (`min_bpm`, `max_bpm`) so users who want slow ballads vs. fast workout tracks can express that.
- Include valence and danceability in the score to capture the "upbeat vs. melancholy" axis that mood alone doesn't fully represent.
- Introduce a diversity penalty so the top 5 don't all come from the same genre when the catalog grows.
- Support multiple users and blend their profiles for group listening recommendations.
- Replace the hard-coded weights with learned values derived from user feedback (thumbs up / thumbs down).

---

## 10. Personal Reflection

Building this made the abstraction behind real recommenders concrete: Spotify's "Discover Weekly" is, at its core, the same loop — score songs, sort, return top-k — just with millions of users providing implicit feedback that refines the weights continuously. The most surprising part was how much the genre bonus (3 points out of 8) dominates: a perfect energy and mood match in the wrong genre still scores lower than a genre hit with mediocre energy. That's probably realistic, but it also means the system has almost no path to surprising a user with something outside their stated genre, which is exactly the kind of serendipity that makes a real playlist feel fresh. That tension between relevance and discovery is where human judgment — a curator deciding to break the pattern — still matters even when the model seems to be working well.

---

## 11. Applied-AI Extension: Reliability Reflection

This section answers the reflection prompts required by the Module 5 applied-AI rubric. It extends — but does not replace — the original Module 3 reflection above.

### 11.1 Limitations and Biases in the System

The reliability layer doesn't fix the original biases — it makes them visible.

- **Catalog bias is now measurable rather than implicit.** The 10-song catalog over-represents lofi (3 songs) and under-represents jazz, rock, ambient, synthwave, and indie pop (1 song each). The evaluation harness exposes this directly: lofi profiles produce confidences > 0.65 while jazz/ambient profiles can't break 0.55 even when the user's preferences are reasonable. The bias was always there; the harness just stopped letting us pretend it wasn't.
- **The confidence metric itself encodes a value judgment.** I picked 0.7 × top-score + 0.3 × normalized-margin. A different choice (say, pure top-score) would change which adversarial cases register as "low confidence." There is no objectively correct formula here — the metric is a statement about what kinds of failure I want to be loud about.
- **Guardrails only check what I told them to check.** The validator catches type errors and out-of-range numbers, but it can't catch a user who sincerely asks for "happy intense ambient at energy 0.9" — a coherent-looking request the catalog cannot satisfy. That ends up as low confidence, not as a rejection. A more mature system would also offer a "no good match found" response instead of always returning *something*.
- **Vocabulary mismatch is a soft warning, not a hard error.** A user requesting "k-pop" gets a warning logged and a recommendation derived from mood + energy alone. That is a deliberate design choice (real users don't speak in catalog vocabulary) but it does mean the system silently degrades to a weaker scoring rule when the genre is unknown — and the user only notices if they read the warnings.

### 11.2 Could It Be Misused, and How Would I Prevent That?

The misuse risk is low — this is a 10-song toy recommender — but the architecture would scale to misuse if deployed naively:

- **Manipulating recommendations by editing `songs.csv`.** Whoever controls the catalog controls the output. In a real product this would be a content-policy and access-control problem, not a model problem. Mitigation: treat the catalog as a versioned, audited input rather than a config file; require code review for changes; log catalog hashes alongside recommendations so a misranking can be traced back to the data state at the time.
- **False precision in the confidence number.** A user (or a downstream system) might read `confidence = 0.72` as a probability and act on it. It is not a probability — it is a heuristic. Mitigation: in the README and docstrings, document confidence as a *relative reliability signal* with no probabilistic interpretation, and never expose it as a percentage in user-facing UI.
- **Genre dominance as soft demographic steering.** If the catalog over-represents one cultural style, every user — regardless of stated preference — gets pulled toward that style as a fallback. At scale this is how recommenders entrench existing taste hierarchies. Mitigation here is fundamentally human: the catalog must be curated by someone whose job is to balance representation, not by the engineer optimizing the score.

### 11.3 What Surprised Me While Testing Reliability

Three things genuinely surprised me:

1. **The lofi case dragged confidence down despite a near-perfect top score (7.96 / 8.00).** Two great answers separated by 0.06 points produced an overall confidence of ~0.70 — barely above the failure threshold. That's the formula working as intended, but it taught me that "reliability" is multi-dimensional: a system can be confident in *what is in its top-k* while genuinely uncertain about *the order within it*, and a single confidence number can't express both.
2. **The adversarial jazz case scored 3.98 — only marginally below the threshold.** I expected adversarial inputs to produce dramatically low scores. Instead they produce middling scores with tiny margins, which is a different (and harder to spot) failure shape. If I had only watched the top score, I would have called the system fine.
3. **Most "improvements" I tried during development made some other case worse.** Lowering the genre weight helped the ambient adversarial case but pushed the strong rock match out of the top spot. That's the bias-variance trade-off in miniature, and it's the reason a fixed evaluation suite matters: without it, you only see the case you happened to be looking at.

### 11.4 AI Collaboration Retrospective

I worked with an AI coding assistant throughout this extension. Two specific moments stand out:

- **One genuinely helpful suggestion.** When I described the reliability goal, the assistant proposed splitting confidence into a *blended* metric (top-score + margin) rather than picking one axis. I had defaulted to `score / max_score`. The blended version is what made the adversarial cases register as low-confidence — the original metric would have called them ~0.5, which is too high to be a useful signal. That single design suggestion changed how the whole evaluation suite behaves.
- **One flawed suggestion.** Earlier, the assistant proposed setting `confidence_above = 0.7` for the lofi case based on the high top score (7.96/8.00). I accepted it without checking the math. The actual computed confidence is ~0.698 — just barely below 0.7 — because the margin between Midnight Coding and Library Rain is only 0.06 points. The test would have failed on the very first run. I caught it by walking through the formula by hand before running pytest, and lowered the threshold to 0.65. The lesson: AI suggestions about *what numbers to assert* require the same scrutiny as suggestions about *what code to write*. Plausibility ≠ correctness, especially with thresholds that look round and reasonable.

The broader pattern: the AI was strongest at proposing structure (the blended confidence metric, the guardrail/core/eval/output layering, the evaluation case shape) and weakest at numeric judgment (specific thresholds, specific weights). I came away trusting it more for architecture and less for arithmetic.
