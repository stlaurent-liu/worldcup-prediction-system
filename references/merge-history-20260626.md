# World Cup Prediction Skill — Merge History & Structure

## Origin

This skill is a merger of two independent systems:

1. **Hermes decision framework** (original skill, ~777 lines)
   - Pure methodology SKILL.md, no code
   - Strengths: customer mode classification, team objective vs ticket objective separation, rotation intent model, climate adaptation model, cashout engine, spending guardrail, live trigger engine
   - 2 worked example references (20260624-colombia, 20260626-turkey-usa)

2. **feibang191/worldcup-prediction-system** (GitHub, v1.0, June 2026)
   - Full quantitative engineering system: 12 Python scripts, SQLite database, 50+ references
   - Strengths: Elo/Poisson/GBM computation, 57 verified pitfalls, Chinese Sports Lottery 6-play-type system, Markowitz bet sizing, Sporttery API pipeline, backtest validation (384 matches, 55.2% accuracy), post-match calibration loop
   - URL: https://github.com/feibang191/worldcup-prediction-system

## Merge date

2026-06-26

## Merge process

1. Clone GitHub repo to /tmp
2. Copy scripts/, references/, modules/, config/, sample_data/ into skill directory
3. Do NOT overwrite existing references/data_sources.md (kept Hermes version)
4. Append engineering sections to SKILL.md (276 new lines, total 1053)
5. Fix 2 typos in original SKILL.md ("as clearly as", "Classify live exit advice as")
6. Scan for sensitive data (API keys, tokens, passwords) — none found
7. Copy to ~/Desktop, push to GitHub as stlaurent-liu/worldcup-prediction-system

## Post-merge structure

```
world-cup-prediction/
├── SKILL.md                    # 1053 lines: decision framework + quantitative engine
├── LICENSE                     # MIT
├── scripts/                    # 12 Python scripts (kelly_engine, poisson, backtest, etc.)
├── modules/                    # 7 module docs (data-collection, model-engine, etc.)
├── references/                 # 50 reference docs (pitfalls, calibration, data sources)
├── config/                     # calibrated-model.json
└── sample_data/                # football_database_sample.sqlite (19 tables) + schema.sql
```

## Complementarity

- **Framework layer** (original): teaches the agent HOW TO THINK about a match — motivation, rotation, climate, triggers, cashout, guardrails
- **Engineering layer** (merged): provides the ability to COMPUTE — Elo probability, Poisson score distribution, EV analysis, bet sizing, backtest validation

The two layers are connected in SKILL.md: the Weight Model section feeds into the Quantitative Engine Integration section, which references the scripts that implement the computation.

## Typos fixed during merge

- Line 601: "as clearly the recommended" → "as clearly as the recommended"
- Line 643: "Classify live exit advice:" → "Classify live exit advice as:"

## Other versions found

- `~/.codex/skills/world-cup-prediction/` — Codex local copy, same as pre-merge Hermes version (no engineering layer, no mandatory qualification verification rule)
- `~/Desktop/world-cup-prediction/` — old skeleton draft (254 lines, no models, safe to delete)
