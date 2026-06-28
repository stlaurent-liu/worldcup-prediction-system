#!/usr/bin/env python3
"""Smoke tests: openfootball cross-validation + knockout_engine."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from knockout_engine import (
    canonical_team_key,
    get_team_absences,
    knockout_match_probs,
    penalty_shootout_win_prob,
    resolve_knockout_winner,
)
from openfootball_parser import cross_validate, index_matches, load_openfootball_matches


def test_openfootball_parser():
    matches = load_openfootball_matches()
    assert len(matches) >= 60, f"expected >=60 group matches, got {len(matches)}"
    idx = index_matches(matches)
    assert len(idx) == len(matches)
    sample = matches[0]
    assert sample.home_goals >= 0 and sample.away_goals >= 0
    print(f"  openfootball: {len(matches)} matches parsed OK")


def test_cross_validate():
    matches = load_openfootball_matches()
    idx = index_matches(matches)
    m = matches[0]
    ok = cross_validate(m.home_espn, m.away_espn, m.score, idx)
    assert ok["status"] == "match"
    bad = cross_validate(m.home_espn, m.away_espn, "99-99", idx)
    assert bad["status"] == "mismatch"
    assert bad["authoritative_score"] == m.score
    missing = cross_validate("Atlantis", "Narnia", "1-0", idx)
    assert missing["status"] == "espn_only"
    print("  cross_validate: match/mismatch/espn_only OK")


def test_knockout_engine():
    pk = penalty_shootout_win_prob(1820, 1500)
    assert 0.5 < pk < 0.52, f"stronger team PK edge expected, got {pk}"

    info = knockout_match_probs("France", "Argentina", 1820, 1800)
    assert info["base"]["p_advance"] > 0.45
    assert 0 < info["adjusted"]["p_pk_win_if_draw"] < 1

    wins = {resolve_knockout_winner("France", "Senegal", 1820, 1580) for _ in range(50)}
    assert "France" in wins
    print("  knockout_engine: PK + advance probs OK")


def test_absence_cn_en_lookup():
    assert canonical_team_key("法国") == "France"
    assert canonical_team_key("France") == "France"
    # squad_absences.json uses Chinese keys; lookup via English must work
    absences = get_team_absences("France")
    assert isinstance(absences, list)
    print("  absence CN/EN lookup OK")


def main():
    print("[test_knockout_openfootball]")
    test_openfootball_parser()
    test_cross_validate()
    test_knockout_engine()
    test_absence_cn_en_lookup()
    print("[all passed]")


if __name__ == "__main__":
    main()