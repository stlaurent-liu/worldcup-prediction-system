# World Cup Prediction Data Sources

Use these sources as a practical starting point. Prefer official or API-backed data over scraped pages. Do not hard-code secrets in this skill; read API keys from environment variables.

## Official Match Data

- FIFA match centre: fixtures, venue, kickoff time, match centre, team pages, official articles, and published lineups when available.
- FIFA World Cup 26 regulations: competition rules, start-list timing, match operations, and tournament procedures.
- Team federation sites and verified team social accounts: confirmed injuries, suspensions, squad news, and press conference quotes.

Use official data for `verified` fields whenever possible.

## Odds And Market Data

Primary API option:

- The Odds API: `https://api.the-odds-api.com/v4/`
- Sport key used in testing: `soccer_fifa_world_cup`
- Useful markets: `h2h`, `spreads`, `totals`
- Useful regions: `us`, `uk`, `eu`, `au`
- Recommended odds format: `decimal`
- Environment variable: `THE_ODDS_API_KEY`

Example request shape:

```text
GET https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/
  ?regions=us,uk,eu,au
  &markets=h2h,spreads,totals
  &oddsFormat=decimal
  &dateFormat=iso
  &apiKey=$THE_ODDS_API_KEY
```

Use the response headers to monitor quota:

- `x-requests-remaining`
- `x-requests-used`
- `x-requests-last`

For a free plan, avoid high-frequency polling. For a single match, recommended checkpoints are:

- Current time when the user asks
- T-6h
- T-90m to T-60m after lineups
- T-15m to T-5m final check

If historical odds are unavailable on the plan, store each snapshot locally to create a market timeline.

Do not treat odds as truth. Convert odds to market-implied probability and compare with the model after uncertainty and bookmaker margin.

## Weather And Environment

Suggested APIs:

- Open-Meteo Forecast API: hourly temperature, humidity, precipitation, wind, and weather codes.
- National or local weather services when available for radar and severe-weather warnings.
- Stadium location metadata for latitude, longitude, roof status, altitude, and travel considerations.

For 2026 North American matches, explicitly check:

- Temperature
- Humidity
- Thunderstorm probability or severe-weather warnings
- Wind speed
- Hydration-break impact
- Pitch or roof condition when known
- Travel distance and rest differential

Classify weather as `forecast`, `current`, or `late_random` depending on timing.

## Football Data APIs

Potential providers for fixtures, squads, standings, lineups, live events, and live stats:

- API-Football / API-SPORTS
- Sportmonks
- football-data.org
- Stats Perform, Opta, or other professional providers if available

Check each provider's World Cup coverage, latency, quota, and license before relying on it. If live xG or shot-quality data is unavailable, lower in-play confidence and use observable events only.

## News, Injuries, And Coach Context

Use multiple sources and classify confidence:

- Official federation/team updates: `confirmed`
- Press conference quotes from reputable outlets: `verified` or `current`
- Reputable beat reporters: `current` or `rumor_or_unverified`
- Generic previews: useful context, but avoid treating predicted XIs as confirmed lineups

Track coach and group-stage incentives:

- Must-win vs draw-is-enough
- Goal-difference pressure
- Rotation likelihood
- Core-player protection
- Conservative lead behavior
- Big-win tendency

## User-Provided Data

Some important data is account-specific and cannot be reliably fetched publicly:

- User's actual entry market and entry odds
- Platform cashout offer
- Platform-specific rules and limits
- Whether the user can watch live
- Declared test amount or personal spending constraint

For cashout decisions, require the current platform offer. Without it, return `need_cashout_offer`.

## Data Quality Labels

Use these labels in output:

- `verified`: official or highly reliable.
- `manual`: supplied by the user or manually captured.
- `inferred`: model-derived from context.
- `missing`: unavailable.
- `forecast`: known but not final.
- `current`: latest checked value.
- `confirmed`: official or reliable enough to drive a decision.
- `rumor_or_unverified`: not decision-grade without cross-checking.
- `late_random`: cannot be known until close to kickoff or during play.