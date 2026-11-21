# Tactical rationale

1. **Survival beats kill count.** The score is `16 - place`; first death is 0 even after multiple kills.
2. **Do not stay in the open center early.** Multi-bot melee movement favors minimum-risk candidate scoring and avoiding clusters.
3. **Controlled aggression.** Commit when a target is weak, close, or actively threatening; otherwise strafe at medium range.
4. **Late-zone discipline.** The shrinking zone is a hard positional constraint, so inward movement receives the largest weight.
5. **Avoid deterministic circles.** Small phase and score jitter reduce easy prediction while remaining reproducible.
6. **Fast path only.** No ML inference, map parsing, allocation-heavy search, or network calls.
