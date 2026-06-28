# Module: Odds Analysis

> Sources: soccer-lottery + worldcup-betting-analyst + soccer-betting-master-system

## Three-Dimension Weighted Model

| Dimension | Weight | Description |
|:|:|:|:|
| Motivation Analysis | 40% | Relegation/title/nothing to play for |
| Odds Movement | 35% | Market consensus + money flow |
| Recent Form | 25% | Last 10 matches + home/away |

## China Sports Lottery Rules (Ticket Output)

**Authoritative reference:** `references/sporttery-vs-overseas-rules.md`

| API | Play | Notes |
|:--|:--|:--|
| HAD | 胜平负 | May be unsold or parlay-only per match |
| HHAD | 让球胜平负 | Integer handicap only; ≠ overseas Asian handicap |
| CRS | 比分 | Per-match single availability |
| TTG | 总进球 | 0–7+ buckets; **not** O/U 2.5 |
| HAFU | 半全场 | Raw HT/FT; not handicap-adjusted |
| MIX | 混合过关 | Cross-match only; same-match mix illegal |

**Before recommending:** verify `singleList` via `getFixedBonusV1`. Never output "over 2.5" or "AH -0.5" as Sporttery bets.

## Overseas Odds (Analysis Only)

Use Titan007 / Pinnacle / Bet365 for **dewatered probabilities** and market sentiment. Map conclusions to Sporttery plays before ticket output.

- Asian handicap / O-U 2.5 → inform model only
- Divergence vs Sporttery >5% → flag pricing edge or trap

**Automated mapping:** run `scripts/odds_cross_compare.py` — outputs `sporttery_mappings` (外盘偏差 → 竞彩可买选项，含 `singleList` 单关/仅过关)。JSON: `数据/odds_cross_compare.json`.

## Recommendation Logic

- HAD: Direction when highest prob >= 50% **and** HAD is on sale + single-eligible (or note parlay-only)
- HHAD: Recommend when cover prob >= 65%; state exact handicap line
- CRS: Top 3 likely scores; prefer singles when `single:1`
- TTG: Predicted total → map to **goal-count buckets** (e.g. 2球/3球), not O/U 2.5
- Parlay: Only when required by `single:0` or clear EV; prefer singles for dispersion

## Pitfalls

1. Odds != Probability: Must remove overround first
2. Sporttery margin 15-20%: Much higher than international (5-6%)
3. Dual source divergence >5%: Market not formed, bet cautiously
