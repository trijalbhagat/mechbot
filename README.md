# Mech Royale Aggressive-Survival Bot

A lightweight Python bot designed for the Builders Mech Royale constraints: 10 Hz observations, 50 ms response budget, 1 CPU, 512 MB RAM, no runtime network, and placement-first scoring.

## Policy
- Placement-first minimum-risk movement over 16 candidate headings.
- Zone return overrides combat.
- Avoids crowd focus fire and point-blank traps.
- Aggressively finishes weak or threatening targets.
- Predictive velocity lead and distance-based weapon choice.
- Loot detours only when nearby enemies are not pressing.
- Pure standard library and O(enemies + pickups) work per candidate tick.

## Important integration note
The official kit download endpoint rejected automated retrieval with HTTP 403, so this archive could not be validated against the exact `protocol.md` JSON Schema. The bot emits the documented conceptual fields `move`, `aim`, and `fire`, plus optional `weapon`. Compare the final action shape with the Python starter in `mechfight-kit.tar.gz`; if its wrapper uses different field names, keep `Bot.decide()` and map its returned values in `main()`.

## Protocol startup
The process writes `{"type":"ready","protocol":"mechfight/1"}` immediately on stdout, before reading stdin. Positional arguments supplied by the match runner do not block startup.

## Quick test
```bash
python3 bot.py check requirements < sample_observation.jsonl
```

## Submission workflow
1. Download `mechfight-kit.tar.gz` from the track page.
2. Copy the official Python starter folder to a public GitHub repository root.
3. Replace its decision logic with `Bot.decide()` from `bot.py`.
4. Retain the official wrapper/Dockerfile if its protocol envelope differs.
5. Run the kit's `check/check.py` command exactly as shown in its README.
6. Build for `linux/amd64`, keep the commit under 20 MB, then submit the repository URL.

## Tuning
Key constants are in `Bot.decide()`: desired engagement range (34/58), retreat health ratio (0.22), fire range (125), pickup safety distance (45), and zone safety margin (0.88). Because the 15 house bots share vision and hunt the weakest player, reducing unnecessary early damage is usually worth more than chasing an uncertain kill.
