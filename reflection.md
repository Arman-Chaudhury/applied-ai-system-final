# Reflection — Music Recommender Simulation

## Profile Comparisons

### Profile 1 (Pop/Happy/0.8) vs Profile 3 (Rock/Intense/0.9)

Both profiles received "Gym Hero" (pop, intense, energy 0.93) in position #2, but for completely different reasons. For the pop listener, Gym Hero appeared because its genre matched even though its mood (intense) was wrong. For the rock listener, Gym Hero appeared because its mood and energy closely matched even though its genre (pop) was wrong. The same song satisfied two very different users for opposite reasons — genre dominance for one, mood/energy proximity for the other. This shows the system is doing something reasonable, but a user who gets Gym Hero recommended when they asked for "happy pop" might be confused by an intense workout track appearing so high.

### Profile 1 (Pop/Happy) vs Profile 2 (Lofi/Chill/Acoustic)

The lofi/acoustic profile produced noticeably tighter top scores (7.96 and 7.90) compared to the pop profile's top score (6.96). This happened because the catalog has three lofi songs and they cluster well: two are chill mood, all three are low energy, and two exceed the 0.6 acousticness threshold for the bonus point. The lofi listener is better served by this catalog than the pop listener — not because the scoring algorithm is smarter, but because the data happens to have more and better-matched lofi songs. This is a data bias, not a model quality difference.

### Profile 2 (Lofi/Chill/Acoustic) — Midnight Coding vs Library Rain

Midnight Coding ranked first (7.96) over Library Rain (7.90) even though Library Rain is considerably more acoustic (0.86 vs 0.71). The difference came from energy proximity: Midnight Coding's energy (0.42) is only 0.02 from the target (0.40), while Library Rain's (0.35) is 0.05 away. A 0.03 difference in energy proximity (worth 0.06 points) outweighed the acoustic quality difference. Whether that ordering "feels right" depends on the listener — someone who cares more about the rainy acoustic texture might disagree with the ranking.

### Profile 3 (Rock/Intense) vs Profile 4 (Jazz/Intense/High Energy)

Both profiles wanted intense, high-energy music. The rock profile got a clear, satisfying top result: Storm Runner scored 6.98 because genre + mood + energy all aligned. The jazz profile got two nearly tied songs at ~3.95 — neither of which is actually intense jazz. "Coffee Shop Stories" (jazz) is slow and relaxed; it only appeared because its genre matched. "Storm Runner" appeared because its mood and energy matched but it is rock, not jazz. The scores were so close (3.98 vs 3.94) that the ranking barely separates them. A real user asking for "intense jazz at high energy" would find both recommendations confusing. The system cannot express "I found your genre but not your mood" vs "I found your mood but not your genre" — it just assigns similar scores to both.

### Profile 5 (Ambient + High Energy) — the genre-trap edge case

This was the most surprising result. "Spacewalk Thoughts" ranked first at 4.76 despite having energy 0.28 — the lowest in the entire catalog — when the user asked for energy 0.9. The genre bonus (+3 pts) was so large that it completely swamped the energy penalty. Energy diff = |0.28 − 0.90| = 0.62, so energy score = (1 − 0.62) × 2 = 0.76. The song still scored 3.0 + 0.76 + 1.0 (acoustic) = 4.76 just because it matched the genre. A user asking for "high-energy ambient" should arguably not be shown the most low-energy song in the catalog first — but the current scoring has no way to penalize a genre match that is paired with a wildly mismatched energy level.

## Weight-Shift Experiment Observations

Doubling the energy weight and halving the genre weight reordered positions #2 and #3 for the pop/happy profile. Gym Hero (energy 0.93, far from target 0.80) dropped behind Rooftop Lights (energy 0.76, close to target). In the standard model, Gym Hero's genre match (+3 pts) compensated for its energy distance. In the experimental model, that compensation no longer held because energy was worth twice as much. The number one result (Sunrise City) stayed the same because it wins on all three signals simultaneously — suggesting it is a genuinely good match regardless of weight choice.

## Key Limitation Identified

The system ignores the *interaction* between features. A genre match that comes with a completely mismatched energy should be worth less than a genre match where energy also aligns. The current additive scoring treats each signal independently — you earn genre points whether or not energy and mood agree. A multiplicative or threshold-based approach (e.g., "only award full genre points if energy is also within 0.3 of target") would reduce cases where the genre bonus surfaces clearly wrong songs, like the ambient/high-energy edge case above.
