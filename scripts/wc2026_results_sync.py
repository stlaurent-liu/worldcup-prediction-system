#!/usr/bin/env python3
"""世界杯 2026 赛后赛果同步：ESPN → SQLite + 动机标签 + 加权 Elo 更新。

每日 cron 调用；也可手动: python3 wc2026_results_sync.py [--from YYYYMMDD] [--to YYYYMMDD]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from cron_expiry import TOURNAMENT_CRON_LAST_DAY, guard_cron_at_start, maybe_retire_cron_after_run
from db_path import get_db_path

ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={date}"
)
ESPN_STANDINGS = "https://site.api.espn.com/apis/v2/sports/soccer/fifa.world/standings"
K_FACTOR = 30
TOURNAMENT_START = datetime(2026, 6, 11)
DEFAULT_END = datetime(2026, 7, 20)

# ESPN displayName → 竞彩/赛程库中文队名
EN_TO_CN: Dict[str, str] = {
    "Mexico": "墨西哥",
    "South Africa": "南非",
    "South Korea": "韩国",
    "Korea Republic": "韩国",
    "Czechia": "捷克",
    "Czech Republic": "捷克",
    "Canada": "加拿大",
    "Bosnia-Herzegovina": "波黑",
    "Bosnia and Herzegovina": "波黑",
    "United States": "美国",
    "USA": "美国",
    "Paraguay": "巴拉圭",
    "Qatar": "卡塔尔",
    "Switzerland": "瑞士",
    "Brazil": "巴西",
    "Morocco": "摩洛哥",
    "Haiti": "海地",
    "Scotland": "苏格兰",
    "Australia": "澳大利亚",
    "Türkiye": "土耳其",
    "Turkey": "土耳其",
    "Germany": "德国",
    "Curaçao": "库拉索",
    "Curacao": "库拉索",
    "Netherlands": "荷兰",
    "Japan": "日本",
    "Ivory Coast": "科特迪瓦",
    "Côte d'Ivoire": "科特迪瓦",
    "Ecuador": "厄瓜多尔",
    "Sweden": "瑞典",
    "Tunisia": "突尼斯",
    "Spain": "西班牙",
    "Cape Verde": "佛得角",
    "Belgium": "比利时",
    "Egypt": "埃及",
    "Saudi Arabia": "沙特阿拉伯",
    "Uruguay": "乌拉圭",
    "Iran": "伊朗",
    "New Zealand": "新西兰",
    "France": "法国",
    "Senegal": "塞内加尔",
    "Norway": "挪威",
    "Argentina": "阿根廷",
    "Austria": "奥地利",
    "Jordan": "约旦",
    "England": "英格兰",
    "Panama": "巴拿马",
    "Ghana": "加纳",
    "Croatia": "克罗地亚",
    "Portugal": "葡萄牙",
    "Colombia": "哥伦比亚",
    "Uzbekistan": "乌兹别克斯坦",
    "DR Congo": "刚果(金)",
    "Congo DR": "刚果(金)",
    "Democratic Republic of Congo": "刚果(金)",
    "Algeria": "阿尔及利亚",
    "Iraq": "伊拉克",
}

OBJECTIVE_ELO_WEIGHT = {
    "must_win": 1.0,
    "goal_difference_push": 1.0,
    "statement_win": 0.9,
    "professional_control": 0.7,
    "draw_acceptable": 0.5,
    "avoid_loss_enough": 0.5,
    "already_qualified": 0.2,
    "rotation_preservation": 0.2,
    "unknown": 0.6,
}

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS wc2026_match_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    espn_event_id TEXT,
    match_date TEXT NOT NULL,
    group_name TEXT,
    round_num INTEGER,
    home_team_cn TEXT NOT NULL,
    away_team_cn TEXT NOT NULL,
    home_team_en TEXT,
    away_team_en TEXT,
    home_score INTEGER,
    away_score INTEGER,
    score TEXT,
    result TEXT,
    home_objective TEXT,
    away_objective TEXT,
    game_management_mode TEXT,
    elo_update_weight_home REAL,
    elo_update_weight_away REAL,
    home_elo_before REAL,
    away_elo_before REAL,
    home_elo_after REAL,
    away_elo_after REAL,
    synced_at TEXT,
    source TEXT DEFAULT 'espn',
    notes TEXT,
    UNIQUE(match_date, home_team_cn, away_team_cn)
);

CREATE TABLE IF NOT EXISTS wc2026_sync_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TEXT,
    date_from TEXT,
    date_to TEXT,
    matches_fetched INTEGER,
    matches_updated INTEGER,
    elo_teams_updated INTEGER,
    status TEXT,
    message TEXT
);

CREATE TABLE IF NOT EXISTS wc2026_elo_baseline (
    team_name TEXT PRIMARY KEY,
    elo_rating REAL NOT NULL,
    captured_at TEXT
);
"""


def fetch_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    conn.commit()


def ensure_elo_baseline(conn: sqlite3.Connection) -> None:
    n = conn.execute("SELECT COUNT(*) FROM wc2026_elo_baseline").fetchone()[0]
    if n > 0:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for name, rating in conn.execute(
        "SELECT team_name, elo_rating FROM worldcup_teams WHERE elo_rating IS NOT NULL"
    ):
        conn.execute(
            "INSERT OR IGNORE INTO wc2026_elo_baseline (team_name, elo_rating, captured_at) VALUES (?,?,?)",
            (name, float(rating), now),
        )
    conn.commit()


def team_round(team: str, group: str, match_date: str, records: List[dict]) -> int:
    played = sum(
        1
        for r in records
        if r.get("group_name") == group
        and r["match_date"] < match_date
        and team in (r["home_team_cn"], r["away_team_cn"])
    )
    return min(3, played + 1)


def load_team_groups(conn: sqlite3.Connection) -> Dict[str, str]:
    groups: Dict[str, str] = {}
    for home, away, grp in conn.execute(
        "SELECT home_team, away_team, group_name FROM worldcup_schedule"
    ):
        if grp:
            groups[home] = grp
            groups[away] = grp
    try:
        data = fetch_json(ESPN_STANDINGS)
        for child in data.get("children", []):
            abbr = (child.get("abbreviation") or "").replace("Group ", "").strip()
            for entry in child.get("standings", {}).get("entries", []):
                en = entry["team"]["displayName"]
                cn = EN_TO_CN.get(en, en)
                if abbr:
                    groups[cn] = abbr
    except Exception as exc:
        print(f"[warn] standings fetch failed: {exc}")
    return groups


def load_elo(conn: sqlite3.Connection) -> Dict[str, float]:
    elo: Dict[str, float] = {}
    for name, rating in conn.execute(
        "SELECT team_name, elo_rating FROM worldcup_teams WHERE elo_rating IS NOT NULL"
    ):
        elo[name] = float(rating)
    for name, rating in conn.execute(
        "SELECT team_name, elo_rating FROM team_stats WHERE elo_rating IS NOT NULL"
    ):
        elo.setdefault(name, float(rating))
    return elo


def expected_score(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400))


def actual_score(home_goals: int, away_goals: int) -> Tuple[float, float]:
    if home_goals > away_goals:
        return 1.0, 0.0
    if home_goals < away_goals:
        return 0.0, 1.0
    return 0.5, 0.5


def blowout_cap(home_goals: int, away_goals: int) -> float:
    """大胜弱队时降低 Elo 更新幅度，避免虚高。"""
    margin = abs(home_goals - away_goals)
    if margin >= 5:
        return 0.5
    if margin >= 4:
        return 0.65
    if margin >= 3:
        return 0.8
    return 1.0


def group_standings(
    group: str, before_date: str, records: List[dict]
) -> Dict[str, dict]:
    table: Dict[str, dict] = {}
    for r in records:
        if r.get("group_name") != group:
            continue
        if r["match_date"] >= before_date:
            continue
        for side in ("home", "away"):
            team = r[f"{side}_team_cn"]
            gf = r["home_score"] if side == "home" else r["away_score"]
            ga = r["away_score"] if side == "home" else r["home_score"]
            if team not in table:
                table[team] = {"pts": 0, "gd": 0, "gf": 0, "played": 0}
            table[team]["played"] += 1
            table[team]["gf"] += gf
            table[team]["gd"] += gf - ga
            if gf > ga:
                table[team]["pts"] += 3
            elif gf == ga:
                table[team]["pts"] += 1
    return table


def classify_objective(
    team: str, group: str, match_date: str, records: List[dict], round_num: int
) -> str:
    st = group_standings(group, match_date, records).get(
        team, {"pts": 0, "gd": 0, "gf": 0, "played": 0}
    )
    pts, played = st["pts"], st["played"]
    remaining = max(0, 3 - played)

    if round_num >= 3 or played >= 2:
        if pts >= 7:
            return "already_qualified"
        if pts >= 6 and remaining <= 1:
            return "rotation_preservation"
        if pts >= 4 and remaining <= 1:
            return "draw_acceptable"
        if pts <= 2 and remaining <= 1:
            return "must_win"
        if st["gd"] < 0 and remaining <= 1:
            return "goal_difference_push"

    if round_num == 1:
        return "must_win"
    if pts <= 1:
        return "must_win"
    if pts >= 6:
        return "professional_control"
    return "professional_control"


def game_management(home_obj: str, away_obj: str) -> str:
    objs = {home_obj, away_obj}
    if "already_qualified" in objs or "rotation_preservation" in objs:
        return "rotation_preservation"
    if "draw_acceptable" in objs or "avoid_loss_enough" in objs:
        return "draw_acceptable"
    if "goal_difference_push" in objs or "statement_win" in objs:
        return "goal_difference_push"
    if "must_win" in objs:
        return "statement_win"
    return "professional_control"


def parse_completed_events(date_str: str) -> List[dict]:
    data = fetch_json(ESPN_SCOREBOARD.format(date=date_str))
    out = []
    for event in data.get("events", []):
        status = event.get("status", {}).get("type", {})
        if status.get("name") != "STATUS_FULL_TIME":
            continue
        comp = event["competitions"][0]
        teams = {t["homeAway"]: t for t in comp["competitors"]}
        home_en = teams["home"]["team"]["displayName"]
        away_en = teams["away"]["team"]["displayName"]
        home_cn = EN_TO_CN.get(home_en)
        away_cn = EN_TO_CN.get(away_en)
        if not home_cn or not away_cn:
            print(f"[skip] unmapped teams: {home_en} vs {away_en}")
            continue
        hg = int(teams["home"].get("score") or 0)
        ag = int(teams["away"].get("score") or 0)
        out.append(
            {
                "espn_event_id": str(event.get("id", "")),
                "match_date": date_str,
                "home_team_en": home_en,
                "away_team_en": away_en,
                "home_team_cn": home_cn,
                "away_team_cn": away_cn,
                "home_score": hg,
                "away_score": ag,
                "score": f"{hg}-{ag}",
            }
        )
    return out


def format_match_time(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y%m%d")
    return dt.strftime("%m-%d") + " 00:00"


def sync(
    conn: sqlite3.Connection,
    date_from: datetime,
    date_to: datetime,
    dry_run: bool = False,
) -> dict:
    ensure_schema(conn)
    team_groups = load_team_groups(conn)

    existing_rows = []
    for row in conn.execute(
        """SELECT match_date, group_name, home_team_cn, away_team_cn,
                  home_score, away_score, round_num
           FROM wc2026_match_records ORDER BY match_date"""
    ):
        existing_rows.append(
            {
                "match_date": row[0],
                "group_name": row[1],
                "home_team_cn": row[2],
                "away_team_cn": row[3],
                "home_score": row[4],
                "away_score": row[5],
                "round_num": row[6],
            }
        )

    fetched: List[dict] = []
    cur = date_from
    while cur <= date_to:
        d = cur.strftime("%Y%m%d")
        try:
            fetched.extend(parse_completed_events(d))
        except Exception as exc:
            print(f"[warn] {d}: {exc}")
        cur += timedelta(days=1)

    fetched.sort(key=lambda x: (x["match_date"], x["home_team_cn"]))
    updated = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    all_records = list(existing_rows)

    for m in fetched:
        grp = team_groups.get(m["home_team_cn"]) or team_groups.get(m["away_team_cn"]) or ""
        m["group_name"] = grp
        m["round_num"] = team_round(m["home_team_cn"], grp, m["match_date"], all_records)

        home_obj = (
            classify_objective(
                m["home_team_cn"], grp, m["match_date"], all_records, m["round_num"]
            )
            if grp
            else "unknown"
        )
        away_obj = (
            classify_objective(
                m["away_team_cn"], grp, m["match_date"], all_records, m["round_num"]
            )
            if grp
            else "unknown"
        )
        gm = game_management(home_obj, away_obj)
        w_home = OBJECTIVE_ELO_WEIGHT.get(home_obj, 0.6)
        w_away = OBJECTIVE_ELO_WEIGHT.get(away_obj, 0.6)
        w_home *= blowout_cap(m["home_score"], m["away_score"])
        w_away *= blowout_cap(m["home_score"], m["away_score"])

        if m["home_score"] > m["away_score"]:
            result = "H"
        elif m["home_score"] < m["away_score"]:
            result = "A"
        else:
            result = "D"

        notes = []
        if gm == "rotation_preservation":
            notes.append("控分/轮换风险场次，Elo已降权")
        if blowout_cap(m["home_score"], m["away_score"]) < 1.0:
            notes.append("大胜弱队，Elo更新已封顶")

        m.update(
            {
                "home_objective": home_obj,
                "away_objective": away_obj,
                "game_management_mode": gm,
                "elo_update_weight_home": round(w_home, 3),
                "elo_update_weight_away": round(w_away, 3),
                "result": result,
                "synced_at": now,
                "notes": "; ".join(notes) if notes else None,
            }
        )

        if dry_run:
            print(
                f"{m['match_date']} {m['home_team_cn']} {m['score']} {m['away_team_cn']} "
                f"[{gm}] {home_obj}/{away_obj}"
            )
            all_records.append(m)
            updated += 1
            continue

        conn.execute(
            """
            INSERT INTO wc2026_match_records (
                espn_event_id, match_date, group_name, round_num,
                home_team_cn, away_team_cn, home_team_en, away_team_en,
                home_score, away_score, score, result,
                home_objective, away_objective, game_management_mode,
                elo_update_weight_home, elo_update_weight_away,
                home_elo_before, away_elo_before, home_elo_after, away_elo_after,
                synced_at, notes
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(match_date, home_team_cn, away_team_cn) DO UPDATE SET
                espn_event_id=excluded.espn_event_id,
                group_name=excluded.group_name,
                round_num=excluded.round_num,
                home_score=excluded.home_score,
                away_score=excluded.away_score,
                score=excluded.score,
                result=excluded.result,
                home_objective=excluded.home_objective,
                away_objective=excluded.away_objective,
                game_management_mode=excluded.game_management_mode,
                elo_update_weight_home=excluded.elo_update_weight_home,
                elo_update_weight_away=excluded.elo_update_weight_away,
                home_elo_before=excluded.home_elo_before,
                away_elo_before=excluded.away_elo_before,
                home_elo_after=excluded.home_elo_after,
                away_elo_after=excluded.away_elo_after,
                synced_at=excluded.synced_at,
                notes=excluded.notes
            """,
            (
                m["espn_event_id"],
                m["match_date"],
                m["group_name"],
                m["round_num"],
                m["home_team_cn"],
                m["away_team_cn"],
                m["home_team_en"],
                m["away_team_en"],
                m["home_score"],
                m["away_score"],
                m["score"],
                m["result"],
                m["home_objective"],
                m["away_objective"],
                m["game_management_mode"],
                m["elo_update_weight_home"],
                m["elo_update_weight_away"],
                None,
                None,
                None,
                None,
                m["synced_at"],
                m["notes"],
            ),
        )

        conn.execute(
            """
            UPDATE worldcup_schedule
            SET score=?, status='completed'
            WHERE home_team=? AND away_team=?
            """,
            (m["score"], m["home_team_cn"], m["away_team_cn"]),
        )

        all_records.append(m)
        updated += 1

    elo_changed: set = set()
    if not dry_run and updated > 0:
        ensure_elo_baseline(conn)
        elo = {
            name: float(rating)
            for name, rating in conn.execute(
                "SELECT team_name, elo_rating FROM wc2026_elo_baseline"
            )
        }
        for name, rating in conn.execute(
            "SELECT team_name, elo_rating FROM worldcup_teams WHERE elo_rating IS NOT NULL"
        ):
            elo.setdefault(name, float(rating))

        all_db = conn.execute(
            """SELECT match_date, home_team_cn, away_team_cn, home_score, away_score,
                      home_objective, away_objective, game_management_mode
               FROM wc2026_match_records ORDER BY match_date, home_team_cn"""
        ).fetchall()

        for row in all_db:
            h_cn, a_cn = row[1], row[2]
            hg, ag = row[3], row[4]
            w_h = OBJECTIVE_ELO_WEIGHT.get(row[5], 0.6) * blowout_cap(hg, ag)
            w_a = OBJECTIVE_ELO_WEIGHT.get(row[6], 0.6) * blowout_cap(hg, ag)
            h_elo = elo.get(h_cn, 1500.0)
            a_elo = elo.get(a_cn, 1500.0)
            exp_h = expected_score(h_elo, a_elo)
            act_h, act_a = actual_score(hg, ag)
            new_h = h_elo + K_FACTOR * w_h * (act_h - exp_h)
            new_a = a_elo + K_FACTOR * w_a * (act_a - (1.0 - exp_h))
            elo[h_cn] = new_h
            elo[a_cn] = new_a
            conn.execute(
                """UPDATE wc2026_match_records
                   SET home_elo_before=?, away_elo_before=?,
                       home_elo_after=?, away_elo_after=?
                   WHERE match_date=? AND home_team_cn=? AND away_team_cn=?""",
                (
                    round(h_elo, 1),
                    round(a_elo, 1),
                    round(new_h, 1),
                    round(new_a, 1),
                    row[0],
                    h_cn,
                    a_cn,
                ),
            )
            elo_changed.add(h_cn)
            elo_changed.add(a_cn)

        for team, rating in elo.items():
            conn.execute(
                "UPDATE worldcup_teams SET elo_rating=? WHERE team_name=?",
                (round(rating, 1), team),
            )
            conn.execute(
                """
                INSERT INTO team_stats (team_name, elo_rating, elo_updated)
                VALUES (?, ?, datetime('now','+8 hours'))
                ON CONFLICT(team_name) DO UPDATE SET
                    elo_rating=excluded.elo_rating,
                    elo_updated=excluded.elo_updated
                """,
                (round(rating, 1), team),
            )

        conn.execute(
            """
            INSERT INTO wc2026_sync_log
            (run_at, date_from, date_to, matches_fetched, matches_updated,
             elo_teams_updated, status, message)
            VALUES (?,?,?,?,?,?,?,?)
            """,
            (
                now,
                date_from.strftime("%Y%m%d"),
                date_to.strftime("%Y%m%d"),
                len(fetched),
                updated,
                len(elo_changed),
                "ok",
                f"synced {updated} matches",
            ),
        )
        conn.commit()

    return {
        "fetched": len(fetched),
        "updated": updated,
        "elo_teams": len(elo_changed),
    }


def main() -> None:
    guard_cron_at_start("wc2026_results_sync")
    parser = argparse.ArgumentParser(description="Sync WC2026 results from ESPN")
    parser.add_argument("--from", dest="date_from", default=None, help="YYYYMMDD")
    parser.add_argument("--to", dest="date_to", default=None, help="YYYYMMDD")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    today = datetime.now()
    date_to = datetime.strptime(args.date_to, "%Y%m%d") if args.date_to else today
    if args.date_from:
        date_from = datetime.strptime(args.date_from, "%Y%m%d")
    else:
        # 默认拉最近 3 天（cron 每日跑）+ 全量回溯用 --from 20260611
        date_from = max(TOURNAMENT_START, date_to - timedelta(days=3))

    db = get_db_path()
    print(f"[wc2026_results_sync] db={db}")
    print(f"[wc2026_results_sync] range {date_from.date()} → {date_to.date()}")

    conn = sqlite3.connect(db)
    try:
        summary = sync(conn, date_from, date_to, dry_run=args.dry_run)
        print(
            f"[done] fetched={summary['fetched']} updated={summary['updated']} "
            f"elo_teams={summary['elo_teams']}"
        )
        print(f"[cron] auto-retire after {TOURNAMENT_CRON_LAST_DAY} 23:00 run")
    finally:
        conn.close()
    maybe_retire_cron_after_run("wc2026_results_sync")


if __name__ == "__main__":
    main()