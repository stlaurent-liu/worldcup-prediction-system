# Norway vs France — Group I Round 3 | 2026-06-27 03:00 BJT

## Match Context

- Stage: Group I, Round 3 (final group match)
- Venue: Gillette Stadium, Foxborough (Boston) — altitude 79m
- Referee: Michael Oliver
- Concurrent match: Senegal vs Iraq (both eliminated, no dependency)

## Verified Group I Standings (after Matchday 2)

| Pos | Team | Pts | GD | Matches |
|:---:|:--|:--:|:--:|:--|
| 1 | France | 6 | +5 | 3-1 Senegal, 3-0 Iraq |
| 2 | Norway | 6 | +4 | 4-1 Iraq, 3-2 Senegal |
| 3 | Senegal | 0 | — | eliminated |
| 4 | Iraq | 0 | — | eliminated |

Sources: Yahoo Sports, CBS Sports, ESPN, FIFA — cross-verified 2026-06-26.

## Incentive Analysis

- **France**: draw_is_enough / avoid_loss_enough — draw locks 1st place, no need to chase goals
- **Norway**: first_place_push / must_win_for_first — must win to take 1st
- Both already qualified. 1st place likely yields easier R16 opponent.
- France game management mode: `professional_control` (Deschamps conservative style)
- Norway game management mode: `goal_difference_push` mixed with `first_place_push`

## Elo & Model

- France Elo: 1820 (calibrated, from `references/elo-calibration-20260614.md`)
- Norway Elo: ~1600 (estimated from FIFA ranking band 11-30 → 1550-1700; not in calibrated table)
- Elo gap: 220 → draw correction factor: 0.85

### Fused Model Probability (Elo 10% + Poisson 50% + Market 40%)

| Outcome | Model Prob | Market Implied | EV |
|:--|:--:|:--:|:--:|
| France Win | 63.4% | 55.6% | +15.7% |
| Draw | 17.0% | 23.1% | -38.3% |
| Norway Win | 19.6% | 20.0% | +7.4% (high uncertainty) |

Poisson λ: France 1.547, Norway 0.821, Total 2.369

### Score Distribution (top 10)

| Score | Prob |
|:--|:--:|
| 1-0 | 14.5% |
| 1-1 | 11.9% |
| 2-0 | 11.2% |
| 0-0 | 9.4% |
| 2-1 | 9.2% |
| 0-1 | 7.7% |
| 3-0 | 5.8% |
| 1-2 | 4.9% |
| 3-1 | 4.8% |
| 2-2 | 3.8% |

Model P(Over 2.5): 41.7% vs Market 56.5% → Under 2.5 has value

## Weather

- Venue: Gillette Stadium, Foxborough — June typical: High 28.2°C, Low 16.3°C, Precip 3.7mm
- Forecast: Rain possible Friday, humidity moderate
- Climate Central: 29% chance of performance-impairing heat
- Impact: Rain → pitch slick, passing accuracy down → favors physical teams; supports Under 2.5

## Key Players

- France: Mbappe (3 goals), Dembele, Barcola, Olise, Saliba, Upamecano
- Norway: Haaland (2 goals), Odegaard, Ryerson (injury concern)
- France projected (4-2-3-1): Maignan; Kounde, Upamecano, Saliba, Digne; Kone, Rabiot; Dembele, Olise, Barcola; Mbappe

## Scenarios

1. France scores first, controls tempo (35%) → 1-0, 2-0, 2-1
2. Norway presses high, France counters (22%) → 2-0, 3-1, 2-1
3. Stalemate, both accept result (20%) → 1-1, 0-0
4. Haaland breakout, Norway upset (15%) → 1-2, 2-2
5. Weather/red card high-variance (8%) → unpredictable

## Recommended Direction

- **France Win** — model 63.4% vs market 55.6%, EV +15.7%
- **Under 2.5 goals** — model 58.3% vs market 43.5%
- Score focus: 1-0, 2-0, 2-1
- Decision label: `buy_only_if_price` (lineup unconfirmed + rain variable)

## Avoid

- France -1.5 deep handicap (professional_control mode, no big-win incentive)
- Over 2.5 goals (model only 41.7%)
- Draw bet (EV -38.3%, worst value)
- Norway win (micro-positive EV but high uncertainty)

## Data Quality

- Verified: standings, results, odds, venue, weather (multi-source cross-verified)
- Inferred: Norway Elo ~1600 (FIFA ranking band estimate, not in calibrated table)
- Missing: confirmed lineups (T-90m window), Ryerson injury status, precise weather nowcast
- Confidence: medium

## Lessons

1. Norway not in Elo calibration table — had to estimate from FIFA ranking band. Should add Norway to calibration table post-match using K=30 update formula.
2. AgentKey Surf/search-web effective for international data collection when Sporttery API covers Chinese-market matches only. Cross-verify across 2+ sources for standings and results.
3. Group I incentive asymmetry is the key insight: France draw_is_enough + Deschamps conservative → professional_control → suppresses big-win and over-goal probability even though raw win probability is high.
4. Rain at Gillette supports Under 2.5 — pitch condition impacts passing teams (France) more than physical teams (Norway), but France's quality gap still dominates.
