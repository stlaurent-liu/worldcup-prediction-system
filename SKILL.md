---
name: world-cup-prediction
description: 体彩竞彩/彩票票据截图分析、六种玩法EV与串关优化。世界杯预测决策系统：赛前/赛中分析、出线动机、同组依赖、淘汰赛路径、赔率价值、止损止盈、强制改模。Use when user sends lottery screenshots, 竞彩投注单, or asks for match prediction.
---

# World Cup Prediction

## Operating Principle

Use this skill to produce a disciplined decision system, not a simple score guess.

Always build the prediction in this order:

1. Identify tournament stage: `group` or `knockout`.
2. Identify decision phase and customer mode.
3. For group-stage matches, model qualification objectives and same-group live dependency before judging team strength.
4. For knockout matches, model advancement path, extra-time tolerance, and penalty-risk posture before judging score ranges.
5. Produce a current best estimate from all data available now, even before lineups.
6. Score the major factors and note data quality.
7. Generate match scenarios before score ranges.
8. Select the most stable current direction, plus price thresholds and lineup sensitivity.
9. Define live triggers before kickoff when the user can watch or manage live.
10. During live play, choose only among hold, partial cashout, full cashout, no add, or remodel.
11. Preserve the prematch thesis unless a trigger, same-group score dependency, or forced-remodel condition occurs.

Do not output "sure win", "guaranteed", "no risk", stake sizing, or instructions to chase losses. Treat betting language as directional analysis with explicit uncertainty and risk boundaries.

The core separation is:

- The match model estimates how the match is likely to be played.
- The odds/value model estimates whether the current price is worth touching.
- The spending guardrail blocks impulse decisions and chase behavior.
- The cashout engine evaluates whether continuing to hold is better than accepting a live exit offer.

When these components disagree, do not morally lecture the user. Return the best available current plan, explain the conflict, and use clear decision labels such as `buy_now_allowed`, `buy_only_if_price`, `small_test_only`, `hold`, `no_add`, or `pass_edge_insufficient`.

## Customer Mode

Classify the user's operating mode before deciding what kind of plan to output:

- `live_watch_user`: user can watch the match and manage live decisions.
- `pre_match_only_user`: user wants to buy before kickoff and cannot manage live, for example because they need to sleep.
- `already_bought_user`: user already has a position and needs hold/cashout/no-add guidance.
- `casual_check_user`: user only asks for analysis and has not expressed purchase intent.

For `pre_match_only_user`, do not rely on live triggers or cashout as part of the core plan. Give the best current prematch plan, show the missing-lineup risk, and define which lineup surprises would have changed the recommendation if the user were awake. If the user declares a fixed entertainment test amount, treat it as a constraint and do not invent bankroll sizing.

## Decision Timeline

Use the timeline to version the answer, not to block analysis. At any time before kickoff, output a current version based on the data available now.

- `Any pre-kickoff time`: Build a current best estimate from fixtures, motivation, team strength, coach behavior, venue, travel, forecast weather, known injuries, news, and available market prices. Make the lineup gap explicit rather than refusing to decide.
- `T-6h rapid prematch`: Refresh the current best estimate with near-term weather forecast, injury/news status, and market movement. This is a useful default customer entry point, not a hard requirement.
- `T-90m to T-60m lineup window`: Treat this as the main uncertainty-reduction window. For the FIFA World Cup 26, teams submit completed start lists at least 90 minutes before kickoff, and start lists are published only once both teams have submitted them. Upgrade, downgrade, or invalidate the current scenario based on goalkeeper, center-back pairing, defensive midfielders, wide pace, striker availability, and core rotation.
- `T-15m to T-5m final check`: Reconfirm weather, warm-up injury, abnormal market movement, public overheat, and whether price still has value. These are not new data categories; they are final versions of data already observed earlier. Do not invent a new thesis unless a forced-remodel condition occurs.
- `In-play`: Evaluate only at defined checkpoints or forced events. Do not chase every odds tick.

Default in-play checkpoints:

- 15 minutes: validate whether the opening script is real.
- 30 minutes: first conditional decision window.
- Halftime: largest tactical adjustment window.
- 60 minutes: motivation and substitution pivot.
- 75 minutes and later: high-variance zone; default to no add unless a prewritten trigger is strongly met.

## Data Contract

Collect or ask for these inputs when available. If any field is missing, continue with a lower confidence rating and mark it in `data_quality.missing`.

```json
{
  "match_context": {
    "stage": "group|knockout",
    "group": "",
    "round": "",
    "team_a_points": 0,
    "team_b_points": 0,
    "goal_difference": {},
    "qualification_scenarios": {
      "win": "",
      "draw": "",
      "loss": ""
    },
    "group_stage_incentive": {
      "must_win": false,
      "draw_is_enough": false,
      "avoid_loss_enough": false,
      "already_qualified": false,
      "second_place_acceptable": false,
      "first_place_push": false,
      "rotation_likely": false,
      "rotation_intent": "protective_rotation|competitive_rotation|mixed|unknown",
      "goal_difference_need": "",
      "injury_conservation_priority": "low|medium|high",
      "same_group_live_dependency": {
        "has_concurrent_match": false,
        "concurrent_match": "",
        "current_score": "",
        "dependency_effect": "none|draw_becomes_enough|win_becomes_required|avoid_loss_becomes_enough|goal_difference_push|unknown"
      }
    },
    "knockout_incentive": {
      "advance_at_any_cost": false,
      "normal_time_win_push": false,
      "extra_time_acceptance": "low|medium|high",
      "penalty_confidence": "low|medium|high|unknown",
      "risk_control_until_60": false,
      "late_push_after_75": false
    }
  },
  "team_strength": {
    "elo": {},
    "xg_for": {},
    "xg_against": {},
    "shots_quality": {},
    "set_piece_strength": {},
    "transition_attack": {}
  },
  "coach_profile": {
    "lead_behavior_index": 0,
    "trailing_aggression_index": 0,
    "substitution_timing": 0,
    "risk_tolerance": 0,
    "big_win_tendency": 0,
    "group_stage_rotation_tendency": 0,
    "protect_core_players_tendency": 0,
    "settle_for_draw_tendency": 0
  },
  "environment": {
    "temperature": 0,
    "humidity": 0,
    "thunderstorm_probability": 0,
    "wind_speed": 0,
    "altitude": 0,
    "pitch_condition": "",
    "travel_distance_km": 0,
    "hydration_break_impact": true,
    "venue_climate_profile": {
      "typical_temperature": 0,
      "typical_humidity": 0,
      "climate_type": ""
    },
    "team_a_climate_profile": {
      "home_climate_type": "",
      "typical_temperature": 0,
      "typical_humidity": 0,
      "humidity_adaptation": "low|medium|high",
      "heat_adaptation": "low|medium|high",
      "altitude_adaptation": "low|medium|high",
      "training_base_adaptation_days": 0
    },
    "team_b_climate_profile": {
      "home_climate_type": "",
      "typical_temperature": 0,
      "typical_humidity": 0,
      "humidity_adaptation": "low|medium|high",
      "heat_adaptation": "low|medium|high",
      "altitude_adaptation": "low|medium|high",
      "training_base_adaptation_days": 0
    },
    "relative_climate_edge": "team_a|team_b|neutral|unknown"
  },
  "market": {
    "opening_line": {},
    "t_minus_24h": {},
    "pre_lineup": {},
    "post_lineup": {},
    "kickoff_minus_5m": {},
    "live_odds": {},
    "cashout_offer": {},
    "odds_movement": {},
    "public_bias": "",
    "market_fundamental_alignment": "market_confirms_model|market_overheated_against_model|market_warning_unexplained|market_underpricing_favorite|unknown"
  },
  "news_sentiment": {
    "injuries": [],
    "manager_comments": [],
    "locker_room_risk": 0,
    "transfer_noise": [],
    "media_pressure": 0
  },
  "referee": {
    "yellow_card_rate": 0,
    "red_card_rate": 0,
    "penalty_rate": 0,
    "added_time_tendency": 0
  },
  "live_state": {
    "minute": 0,
    "score": "",
    "xg": {},
    "shots_quality": {},
    "dangerous_attacks": {},
    "cards": [],
    "substitutions": [],
    "weather_interruption": false,
    "cashout_offer": null,
    "original_entry_price": null
  },
  "customer_mode": {
    "mode": "live_watch_user|pre_match_only_user|already_bought_user|casual_check_user",
    "can_watch_live": false,
    "can_wait_for_lineup": false,
    "declared_test_amount": null,
    "already_bought": false,
    "entry_market": "",
    "entry_odds": null,
    "ticket_objective": "team_win|team_not_lose|handicap|total_goals|score_range|half_full_time|parlay|unknown"
  },
  "user_behavior": {
    "is_impulse_purchase": false,
    "recent_losses_mentioned": false,
    "trying_to_chase": false,
    "understands_full_loss_possible": false,
    "too_many_matches_selected": false
  }
}
```

## Data Source Policy

Classify each input as `verified`, `manual`, `inferred`, or `missing`.

Also classify time-sensitive inputs by version:

- `forecast`: available before matchday but still changeable, especially weather.
- `current`: latest checked value at the time of the answer.
- `confirmed`: official or highly reliable, such as published start lists or confirmed injuries.
- `rumor_or_unverified`: plausible but not decision-grade without cross-checking.
- `late_random`: only knowable close to kickoff or during play, such as warm-up injury, sudden storm cell, last-minute lineup replacement, or sharp final market move.

Recommended source layers:

- Fixtures, venue, kickoff time, competition rules: FIFA or a trusted fixture API.
- Weather, heat, humidity, rain, wind, thunderstorm risk: weather API for the stadium location and kickoff window. Use early forecasts before kickoff, then refresh near match time; do not treat early weather as missing.
- Lineups: official FIFA start list, team channels, or a trusted football data API. If confirmed lineups are missing before kickoff, return a `pre_lineup_current_plan` with lineup sensitivity and confidence penalty, not a blank wait state.
- Scores, cards, substitutions, live stats: official match center or trusted live-data API. If live xG or shot quality is missing, lower confidence and rely on observable events only.
- Injuries and availability: confirmed federation/team updates, reputable reporters, press conferences, and match previews. Separate confirmed absences from doubtful players and rumors.
- Market heat and odds timeline: user input, odds API, or manually captured bookmaker data. Track opening, current, pre-lineup, post-lineup, and final market states. Do not scrape or assume bookmaker data when absent.
- Cashout offer: user-provided live offer or platform API. If cashout offer is missing, do not say whether to sell; only say what information is needed.

For concrete source suggestions, API endpoints, and integration notes, read `references/data_sources.md` before building a collector, automation, or source-backed match report.

Data sufficiency rules:

- Without confirmed lineups: allow a pre-lineup recommendation if enough non-lineup data exists, but include `lineup_sensitivity`, `confidence_penalty`, and `upgrade_or_cancel_conditions`.
- Without current odds: no value recommendation, only football probability direction and fair-price thresholds.
- Without cashout offer: no concrete cashout recommendation.
- Without live stats: in-play confidence cannot be high.
- Without weather data in 2026 North American venues: environment risk must be at least `unknown_medium`, not ignored. If forecast data exists but latest nowcast is missing, mark it as `forecast_not_final`, not `missing`.
- **Mandatory first step**: For group-stage matches, always verify current group points and qualification status before classifying team objectives. Do not assume every final-group match has both teams needing to win; one or both may already be qualified or eliminated, which changes motivation and rotation risk completely. See `references/20260626-turkey-usa-groupc.md` for a worked example.

## Weight Model

Use these weights unless the user explicitly asks to experiment with alternatives:

```text
PreMatchScore =
motivation_score * 0.25 +
coach_score * 0.15 +
strength_score * 0.15 +
environment_score * 0.15 +
market_score * 0.10 +
style_matchup_score * 0.08 +
locker_room_score * 0.07 +
referee_score * 0.05
```

Default factor weights:

- Qualification motivation: 25%
- Coach personality and game-state behavior: 15%
- Team strength data: 15%
- Environment and venue: 15%
- Betting market timeline: 10%
- Style matchup: 8%
- Locker-room and media sentiment: 7%
- Referee tendency: 5%

For the 2026 World Cup, keep environment weight high. Explicitly evaluate thunderstorm delay risk, heat, humidity, hydration breaks, altitude, pitch condition, and travel distance. Weather interruption, extreme heat, and forced hydration rhythm can change pressing intensity, substitutions, tempo, and late-game fatigue.

## Tournament Stage Model

Choose the model by tournament stage before interpreting strength, odds, or scorelines.

For `group` matches, the primary question is qualification objective management:

- Can the team advance with a draw?
- Is avoiding defeat enough?
- Is second place acceptable, or is first place materially better?
- Does goal difference matter?
- Is the team already qualified or nearly qualified?
- Is the team likely to preserve players, avoid cards, or reduce injury risk?
- Is there a simultaneous same-group match that changes the live objective?

For `knockout` matches, the primary question is advancement path:

- There is no group-table draw objective; the team must advance.
- A team may still prefer risk control in normal time if extra time or penalties are acceptable.
- Model whether the coach pushes for a normal-time win, controls risk until 60 minutes, waits for late substitutions, or accepts penalties.
- Include extra-time fatigue, penalty confidence, yellow-card accumulation, and substitution depth.

Do not apply group-stage control logic to knockout matches. Do not apply knockout "must win now" logic to group-stage matches where a draw or narrow result is enough.

## Team Objective vs Ticket Objective

Separate the team's competitive objective from the user's ticket objective.

Examples:

- A team may only need a draw to advance, while the user ticket requires that team to win.
- A team may accept second place, while the ticket requires a deep handicap.
- A team may lead and protect players, while the ticket needs more goals.
- A team may chase only an equalizer, while the ticket needs a comeback win.

When these diverge, lower the value rating of the ticket even if the football direction looks reasonable.

Output the mismatch explicitly:

```text
team_objective: draw_enough
ticket_objective: team_win
alignment: weak
interpretation: The team can satisfy its tournament goal without satisfying the ticket.
```

## Conditional Amplifiers

Do not rely only on static weights. Apply conditional amplifiers when factors reinforce each other. Use these as probability-shift heuristics, not deterministic multipliers.

Raise favorite big-win and over-goal scenario weight when several of these align:

- Strong favorite dropped points in the previous group match and faces `statement_response_pressure`.
- Favorite must win and goal difference matters.
- Underdog already conceded multiple goals in the previous match or showed defensive fragility.
- Market deep handicap and totals align with the same football fundamentals.
- Favorite's confirmed lineup is strong, with first-choice center backs and enough attacking width or pace.
- Favorite has a bench-depth and climate-adaptation edge.
- Rotation is `competitive_rotation`, where substitutes are trying to prove themselves and keep the team's internal level high.
- Early-goal collapse risk is high because the underdog's low-block plan depends on surviving the opening phase.

Lower big-win and over-goal scenario weight when several of these align:

- Favorite is already qualified or draw-is-enough.
- Coach has a strong protect-lead tendency or rotation is clearly `protective_rotation`.
- Favorite lineup lacks width, speed, or chance creation.
- Market is hot but football fundamentals do not support the move.
- Weather, travel, or altitude disadvantages affect the favorite more than the underdog.

Document which amplifier changed the scenario distribution. Avoid silent probability shifts.

## Climate Adaptation Model

Do not treat weather as a uniform effect. Compare the match environment with each team's usual climate, training base, travel, squad depth, and tactical burden.

Evaluate:

- Absolute match environment: temperature, humidity, thunderstorm risk, wind, altitude, roof or pitch, hydration breaks.
- Venue climate baseline: whether the matchday conditions are normal or extreme for the host city.
- Team origin and player-base climate: home-country climate, major club leagues, recent camp location, and adaptation days.
- Relative climate edge: which team is better adapted to heat, humidity, altitude, or travel.
- Tactical exposure: which team must run more without the ball, defend low for long periods, press high, or chase the match.
- Bench depth: which team can maintain intensity through substitutions.

Interpretation rules:

- Similar climate profiles reduce the environment penalty.
- High heat or humidity can reduce high-press intensity, but it can also accelerate the weaker team's defensive collapse when that team spends long periods without the ball.
- Dry heat and humid heat are different. Humidity should increase concern about concentration drops, cramps, recovery between sprints, and late defensive errors.
- If the strong team has a climate or depth edge, hostile weather may amplify late scoring rather than suppress it.
- If the underdog is more climate-adapted and the favorite relies on sustained pressing, weather may support a narrower score.
- If weather causes interruption, forced hydration rhythm, or pitch deterioration, reassess tempo and technical-quality assumptions.

Do not write "hot weather means under" without checking relative adaptation and tactical burden.

## Group Stage Incentive Model

In group-stage matches, do not equate team strength with match intensity. Some strong teams do not need to win big, especially when a draw is acceptable, qualification is nearly secured, heat is high, travel load is heavy, or the coach is protecting core players.

Always classify each team:

- `must_win`: needs three points to qualify, recover from a poor start, or avoid elimination.
- `statement_response_pressure`: strong team dropped points or played poorly in the previous match and needs a convincing response for standings, goal difference, morale, or media pressure.
- `draw_is_enough`: one point materially improves or secures qualification.
- `avoid_loss_enough`: the team can achieve its objective by not losing, even if a win would be better for market optics.
- `second_place_acceptable`: the team does not need to risk everything for first place.
- `first_place_push`: the team has a strong reason to win the group, such as a materially better knockout path or host advantage.
- `goal_difference_chasing`: needs margin, which can support late pressure and bigger scorelines.
- `already_qualified_or_nearly`: may lower pressing, rotate, slow tempo, or protect stars.
- `injury_conservation`: likely to reduce duels, avoid unnecessary tempo, or substitute core players early.
- `third_round_rotation_risk`: strongest in the final group match when qualification math allows rest.
- `protective_rotation`: rotation intended to protect core players, reduce injury/card risk, and lower tempo.
- `competitive_rotation`: rotation intended to keep intensity, let substitutes compete for knockout minutes, preserve winning rhythm, or raise the squad's overall form.
- `same_group_live_dependency`: simultaneous group match can change the team's live objective.

Adjust market interpretation:

- Strong team plus `must_win` supports win probability, but not automatically deep handicap coverage.
- Strong team plus `draw_is_enough` or `injury_conservation` lowers big-win and over-goal confidence.
- Team plus `draw_is_enough` or `avoid_loss_enough` may not chase a win after 0-0 or 1-1 if the concurrent match favors them.
- Favorite leading by one or two goals with conservation incentives should increase control/slow-tempo scenarios.
- Underdog `must_win` can increase late 1-1, 2-1, and high-variance outcomes after 60 minutes.
- Goal-difference incentives can justify continued pressure after a lead, but only when coach style and environment support it.
- If same-group live scores change the objective, rebuild the live scenario distribution immediately.
- Do not treat rotation as automatically conservative. Classify `protective_rotation` versus `competitive_rotation`.

## Game Management Model

In group-stage matches, classify the strong team's desired game state. This is different from raw win probability.

Use these labels:

- `statement_win`: team needs a convincing response, goal difference, morale repair, or media-pressure release. Big-win and continued-pressure scenarios can rise.
- `professional_control`: team mainly needs the result and is likely to manage tempo after leading. One-goal or two-goal wins rise; deep handicap and over-goal confidence fall.
- `draw_acceptable`: draw materially helps qualification or group position. Draw and low-event scenarios rise, especially if both sides benefit.
- `avoid_loss_control`: not losing is enough. The team may resist opening the game even if it is stronger.
- `rotation_preservation`: team is likely to rest core players, avoid injury, and reduce intensity. Under, narrow-win, and late-control scenarios rise.
- `competitive_rotation`: team is already safe or nearly safe, but substitutes are incentivized to play intensely, win roles, and keep team rhythm. Late scoring and opponent-collapse scenarios can rise if the opponent must chase.
- `goal_difference_push`: team has a clear goal-difference incentive. Continued attack after leading becomes more plausible.
- `live_objective_shift`: same-group live score has changed the optimal target from win to draw, draw to win, or margin to control.

Inputs:

- Current group points, goal difference, goals scored, and tiebreaker position.
- Remaining opponent quality and travel/rest burden.
- Whether a draw or narrow win is enough.
- Same-group concurrent score and live table.
- Coach style and substitution tendencies.
- Player availability, accumulated fatigue, and injury-conservation priority.
- Rotation intent: protective preservation or competitive squad-building.
- Market totals and handicap: whether the market expects control or pursuit of margin.

Interpretation:

- Do not assume a strong team always maximizes goals.
- Do not assume a strong team always preserves energy.
- Do not assume rotation means lower motivation. Substitutes in a strong squad may increase intensity because they are auditioning for knockout minutes.
- Pick the management mode that best matches standings incentives, coach profile, lineup strength, and market-fundamental alignment.
- If the mode is `professional_control` or `rotation_preservation`, lower exact-score clusters such as 3-0, 4-0, 4-1 unless early-goal collapse or goal-difference push overrides it.
- If the mode is `competitive_rotation` and the opponent must chase, raise late goal and margin-extension scenarios even if starters are rested.
- If the team objective and ticket objective diverge, flag it. For example, a team that only needs a draw may not help a `team_win` ticket after the match becomes level.

## Rotation Intent Model

Before downgrading a rotated lineup, decide why the team is rotating.

Classify as `protective_rotation` when:

- The team faces a difficult knockout path and wants to protect core players.
- Draw or avoid-loss is enough and the opponent is strong enough to punish risk.
- The coach has a conservative tournament profile.
- Key players have knocks, yellow-card risk, or heavy minutes.
- The lineup sacrifices attacking width, transition threat, or chance creation.

Classify as `competitive_rotation` when:

- The team is strong enough that substitutes still create a large quality edge.
- The opponent is weaker or must chase the game.
- Substitute attackers or midfielders are competing for knockout roles.
- The coach wants rhythm, confidence, and squad-wide sharpness.
- The market and fundamentals still support the favorite after rotation.

Interpretation:

- `protective_rotation` lowers tempo, deep handicap, and over-goal confidence.
- `competitive_rotation` can preserve or raise late attacking intensity.
- If rotation type is unclear, do not assume either direction; mark `mixed` or `unknown`.

## Coach Style Model

Coach behavior is a separate factor from team quality. Evaluate:

- Whether the coach protects a one-goal lead or keeps attacking.
- Whether substitutions usually arrive early or late.
- Whether the coach accepts a draw in tournament contexts.
- Whether core attackers are substituted early when leading.
- Whether the coach runs up scores or conserves energy.
- Whether the coach rotates in group-stage matches.

Use coach style to decide between "favorite wins comfortably" and "favorite wins but does not cover." This matters especially for handicap, total goals, and exact-score clusters.

## Market Handling

Do not treat odds or handicap lines as truth. Treat them as market information that may encode public bias, injury rumors, sharp movement, liquidity, and timing.

When market movement matters, cross-check it against:

- Team news and injuries
- Confirmed or likely lineups
- Weather and pitch conditions
- Motivation and qualification incentives
- Public bias toward famous teams or stars

If the market moves without an explainable football reason, mark it as a risk flag rather than blindly following it.

Classify market and fundamentals alignment:

- `market_confirms_model`: market heat, deep handicap, or rising totals agree with motivation, strength gap, lineup, opponent fragility, and tactical matchup. Treat as confirmation, not automatic overheat.
- `market_overheated_against_model`: market prices an aggressive result while motivation, lineup, coach style, weather adaptation, or opponent matchup argue for a narrower game.
- `market_warning_unexplained`: odds move sharply without visible news, lineup, weather, or motivation explanation. Treat as a risk flag.
- `market_underpricing_favorite`: market is cautious despite strong fundamentals; inspect for hidden injury, rotation, or weather concerns before calling it value.

Do not use "public is hot" as a standalone reason to fade a side. First decide whether market heat is explained by football fundamentals.

## Integrity Anomaly Monitor

Do not assume match fixing, private betting, or manipulation. Do not accuse players, coaches, teams, officials, or leagues without reliable public evidence.

You may monitor only verifiable anomalies:

- Sharp odds movement with no visible injury, lineup, weather, motivation, or news explanation.
- Late lineup or substitution choices that strongly conflict with normal competitive incentives.
- On-field behavior that appears tactically abnormal, while acknowledging it may have ordinary football explanations.
- Official investigation, federation statement, credible reporting, suspension, or disciplinary action.

Output anomaly labels only as uncertainty flags:

- `market_warning_unexplained`
- `behavior_anomaly_unverified`
- `integrity_risk_reported`
- `high_uncertainty_do_not_overfit`

Use these flags to reduce confidence or require more evidence. Never make them the default explanation for a prediction.

## Value Evaluation

A direction is actionable only when the model probability is meaningfully above the market-implied probability after margin and uncertainty.

Use this reasoning:

```text
implied_probability = 1 / decimal_odds
actionable_edge = model_probability - implied_probability - uncertainty_buffer
```

Guidance:

- If `actionable_edge` is clearly positive and data quality is acceptable, mark as `buy_now_allowed`.
- If the edge depends on price, mark as `buy_only_if_price` and state the minimum acceptable odds or maximum acceptable handicap.
- If the football direction is right but the price is poor, mark as `direction_only_price_bad`.
- If lineups are missing but the user cannot wait, mark as `pre_lineup_small_test_only` when the current edge is adequate after a lineup uncertainty penalty.
- If data quality is weak, mark as `needs_more_data` or `pass_edge_insufficient`.
- If the user appears to be chasing losses, mark as `chase_risk_block` for add/chase decisions. Still provide the current analytical view of the match.

Never select a recommendation only because it has the highest raw probability. A low-priced outcome can be likely but still not worth buying.

## Scenario Generation

Generate 3-5 scenarios before score ranges. Each scenario must include:

- `name`: a football script, not a score
- `probability`: calibrated approximate probability
- `why`: concise cause chain
- `score_ranges`: plausible score outcomes
- `trigger_watch`: live signs that confirm or weaken this scenario

Example scenario patterns:

```json
{
  "scenarios": [
    {
      "name": "Strong team scores first, then controls tempo",
      "probability": 0.35,
      "score_ranges": ["2-0", "2-1", "3-0"]
    },
    {
      "name": "Strong team scores early and breaks the underdog's low-block plan",
      "probability": 0.22,
      "score_ranges": ["3-0", "4-0", "5-0", "4-1"]
    },
    {
      "name": "Underdog survives early pressure and drags game into second half",
      "probability": 0.25,
      "score_ranges": ["1-0", "1-1", "2-0"]
    },
    {
      "name": "Weather interruption damages favorite's rhythm",
      "probability": 0.20,
      "score_ranges": ["1-1", "2-1", "2-0"]
    },
    {
      "name": "Red card or penalty breaks the model",
      "probability": 0.10,
      "score_ranges": ["high_variance"]
    }
  ]
}
```

## Prematch Main Direction

Select the most stable direction, not the most exciting one.

For example, if the favorite has a high win probability but the coach is conservative, environment risk is high, and the handicap is deep, prefer:

- Favorite to win
- Total goals in a controlled range such as 2-4
- Narrow-win score cluster
- Avoid deep handicap exposure

Explain the avoided directions as clearly as the recommended directions.

For pre-lineup decisions, include:

- `current_best_direction`: best answer from available data now.
- `lineup_sensitivity`: low, medium, or high.
- `price_thresholds`: acceptable odds or handicap boundaries.
- `upgrade_conditions`: lineup or market facts that improve the plan.
- `cancel_or_downgrade_conditions`: lineup or market facts that weaken the plan.

Do not make `T-90m` the only valid purchase window. It is a better information window, but some users must decide earlier. For those users, reduce confidence and simplify the plan rather than refusing to produce one.

## Live Trigger Engine

Before kickoff, define conditional actions. During the match, only adjust when a trigger fires.

Default triggers:

- 30 minutes, 0-0, favorite xG >= 0.9 and shot quality clearly superior: increase next-goal or favorite-win confidence.
- Favorite scores inside 20 minutes against an underdog whose plan was low-block survival: raise collapse and big-win scenarios, especially when the favorite has statement pressure, lineup strength, and bench-depth or climate edge.
- Halftime, 1-0, slow tempo, leading coach is conservative: lower over-goal weight and increase 1-0, 2-0, 2-1.
- 60 minutes, still 1-0, underdog must take points: increase 1-1 and 2-1 probability; do not chase a blowout.
- Same-group concurrent score changes the team's qualification objective: remodel immediately. Example: a team that needed a win may only need a draw, or a team that was controlling a draw may now need to chase.
- Team falls behind despite `draw_is_enough`: raise equalizer pressure, but do not automatically raise comeback-win probability unless standings require a win.
- Team equalizes when draw is enough and concurrent score remains favorable: lower win-chase probability and increase control/draw scenarios.
- Rotated favorite leads or faces an opponent that must chase: if rotation is `competitive_rotation`, raise late margin-extension scenarios; if `protective_rotation`, expect control and lower tempo.
- Favorite leads 2-0 before 60 minutes but substitutes core attackers: stop increasing big-score probability.
- Red card, penalty, weather delay, core injury, or major tactical reshuffle: pause the original plan and rebuild.

Forced-remodel conditions:

- Red card
- Penalty that materially changes game state
- Severe weather delay or pitch deterioration
- Core player injury or unexpected substitution
- Confirmed lineup shock
- Tactical change that invalidates the prematch matchup

## Cashout Decision Engine

Use this only when the user provides a live cashout offer or a platform/API supplies it. Do not invent a cashout price.

Classify live exit advice as:

- `hold`: prematch script still holds and the cashout offer is poor relative to model hold value.
- `partial_cashout`: prematch script is partly intact but variance has risen, or the offer already captures much of the expected value.
- `full_cashout`: the original thesis is invalidated, a forced-remodel event occurred, or the offer is attractive enough compared with continuing risk.
- `no_add`: do not add or chase, even if holding is acceptable.
- `remodel`: pause the old plan and rebuild probabilities.

Evaluate:

- Current score, minute, and remaining time.
- Whether the original scenario is confirmed or broken.
- Cards, injuries, substitutions, weather interruption, and pitch deterioration.
- Current cashout offer versus original entry price.
- Whether the user is emotionally chasing or trying to recover recent losses.

If cashout offer is absent, return:

```json
{
  "cashout_action": "need_cashout_offer",
  "reason": "Cannot evaluate sell decision without the platform's current cashout price."
}
```

## Spending Guardrail

Treat casual sports betting as impulse-prone entertainment spending, not as a professional bankroll system. Do not assume the user has a defined capital pool.

Before any buy or add recommendation, check:

- Is this a last-minute impulse purchase?
- Is the user buying because of a recent loss?
- Is the user increasing risk to recover previous losses?
- Is the user buying too many matches or unfamiliar markets?
- Would a total loss create stress or affect normal expenses?
- Is the user trying to add after 75 minutes in a high-variance phase?

Output:

- `spending_risk`: `low`, `medium`, `high`, or `chase_risk_block`
- `chase_behavior_detected`: boolean
- `max_loss_acceptance_check`: boolean
- `guardrail_message`: a direct warning when risk is high

If the user says or implies they are trying to recover losses, block add/chase behavior and label the risk clearly. Do not hide the match analysis; separate the football view from the spending-risk view.

## Output Format

Return structured JSON first, followed by a short explanation in the user's language.

```json
{
  "phase": "pre_lineup|t_minus_6h|lineup_window|final_check|in_play",
  "tournament_stage": "group|knockout",
  "customer_mode": "live_watch_user|pre_match_only_user|already_bought_user|casual_check_user",
  "prematch_main_scenario": "",
  "current_best_direction": "",
  "team_objective": {
    "team_a": "must_win|draw_enough|avoid_loss_enough|first_place_push|second_place_acceptable|rotation_preservation|advance_at_any_cost|unknown",
    "team_b": "must_win|draw_enough|avoid_loss_enough|first_place_push|second_place_acceptable|rotation_preservation|advance_at_any_cost|unknown"
  },
  "rotation_intent": {
    "team_a": "protective_rotation|competitive_rotation|mixed|unknown",
    "team_b": "protective_rotation|competitive_rotation|mixed|unknown"
  },
  "ticket_objective_alignment": {
    "ticket_objective": "team_win|team_not_lose|handicap|total_goals|score_range|half_full_time|parlay|unknown",
    "alignment": "strong|medium|weak|conflict|unknown",
    "reason": ""
  },
  "same_group_live_dependency": {
    "has_concurrent_match": false,
    "concurrent_match": "",
    "current_score": "",
    "dependency_effect": "none|draw_becomes_enough|win_becomes_required|avoid_loss_becomes_enough|goal_difference_push|unknown"
  },
  "game_management_mode": "statement_win|professional_control|draw_acceptable|avoid_loss_control|rotation_preservation|goal_difference_push|live_objective_shift|unknown",
  "scenario_amplifiers": [],
  "market_fundamental_alignment": "market_confirms_model|market_overheated_against_model|market_warning_unexplained|market_underpricing_favorite|unknown",
  "climate_adaptation": {
    "absolute_environment_risk": "low|medium|high|unknown",
    "relative_climate_edge": "team_a|team_b|neutral|unknown",
    "tactical_burden": "",
    "environment_interpretation": ""
  },
  "pre_lineup_plan": {
    "allowed": false,
    "lineup_sensitivity": "low|medium|high",
    "confidence_penalty": 0,
    "price_thresholds": [],
    "upgrade_conditions": [],
    "cancel_or_downgrade_conditions": []
  },
  "recommended_direction": [],
  "avoid": [],
  "score_distribution": {
    "2-0": 0.22,
    "2-1": 0.18,
    "3-0": 0.16,
    "1-1": 0.12
  },
  "live_triggers": [],
  "value_evaluation": {
    "model_probability": null,
    "market_implied_probability": null,
    "uncertainty_buffer": null,
    "actionable_edge": null,
    "decision": "buy_now_allowed|buy_only_if_price|pre_lineup_small_test_only|direction_only_price_bad|needs_more_data|pass_edge_insufficient|chase_risk_block"
  },
  "cashout": {
    "cashout_action": "hold|partial_cashout|full_cashout|no_add|remodel|need_cashout_offer|not_applicable",
    "reason": ""
  },
  "spending_guardrail": {
    "spending_risk": "low|medium|high|chase_risk_block",
    "chase_behavior_detected": false,
    "max_loss_acceptance_check": false,
    "guardrail_message": ""
  },
  "risk_flags": [],
  "integrity_anomaly_flags": [],
  "forced_rebuild_conditions": [],
  "data_quality": {
    "verified": [],
    "manual": [],
    "missing": [],
    "inferred": []
  },
  "confidence": "low|medium|high"
}
```

Ensure score distribution follows from the scenarios. If scenario probabilities and score distribution conflict, fix the scenario logic first rather than forcing the scores.

## Quantitative Engine Integration

This skill is backed by a full quantitative engine with executable Python scripts, a SQLite database, and calibrated model parameters. Use these resources when the user needs computed probabilities, backtested metrics, or automated data collection — not just reasoning.

### Model Computation Pipeline

```
Data Collection → Odds Dewatering → Elo/Poisson Probability → EV Analysis → Bet Sizing → Post-Match Calibration
```

Use `scripts/` for deterministic computation. The AI explains and interprets results; it does not guess probabilities when code can compute them.

| Script | Function | When to use |
|:--|:--|:--|
| `kelly_engine.py` | Kelly + EV 5-tier + **`quantize_stake` / `quantize_budget`** (2元/注票面量化) | Computing bet amounts from model probability and odds; **mandatory** before any Sporttery purchase output |
| `multi_bookmaker_engine.py` | Sporttery dewatering + 17-company Asian handicap aggregation + direction conflict detection | Multi-source odds fusion and bias detection |
| `odds_movement_engine.py` | Asian handicap water-level change detection (Δ≥0.06 triggers signal) + money flow inference | Detecting sharp market movement before kickoff |
| `wc2026_results_sync.py` | ESPN sync → **openfootball cross-check** → `wc2026_match_records` + weighted Elo + motivation tags | **Daily cron after matchday**; full backfill `--from 20260611`; mismatch → openfootball score wins |
| `openfootball_parser.py` | Parse openfootball/worldcup `cup.txt` + `cross_validate()` | Post-match score verification; CC0 backup source |
| `knockout_engine.py` | Absence Elo penalty + Bayesian PK model (N=103 prior) + `resolve_knockout_winner()` | Knockout matches; edit `config/squad_absences.json` before kickoff; MC uses this instead of 50/50 PK |
| `setup_wc2026_cron.sh` | Install/remove crontab (results 12:00&23:00 BJT + odds every 2h) | One-time deploy on tournament host |
| `odds_snapshot_cron.py` | Scheduled odds snapshot capture → `odds_snapshots` table | Automated odds monitoring every 2 hours |
| `odds_ev_analysis.py` | EV computation across all 6 lottery play types | Finding positive-EV options across HAD/HHAD/HAFU/CRS/TTG |
| `monte-carlo-tournament.py` | Monte Carlo tournament simulation (50,000 iterations) | Group qualification probability, knockout bracket paths |
| `age_peak_model.py` | Player age → peak coefficient + tournament experience index | Adjusting team strength for squad age profile |
| `hot_trap_detector.py` | Overrated high-Elo / inflated-value team flagging | Detecting popular traps where market overprices famous teams |
| `settlement_review.py` | Post-match auto-settlement + model_calibration table write | After every match: update Elo, write calibration, generate review |
| `wc2026_backtest.py` | World Cup backtest engine (5 editions, 384 matches) | Validating model accuracy and calibration curves |
| `wc2026_odds_monitor.py` | Real-time Sporttery odds monitor with change alerts | Live odds tracking during matchday |
| `weixin_fetch.py` | WeChat article extraction (gzip bypass + MicroMessenger UA) | Fetching Chinese match previews and news |

### Elo → Win/Draw/Loss Probability

```python
expected_home = 1 / (1 + 10 ** ((elo_away - elo_home) / 400))
p_home = expected_home * 0.85
p_away = (1 - expected_home) * 0.85
p_draw = 1 - p_home - p_away

# Draw correction factor decreases with Elo gap (not one-size-fits-all)
# Lesson: France(1810) vs Senegal(1580), Elo gap 230
#         Global x1.44 overestimated draw, actual 3-1 France win
if elo_gap < 50:    draw_factor = 1.44
elif elo_gap < 100:  draw_factor = 1.25
elif elo_gap < 150:  draw_factor = 1.10
elif elo_gap < 200:  draw_factor = 1.00
else:                draw_factor = 0.85
```

Elo calibration table for 48 World Cup 2026 teams: see `references/elo-calibration-20260614.md`. Wikipedia Elo values are unreliable (Germany 1496 vs actual ~1750, France 1479 vs actual ~1820).

### Poisson Score Distribution

```python
# Reverse-engineer lambda from win/draw/loss probability
lambda_total = -math.log(p_draw) * 1.15
ratio = math.sqrt(p_home / p_away)
lambda_home = lambda_total * ratio / (1 + ratio)
lambda_away = lambda_total / (1 + ratio)

# Newton iteration refinement (20 steps, max delta 0.5)
# Range: lambda_home in [0.3, 4.0], lambda_away in [0.2, 4.0]
# Verify error < 3%

# Score probability
P(i, j) = poisson(i, lambda_home) * poisson(j, lambda_away)
```

Full algorithm with Newton iteration: see `references/poisson-lambda-solver-v2.md`.

### GBM Draw Filter

Standard Poisson structurally never predicts draws as the highest probability. Solution: GBM classifier trained on 5,058 international matches. When `gbm_draw_prob > 0.35` and `p_draw > 0.22`, predict draw. Backtest: 25 draw predictions, 44% accuracy (vs 0 without filter).

### Odds Dewatering

```python
# SP odds (13% overround) vs 99-company average (~4% overround)
# Use 99Avg dewatered probability as true probability baseline
true_prob = (1 / odds_99avg) / overround_99avg

# Corrected EV = true_prob * SP_odds - 1
ev = true_prob * sp_odds - 1
# ev > 0 → positive EV, worth betting
```

Sporttery and 500.com are the same system (both China Sports Lottery). Sporttery overround is 15-20%, bet365 is 5-6%. Always dewater before model fusion.

### Model Fusion Weights

```json
{
  "model_version": "v6.0-unified",
  "weights": {
    "group_stage": {"odds": 0.50, "elo": 0.20, "xg": 0.15, "form": 0.10, "fifa": 0.05},
    "knockout": {"elo": 0.40, "odds": 0.30, "xg": 0.15, "form": 0.10, "fifa": 0.05}
  },
  "odds_sources": {
    "titan007": {"weight": 0.50, "companies": "93-187"},
    "sporttery": {"weight": 0.30, "companies": 1},
    "bet365": {"weight": 0.20, "companies": 1}
  },
  "draw_threshold": 0.35,
  "mc_iterations": 50000,
  "backtest_seasons": ["2006", "2010", "2014", "2018", "2022"]
}
```

Three-source fusion: Poisson 50% + Market 40% + Elo 10%. FIFA ranking conversion is too aggressive (Egypt away-win EV=+77% was false). Elo systematically undervalues weak teams, cap at 10%.

### Backtest Results (v6.0, 5 World Cups, 384 matches)

| Metric | Value | Notes |
|:--|:--:|:--|
| Accuracy | 55.2% | Highest across all versions |
| Log Loss | 0.9735 | Lowest across all versions |
| Brier Score | 0.1925 | First time below 0.20 |
| EV (+5% overround) | +3.20% | Positive EV |
| Draw prediction accuracy | 44% | 25 matches, GBM filter effective |
| High-confidence (≥60%) accuracy | 72.7% | 110 matches, core betting zone |

Confidence tiers: ≥55% → 65.4% accuracy, ≥60% → 72.7%, ≥65% → 69.4%.

Historical mean Poisson backtest (4,944 international matches, 500 sampled): 56.4% accuracy, Brier 0.1812, random baseline 33.3%.

## Chinese Sports Lottery Betting System

When the user is betting on China Sports Lottery (体彩竞彩), use the full 6-play-type system. **Read `references/sporttery-vs-overseas-rules.md` first** — never map overseas Asian handicap / over-under 2.5 directly to Sporttery play types. Do not only check HAD (胜平负) — always scan all available play types. For lottery ticket screenshots, follow `references/lottery-ticket-analysis.md` (see **Handling User-Provided Screenshots** below).

### 6 Play Types

| Code | Play | poolStatus | Notes |
|:----|:----|:----------:|:-----|
| HAD | 胜平负 | Selling/Define | Basic, odds may be low |
| HHAD | 让球胜平负 | Selling/Define | Handicap, often better value |
| HAFU | 半全场 | Selling | 9-in-1, high odds on upsets |
| CRS | 比分 | Selling | High odds but hard to hit |
| TTG | 总进球数 | Selling | 0-7+ goals, good for directional matches |
| (none) | 上下单双 | (no API) | Know it exists |

Iron rule: when HAD odds are too low or HAD is unavailable, do not say "skip". Must check HHAD/HAFU/CRS/TTG for value first.

### Bet Sizing: Mean-Variance Optimization (Markowitz)

All bet allocations must use mean-variance optimization. No intuitive guessing.

```
Maximize: L = Σ b_i·edge_i - (λ/2)·Σ b_i²·σ_i²
Constraint: Σ b_i = B (budget), b_i ≥ 0

Analytical solution: b_i = (edge_i - μ) / (λ·σ_i²)
```

Lambda selection:

| Scenario | λ | Notes |
|:--|:--:|:--|
| Default | 2.0 | Balance return and risk |
| High confidence | 1.5 | Moderately aggressive |
| Low confidence | 3.0 | More diversified |
| All negative EV | 5.0 | Minimize loss |
| 3+ consecutive losing days | 5.0 | Stop-loss mode |

**After Markowitz/Kelly, always run Sporttery stake quantization.** Overseas books accept continuous amounts; 体彩 only accepts `票面金额 = 注数 × 2元 × 倍数`. Never output purchase advice as a bare decimal like `58.3元` without 注数/倍数.

### Stake Quantization (2元/注, mandatory for purchase output)

Official rule ([胜平负游戏规则](https://www.sporttery.cn/help/60333.html?gid=2)): **每注 2 元**; ticket face value = `注数 × 2元 × 倍数`; single ticket max **20,000 元**. Overseas staking is continuous — do not reuse overseas dollar amounts as 竞彩票面.

**Workflow (after Markowitz/Kelly, before ticket labeling):**

1. Compute ideal continuous amount `b_i` per option (reference only).
2. Set `ticket_count`: single selection = 1; 复式 = combination count (e.g. 2 options on one leg of 2串1 → 2注).
3. Run `quantize_stake(b_i, ticket_count)` or `quantize_budget(allocations, budget, ticket_counts)` from `scripts/kelly_engine.py`.
4. Output **注数 + 倍数 + 票面金额** for every line; optional `理想金额` for transparency.
5. If `unallocated_yuan > 0` (budget remainder &lt; 2元 step), say so — merge into top-EV item or leave unbet.
6. **Forbidden:** `建议买 73.5元` with no 注/倍; fractional yuan that cannot be ticketed.

**Preferred pattern for simple singles:** `1注 × 2元 × N倍 = 票面` (easy to enter in the App).

**复式 warning:** selecting multiple scores/options multiplies `注数` before multiplier — e.g. 3 score picks in one 2串1 leg = 3注 minimum = 6元 at 1倍.

| | 体彩竞彩 | 外盘 |
|:--|:--|:--|
| Min unit | 2元/注 | ~$1 or less, continuous |
| Amount formula | 注数 × 2 × 倍数 |任意金额 |
| Markowitz output | Must quantize | Can use as-is |

### Capital Preservation Strategy

When the user wants to maximize "break-even probability" within a budget:

```
Break-even condition: x₁·d₁ ≥ B and x₂·d₂ ≥ B
Solve: x₁ = B/d₁, x₂ = B/d₂, B_base = B/d₁ + B/d₂
Remainder: B_extra = B - B_base → bet on highest-odds option for upside
```

Applicable when: 1/d₁ + 1/d₂ < 1 (two outcomes' dewatered probabilities sum < 100%).

### Sporttery Rules (vs Overseas)

**Boundary rule:** Overseas odds (Asian handicap, O/U 2.5, DNB) are for **probability reference only**. Output tickets must use Sporttery play types (HAD/HHAD/CRS/TTG/HAFU) and pass `singleList` verification. Full对照表见 `references/sporttery-vs-overseas-rules.md`.

**Pre-ticket checklist (mandatory):**
1. `getMatchListV1` → which poolCodes are on sale (HAD may be missing entirely)
2. `getFixedBonusV1` → `singleList`: `single:1` = 可单关, `single:0` = 仅过关
3. If user asks for "Team X win" but HAD not sold → map to HHAD option and explain semantic difference
4. Label singles as **浮动奖金**, parlays as **固定奖金**
5. **Quantize every stake** to 注数 × 2元 × 倍数; total face value must match user budget in 2-yuan steps

### Parlay Rules

- Same-match different play types cannot be parlayed (illegal): ❌ Mexico HAD × Mexico TTG
- Cross-match parlay is legal: ✅ Mexico HAD × Korea TTG
- Barrel principle: max legs = lowest among included play types
- **All play types** (HAD/HHAD/CRS/TTG/HAFU) use **per-match** single availability (场次开放制) — HAD is NOT always single-eligible; verify `singleList` every match
- **Any single bet** = 浮动奖金; **any parlay** = 固定奖金 (not CRS-only)
- HAFU/BQC settlement uses **raw** HT/FT results — **not** handicap-adjusted
- Do **not** force into 2串1 when single is open — prefer singles for dispersion unless parlay EV clearly justifies it
- Score parlays have worst ROI (-85.7%), limit to ≤10% budget for upset fishing

### Bet Ticket Labeling

Every ticket must show:
1. Match number (周五001/002)
2. Full team names in Chinese (加拿大 ⚔ 波黑)
3. Play type name (胜平负/让球胜平负(-1)/比分/总进球/半全场)
4. Plain-language explanation (如"波黑不败" not just "让负")

## AgentKey Fallback Rule

When the user asks for sports data and `mcp_agentkey_find_tools` does not return a usable sports/odds/live-score tool, **do not keep retrying search**. Fall back immediately to the skill's own data sources:

1. `references/wc2026-corrected-schedule.md` for fixtures.
2. Sporttery API via direct curl for Chinese-market odds (`webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001` with `User-Agent` + `Referer`).
3. `references/data-source-availability.md` to decide whether a source is worth attempting at all.

AgentKey is great for general web/news retrieval, but it is **not a reliable discovery layer for niche sports APIs**. Treat an empty/low-relevance sports tool search as a signal to use the skill's internal pipeline, not as a blocker.

## Data Collection Pipeline

### Verified Data Sources

| Source | Status | Access | Notes |
|:--|:--:|:--|:--|
| Sporttery API | ✅ Verified 2026-06-14 | `webapi.sporttery.cn` curl direct | Mozilla UA + Referer, returns 22+ matches |
| 500.com main table | ✅ Verified | curl + gb2312 decode | Same system as Sporttery, redundant |
| worldcupwiki.com | ✅ Verified | browser_navigate + console | Only reliable public score source |
| WhoScored | ⚠️ One-shot | First curl 200, second 403 | Fetch everything in one request |
| Titan007 | ⚠️ Browser needed | Requires automation | 93-187 bookmaker odds |
| Wikipedia Elo | ❌ Unreliable | SSL fail + bad data | Germany 1496 vs actual ~1750 |
| zgzcw.com | ❌ 3-layer CloudWAF | Cannot bypass | Abandoned |
| TheSportsDB | ❌ 404 | National team API broken | |
| OddsPortal | ❌ 404 | No WC2026 page | |

Sporttery API caveat: `businessDate` is match local time, NOT Beijing time. A 03:00 BJT match (Europe time) is filed under the previous day. Query both dates and cross-verify with schedule.

### Sporttery API Quick Access

```text
GET https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001
Headers: User-Agent: Mozilla/5.0, Referer: https://www.sporttery.cn/
Returns: JSON with all selling matches, HAD + HHAD odds (some matches only have HHAD)
```

**⚠️ Not all matches offer HAD.** Some matches (e.g. Senegal vs Iraq, NZ vs Belgium on 6/27) only have HHAD in sale. Always check all poolCodes. See `references/sporttery-json-format.md` for full poolCode mapping and reliable parse code.

### Automated Monitoring

**Post-match results cron (local Mac crontab, not Hermes):** `scripts/setup_wc2026_cron.sh --install` registers `wc2026_results_sync.py` at **12:00 and 23:00** daily (BJT). **Auto-retires on 2026-07-20 after the 23:00 run** (`scripts/cron_expiry.py`); 2030 世界杯前手动 `--install` again. Manual backfill: `python3 scripts/wc2026_results_sync.py --from 20260611`. DB: `data/football_database.sqlite`.

Odds snapshot cron: `scripts/odds_snapshot_cron.py` runs every 2 hours, captures Sporttery odds into `odds_snapshots` SQLite table.

### International Data Collection (Non-Chinese Sources)

For matches where Sporttery/500.com data is insufficient or when collecting international standings, odds, weather, and lineup projections outside China:

**Reliable standings verification (2026-06-27 tested):**

ESPN standings page is the most reliable source for live group standings:
```python
# browser_navigate to https://www.espn.com/soccer/standings/_/league/fifa.world
# browser_console evaluate JavaScript to extract text:
#   document.body.innerText
# Returns all 12 groups with GP/W/D/L/F/A/GD/P for each team
# Parse by splitting on "Group X" headers
```

Use AgentKey `Surf/search-web` to gather:
- Current group standings and results (cross-verify across Yahoo Sports, CBS Sports, ESPN)
- Betting odds from multiple bookmakers (DraftKings, totalfootballanalysis, sportsgambler)
- Weather forecast for the venue (local NBC affiliates, Climate Central)
- Predicted lineups (SI.com, Yahoo Sports)
- Injury updates and team news

**⚠️ Known data source issues (2026-06-27):**
- Google search from Hermes browser → CAPTCHA blocked. Do not use.
- Bing search → poor result quality for sports standings. Do not use.
- AgentKey Surf/search-web → reliable but can disconnect mid-session. Capture critical data early.
- CBS Sports page → 60s timeout. Do not use.
- ESPN standings page → reliable, fast, extractable via console JS. **Preferred method.**

Workflow:
1. Verify match exists in `references/wc2026-corrected-schedule.md` and team names in `references/team-name-cn.md`
2. Query Sporttery API first (`getMatchListV1.qry?clientCode=3001`) — if match is listed, extract matchNum and businessDate
3. **Verify group standings via ESPN standings page** (preferred) or search "World Cup 2026 Group X standings" — cross-verify 2+ sources
4. Search "TeamA vs TeamB odds lineup weather" for match-specific data
5. Cross-verify key facts (score results, standings, odds) across 2+ sources before marking as `verified`
6. Run Elo → Poisson → Fusion model with collected data
7. Apply group stage incentive model using verified standings (MANDATORY: never assume both teams need points)
8. Mark web-sourced data with verification status in output

Pitfall: Sporttery API returns team names in Chinese only. Use `references/team-name-cn.md` to map before cross-referencing with English-language web search results.

## Handling User-Provided Screenshots

When the user sends a screenshot or photo of their lottery app (体彩竞彩界面), betting ticket, or 投注单:

**MANDATORY — do NOT substitute casual image reading for the skill workflow.** Native vision reads the pixels; this skill supplies the analysis framework (6 play types, EV, parlay risk, optimization).

1. **Load workflow references first** (if not already in context): `skill_view("world-cup-prediction")` and `skill_view("world-cup-prediction", "references/lottery-ticket-analysis.md")`. Skipping this produces shallow "I see your bet is X" instead of EV-based analysis.
2. **Use native multimodal vision to read the image.** Hermes' main model is vision-capable; Feishu and most chat platforms deliver attached images inline — read match numbers, teams, play types, selections, and odds directly without tool calls. Vision and skill workflow are complementary, not either/or.
3. **Run the ticket analysis pipeline** from `references/lottery-ticket-analysis.md`: extract options → model probability → EV per option → identify problems (all negative EV? too many parlays?) → optimization advice. Output structured analysis.
4. **Merge image + user text.** If the user also states constraints (available play types, parlay size, budget), combine both immediately — don't block on image verification.
5. **If the image is not visible** (rare on vision-capable models), ask once: "我看不清图片——能告诉我场次编号、对阵和赔率吗？" Do NOT spend more than 1-2 tool calls on workarounds.
6. **Never open the image in Preview and try cua-driver/computer_use capture.** This is expensive, unreliable (localized app names like 预览 break capture), and wastes 10+ tool calls. The image cache path (`~/.hermes/image_cache/`) is a local file — either the model sees it natively, or it doesn't; screen capture adds no value.
7. **Ask for specific missing data.** If odds, match numbers, or kick-off times are unclear from the image, ask one focused question.

Pitfall history: (a) agent spent 10+ cua-driver calls on Preview screen capture and never succeeded; (b) agent read the image natively via multimodal vision but skipped the skill entirely, frustrating the user who expected EV analysis and optimization advice.

## Post-Match Settlement Loop

After every match, run the full settlement → review → calibration cycle. Skipping settlement means wasting the bet data.

```
Final whistle → Per-ticket settlement (template: references/post-match-settlement.md)
              → Hit/miss reason analysis
              → Model accuracy validation (probability vs actual)
              → Elo update (K=30): new_elo = elo + 30*(actual_score - expected_score)
              → Data gap marking (S/A/B priority)
              → Lesson items appended
              → model_calibration table write
              → Calibration curve update (by confidence band)
              → Next-stage data supplement priority update
```

## Verified Pitfalls

57 verified pitfalls from real World Cup 2026 development. Full list in SKILL.md Pitfalls section above and module references. Key categories:

- **Model**: Poisson draw structural defect, Elo-xG uncorrelated (R²=0.0095), draw correction must scale with Elo gap
- **Data sources**: WhoScored second-request 403, 500.com gb2312 encoding, Sporttery date timezone offset
- **Betting**: Same-match parlay illegal; all play types per-match single eligibility (`singleList`); HAD may be unsold; never map overseas AH/O-U to Sporttery; HAFU not handicap-adjusted; score parlay worst ROI (-85.7%); **2元/注** — Markowitz amounts must be quantized via `quantize_stake` before purchase output (overseas continuous stakes invalid on Sporttery)
- **Scraping**: 3 regex failures → change approach, zgzcw 3-layer WAF impassable, Wikipedia Elo unreliable

## Module Navigation

Use these bundled files for detailed implementation guidance:

### Modules (`modules/`)
- `data-collection.md` — Data collection methods (500.com/Sporttery/Titan007 URL patterns + parsing)
- `model-engine.md` — Elo + Poisson + xG + GBM + Monte Carlo engine details
- `odds-analysis.md` — Odds/value analysis; overseas AH/O-U for reference only, map to Sporttery plays for tickets
- `backtest.md` — Backtest framework + calibration curves
- `betting-strategy.md` — Mean-variance optimization + 6 play-type rules
- `report-generation.md` — Chinese report formatting + visualization
- `validation.md` — Hypothesis testing, feature effectiveness, methodology audit

### Key References (`references/`)
- `elo-calibration-20260614.md` — 48-team calibrated Elo table (incl. 2026-06-27 supplemental estimates for 9 previously-missing teams)
- `poisson-lambda-solver-v2.md` — Poisson λ reverse algorithm (Newton iteration)
- `backtest-results-v6.md` — v6.0 full backtest results
- `sporttery-vs-overseas-rules.md` — **体彩 vs 外盘规则分界（出票前必读）**
- `complete-betting-rules.md` — Complete lottery betting rules
- `card-layout-standard.md` — Report card layout standard
- `team-name-cn.md` — 48-team Chinese-English name mapping
- `wc2026-corrected-schedule.md` — Full 72-match schedule (Beijing time)
- `venue-environment.md` — 16 venue altitude/temperature/precipitation data
- `weak-home-strong-away-strategy.md` — Weak home vs strong away betting strategy
- `post-match-settlement.md` — Post-match settlement template
- `data-source-availability.md` — Data source availability status table
- `sporttery-json-format.md` — Sporttery API JSON format + poolCode mapping (updated 2026-06-27 with HAD-not-available finding and reliable parse code)
- `multi-match-budget-allocation.md` — Multi-match budget allocation workflow (Step-by-step: verify odds → verify standings → model → incentive → EV sort → Markowitz → output)
- `upgrades-v7-20260614.md` — 7 model upgrades overview (Kelly, multi-bookmaker, movement, snapshot, age-peak, hot-trap, settlement)
- `merge-history-20260626.md` — Merge history: how this skill was combined from Hermes decision framework + feibang191 GitHub quantitative engine
- `merge-history-20260626.md` — Merge history: how this skill was combined from Hermes decision framework + feibang191 GitHub quantitative engine

### Config (`config/`)
- `calibrated-model.json` — Calibrated model parameters (weights, thresholds, backtest seasons)

### Sample Data (`sample_data/`)
- `football_database_sample.sqlite` — Anonymized database (20 tables, 54+ matches)
- `schema.sql` — Table creation SQL
