#!/usr/bin/env python3
"""Parse openfootball/worldcup Football.TXT (CC0) for fixtures and results."""
from __future__ import annotations

import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

OPENFOOTBALL_CUP_URL = (
    "https://raw.githubusercontent.com/openfootball/worldcup/master/2026--usa/cup.txt"
)

# openfootball display name → ESPN-style key (for EN_TO_CN lookup)
OF_NAME_TO_ESPN: Dict[str, str] = {
    "South Korea": "South Korea",
    "Czech Republic": "Czechia",
    "Bosnia & Herzegovina": "Bosnia-Herzegovina",
    "Ivory Coast": "Ivory Coast",
    "DR Congo": "DR Congo",
    "Cape Verde": "Cape Verde",
    "Turkey": "Türkiye",
    "USA": "United States",
    "Curaçao": "Curaçao",
    "IR Iran": "Iran",
    "Korea Republic": "South Korea",
    "Czechia": "Czechia",
    "Congo DR": "DR Congo",
    "Côte d'Ivoire": "Ivory Coast",
    "Cabo Verde": "Cape Verde",
    "Türkiye": "Türkiye",
}

MONTH_MAP = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

MATCH_LINE_RE = re.compile(
    r"^\s*\d{1,2}:\d{2}\s+UTC[^\s]+\s+"
    r"(?P<home>.+?)\s+"
    r"(?P<score>\d+-\d+)\s*"
    r"(?:\([^)]+\))?\s*"
    r"(?P<away>.+?)\s+@\s+"
)

DATE_LINE_RE = re.compile(
    r"^(?P<dow>\w+)\s+(?P<month>\w+)\s+(?P<day>\d{1,2})\s*$", re.I
)
GROUP_LINE_RE = re.compile(r"^▪\s*Group\s+(?P<grp>[A-L])\s*$", re.I)


@dataclass
class OpenFootballMatch:
    home_of: str
    away_of: str
    home_espn: str
    away_espn: str
    score: str
    home_goals: int
    away_goals: int
    group_name: Optional[str]
    match_date: Optional[str]  # YYYYMMDD
    source_line: str


def fetch_cup_text(url: str = OPENFOOTBALL_CUP_URL) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return resp.read().decode("utf-8")


def of_to_espn(name: str) -> str:
    name = name.strip()
    return OF_NAME_TO_ESPN.get(name, name)


def parse_score(score: str) -> Tuple[int, int]:
    a, b = score.split("-", 1)
    return int(a), int(b)


def parse_cup_text(text: str, year: int = 2026) -> List[OpenFootballMatch]:
    current_group: Optional[str] = None
    current_date: Optional[str] = None
    out: List[OpenFootballMatch] = []

    for raw in text.splitlines():
        line = raw.rstrip()
        gm = GROUP_LINE_RE.match(line)
        if gm:
            current_group = gm.group("grp").upper()
            continue
        dm = DATE_LINE_RE.match(line)
        if dm:
            month = MONTH_MAP.get(dm.group("month").capitalize())
            if month:
                current_date = f"{year}{month:02d}{int(dm.group('day')):02d}"
            continue
        mm = MATCH_LINE_RE.match(line)
        if not mm:
            continue
        home_of = mm.group("home").strip()
        away_of = mm.group("away").strip()
        score = mm.group("score").strip()
        hg, ag = parse_score(score)
        out.append(
            OpenFootballMatch(
                home_of=home_of,
                away_of=away_of,
                home_espn=of_to_espn(home_of),
                away_espn=of_to_espn(away_of),
                score=score,
                home_goals=hg,
                away_goals=ag,
                group_name=current_group,
                match_date=current_date,
                source_line=line.strip(),
            )
        )
    return out


def load_openfootball_matches(url: str = OPENFOOTBALL_CUP_URL) -> List[OpenFootballMatch]:
    return parse_cup_text(fetch_cup_text(url))


def match_key(home_espn: str, away_espn: str) -> str:
    return f"{home_espn}|{away_espn}"


def index_matches(matches: List[OpenFootballMatch]) -> Dict[str, OpenFootballMatch]:
    idx: Dict[str, OpenFootballMatch] = {}
    for m in matches:
        idx[match_key(m.home_espn, m.away_espn)] = m
    return idx


def cross_validate(
    espn_home_en: str,
    espn_away_en: str,
    espn_score: str,
    of_index: Dict[str, OpenFootballMatch],
) -> dict:
    key = match_key(espn_home_en, espn_away_en)
    ofm = of_index.get(key)
    if not ofm:
        return {
            "status": "espn_only",
            "openfootball_score": None,
            "authoritative_score": espn_score,
            "message": "openfootball 未收录该场",
        }
    if ofm.score == espn_score:
        return {
            "status": "match",
            "openfootball_score": ofm.score,
            "authoritative_score": ofm.score,
            "message": None,
        }
    return {
        "status": "mismatch",
        "openfootball_score": ofm.score,
        "authoritative_score": ofm.score,
        "message": f"ESPN {espn_score} vs openfootball {ofm.score}，采用 openfootball",
    }


if __name__ == "__main__":
    ms = load_openfootball_matches()
    print(f"parsed {len(ms)} matches from openfootball")
    for m in ms[:5]:
        print(m.match_date, m.home_of, m.score, m.away_of, f"Group {m.group_name}")