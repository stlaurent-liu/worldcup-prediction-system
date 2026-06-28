#!/usr/bin/env python3
"""体彩 + 外盘双源赔率交叉对比
- Sporttery API: 竞彩 HAD / HHAD + singleList 单关/仅过关
- The Odds API: Pinnacle 优先，辅以百家均值去水
- 输出: JSON + 终端对照表 + 外盘偏差 → 竞彩可买映射

规则口径: references/sporttery-vs-overseas-rules.md
"""
from __future__ import annotations

import json
import os
import ssl
import statistics
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"

TEAM_CN_TO_EN = {
    "墨西哥": "Mexico",
    "南非": "South Africa",
    "韩国": "South Korea",
    "捷克": "Czech Republic",
    "加拿大": "Canada",
    "波黑": "Bosnia",
    "卡塔尔": "Qatar",
    "瑞士": "Switzerland",
    "巴西": "Brazil",
    "摩洛哥": "Morocco",
    "海地": "Haiti",
    "苏格兰": "Scotland",
    "土耳其": "Turkey",
    "巴拉圭": "Paraguay",
    "澳大利亚": "Australia",
    "美国": "USA",
    "厄瓜多尔": "Ecuador",
    "库拉索": "Curaçao",
    "德国": "Germany",
    "科特迪瓦": "Ivory Coast",
    "日本": "Japan",
    "瑞典": "Sweden",
    "突尼斯": "Tunisia",
    "荷兰": "Netherlands",
    "伊朗": "Iran",
    "埃及": "Egypt",
    "新西兰": "New Zealand",
    "比利时": "Belgium",
    "西班牙": "Spain",
    "佛得角": "Cape Verde",
    "沙特": "Saudi Arabia",
    "沙特阿拉伯": "Saudi Arabia",
    "乌拉圭": "Uruguay",
    "法国": "France",
    "塞内加尔": "Senegal",
    "挪威": "Norway",
    "伊拉克": "Iraq",
    "阿根廷": "Argentina",
    "阿尔及利亚": "Algeria",
    "阿尔及利": "Algeria",
    "奥地利": "Austria",
    "约旦": "Jordan",
    "阿联酋": "UAE",
    "葡萄牙": "Portugal",
    "哥伦比亚": "Colombia",
    "刚果(金)": "Congo DR",
    "刚果金": "Congo DR",
    "民主刚果": "Congo DR",
    "乌兹别克斯坦": "Uzbekistan",
    "乌兹别克": "Uzbekistan",
    "英格兰": "England",
    "克罗地亚": "Croatia",
    "加纳": "Ghana",
    "巴拿马": "Panama",
}

TEAM_EN_ALIASES = {
    "dr congo": "congo dr",
    "congo dr": "congo dr",
    "democratic republic of the congo": "congo dr",
    "czechia": "czech republic",
    "bosnia and herzegovina": "bosnia",
    "bosnia & herzegovina": "bosnia",
    "united states": "usa",
    "korea republic": "south korea",
    "curacao": "curaçao",
}

SIDE_CN = {"home": "主胜", "draw": "平局", "away": "客胜"}
HHAD_SIDE_CN = {"home": "让球主胜", "draw": "让球平", "away": "让球负"}
PROB_KEYS = ("home", "draw", "away")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

SPORTTERY_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.sporttery.cn/",
    "Accept": "application/json",
}


def load_env() -> None:
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def fetch_json(url: str, headers: dict | None = None) -> tuple[dict | list, dict]:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=20, context=SSL_CTX) as resp:
        body = resp.read().decode("utf-8")
        meta = {
            "x-requests-remaining": resp.headers.get("x-requests-remaining"),
            "x-requests-used": resp.headers.get("x-requests-used"),
        }
        return json.loads(body), meta


def normalize_team(name: str) -> str:
    n = name.strip().lower()
    return TEAM_EN_ALIASES.get(n, n)


def cn_to_en(name: str) -> str:
    return TEAM_CN_TO_EN.get(name, name)


def match_key(home: str, away: str) -> str:
    return f"{normalize_team(home)}|{normalize_team(away)}"


def de_margin(h: float, d: float, a: float) -> dict:
    imp = [1 / h, 1 / d, 1 / a]
    total = sum(imp)
    return {
        "home": imp[0] / total,
        "draw": imp[1] / total,
        "away": imp[2] / total,
        "overround": total,
    }


def favorite_side(probs: dict) -> str:
    return max(PROB_KEYS, key=lambda k: probs[k])


def fetch_single_status(sporttery_match_id: int) -> dict[str, str | None]:
    """Return poolCode -> 'single' | 'parlay_only' | None (not listed)."""
    url = (
        "https://webapi.sporttery.cn/gateway/uniform/football/getFixedBonusV1.qry"
        f"?clientCode=3001&matchId={sporttery_match_id}"
    )
    try:
        data, _ = fetch_json(url, SPORTTERY_HEADERS)
        out: dict[str, str | None] = {}
        for item in data.get("value", {}).get("oddsHistory", {}).get("singleList", []):
            pool = item.get("poolCode")
            if not pool:
                continue
            out[pool] = "single" if item.get("single") == 1 else "parlay_only"
        return out
    except Exception:
        return {}


def ticket_label(pool: str, single_status: dict[str, str | None]) -> tuple[str, str]:
    st = single_status.get(pool)
    if st == "single":
        return "单关", "浮动奖金"
    if st == "parlay_only":
        return "仅过关", "固定奖金(须2串1+)"
    return "待核实", "待核实"


def hhad_semantic(line: str, side: str, home_cn: str, away_cn: str) -> str:
    line = (line or "").strip()
    side_cn = HHAD_SIDE_CN[side]
    if line.startswith("+"):
        n = line.replace("+", "").replace(".00", "")
        if side == "home":
            return f"{home_cn}受让{n}球后{side_cn}（客队最多净胜{n}球或更少）"
        if side == "draw":
            return f"{home_cn}受让{n}球后{side_cn}（客队恰好净胜{n}球）"
        return f"{home_cn}受让{n}球后{side_cn}（客队净胜{n}球以上）"
    if line.startswith("-"):
        n = line.replace("-", "").replace(".00", "")
        if side == "home":
            return f"{home_cn}让{n}球后{side_cn}（主队净胜{n}球以上）"
        if side == "draw":
            return f"{home_cn}让{n}球后{side_cn}（主队恰好净胜{n}球）"
        return f"{home_cn}让{n}球后{side_cn}（主队净胜不足{n}球）"
    return side_cn


def map_totals_to_ttg(totals_line: float | None) -> dict | None:
    if totals_line is None:
        return None
    low = int(totals_line)
    if totals_line - low >= 0.25:
        buckets = [str(low), str(low + 1)]
        note = f"外盘O/U {totals_line} → 竞彩TTG关注「{low}球」「{low + 1}球」档位（非大小球2.5）"
    else:
        buckets = [str(max(0, low - 1)), str(low), str(low + 1)]
        note = f"外盘O/U {totals_line} → 竞彩TTG关注「{buckets[0]}球」「{buckets[1]}球」「{buckets[2]}球」档位（非大小球2.5）"
    return {
        "play": "总进球",
        "pool": "TTG",
        "buckets": buckets,
        "ticket_hint": "场次开放制，查 singleList",
        "note": note,
    }


def build_sporttery_mappings(
    sp: dict,
    deviation: dict | None,
    totals_line: float | None,
) -> list[dict]:
    """外盘偏差/方向 → 竞彩可买玩法映射（含单关/仅过关）。"""
    mappings: list[dict] = []
    singles = sp.get("single_status", {})
    had = sp.get("had")
    hhad = sp.get("hhad")

    value_sides: list[str] = []
    if deviation:
        value_sides = [s for s in PROB_KEYS if deviation["deltas"][s] <= -0.03]
        if not value_sides and deviation.get("direction_conflict"):
            value_sides = [deviation["sharp_favorite"]]

    for side in value_sides:
        side_cn = SIDE_CN[side]
        signal = ""
        if deviation:
            signal = f"外盘去水偏低 {deviation['deltas'][side]:+.1%}"

        if had:
            ticket_type, bonus = ticket_label("HAD", singles)
            mappings.append(
                {
                    "priority": "primary",
                    "play": "胜平负",
                    "pool": "HAD",
                    "selection": side_cn,
                    "odds": had[side],
                    "ticket_type": ticket_type,
                    "bonus_type": bonus,
                    "semantic": f"全场90分钟{side_cn}",
                    "overseas_signal": signal,
                    "caveat": (
                        None
                        if ticket_type == "单关"
                        else (
                            "胜平负本场仅过关，须至少2串1"
                            if ticket_type == "仅过关"
                            else "须查 singleList 确认单关/仅过关"
                        )
                    ),
                }
            )
        else:
            mappings.append(
                {
                    "priority": "blocked",
                    "play": "胜平负",
                    "pool": "HAD",
                    "selection": side_cn,
                    "odds": None,
                    "ticket_type": "未开售",
                    "bonus_type": None,
                    "semantic": f"口语「{side_cn}」",
                    "overseas_signal": signal,
                    "caveat": "HAD未开售，不可直接买胜平负；请改用下方HHAD选项",
                }
            )

        if hhad:
            ticket_type, bonus = ticket_label("HHAD", singles)
            caveat = None
            if not had:
                caveat = f"语义≠HAD{side_cn}，须阅读让球说明"
            elif side != "draw":
                caveat = "HHAD选项含义与胜平负不同，勿混淆"
            mappings.append(
                {
                    "priority": "secondary",
                    "play": "让球胜平负",
                    "pool": "HHAD",
                    "selection": HHAD_SIDE_CN[side],
                    "line": hhad.get("line", ""),
                    "odds": hhad[side],
                    "ticket_type": ticket_type,
                    "bonus_type": bonus,
                    "semantic": hhad_semantic(
                        hhad.get("line", ""),
                        side,
                        sp["home_cn"],
                        sp["away_cn"],
                    ),
                    "overseas_signal": signal,
                    "caveat": caveat,
                }
            )

    if hhad and (not value_sides or not had):
        ticket_type, bonus = ticket_label("HHAD", singles)
        pri = "primary_hhad" if not had else "reference"
        signal = (
            "HAD未开售，让球为本场主要出票玩法"
            if not had
            else "定价接近，列出让球三项供选型"
        )
        for side in PROB_KEYS:
            mappings.append(
                {
                    "priority": pri,
                    "play": "让球胜平负",
                    "pool": "HHAD",
                    "selection": HHAD_SIDE_CN[side],
                    "line": hhad.get("line", ""),
                    "odds": hhad[side],
                    "ticket_type": ticket_type,
                    "bonus_type": bonus,
                    "semantic": hhad_semantic(
                        hhad.get("line", ""),
                        side,
                        sp["home_cn"],
                        sp["away_cn"],
                    ),
                    "overseas_signal": signal,
                    "caveat": (
                        "口语胜平负不可直接下单，此为让球选项"
                        if not had
                        else None
                    ),
                }
            )

    ttg = map_totals_to_ttg(totals_line)
    if ttg:
        ttg_type, ttg_bonus = ticket_label("TTG", singles)
        ttg["ticket_type"] = ttg_type
        ttg["bonus_type"] = ttg_bonus
        ttg["priority"] = "supplement"
        mappings.append(ttg)

    order = {
        "primary": 0,
        "primary_hhad": 1,
        "secondary": 2,
        "blocked": 3,
        "supplement": 4,
        "reference": 5,
    }
    mappings.sort(key=lambda m: order.get(m.get("priority", 9), 9))
    return mappings


def fetch_sporttery() -> dict[str, dict]:
    url = "https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001"
    data, _ = fetch_json(url, SPORTTERY_HEADERS)
    out: dict[str, dict] = {}
    pending_ids: list[tuple[str, int]] = []

    for day in data.get("value", {}).get("matchInfoList", []):
        for m in day.get("subMatchList", []):
            if m.get("leagueAllName") != "世界杯":
                continue
            home_cn = m.get("homeTeamAllName", "")
            away_cn = m.get("awayTeamAllName", "")
            home_en = cn_to_en(home_cn)
            away_en = cn_to_en(away_cn)
            key = match_key(home_en, away_en)
            sporttery_id = m.get("matchId")
            row = {
                "sporttery_id": sporttery_id,
                "match_id": m.get("matchNumStr", ""),
                "home_cn": home_cn,
                "away_cn": away_cn,
                "home_en": home_en,
                "away_en": away_en,
                "kickoff": f"{m.get('matchDate', '')} {m.get('matchTime', '')}",
                "status": m.get("matchStatus", ""),
                "had": None,
                "hhad": None,
                "had_on_sale": False,
                "hhad_on_sale": False,
                "single_status": {},
            }
            for o in m.get("oddsList", []):
                pool = o.get("poolCode")
                if pool == "HAD" and o.get("h"):
                    row["had"] = {
                        "home": float(o["h"]),
                        "draw": float(o["d"]),
                        "away": float(o["a"]),
                    }
                    row["had_on_sale"] = True
                elif pool == "HHAD" and o.get("h"):
                    row["hhad"] = {
                        "line": o.get("goalLine", ""),
                        "home": float(o["h"]),
                        "draw": float(o["d"]),
                        "away": float(o["a"]),
                    }
                    row["hhad_on_sale"] = True
            out[key] = row
            if sporttery_id:
                pending_ids.append((key, int(sporttery_id)))

    for key, sid in pending_ids:
        out[key]["single_status"] = fetch_single_status(sid)
        time.sleep(0.12)

    return out


def fetch_odds_api(api_key: str) -> tuple[dict[str, dict], dict]:
    url = (
        "https://api.the-odds-api.com/v4/sports/soccer_fifa_world_cup/odds/"
        f"?apiKey={api_key}&regions=eu,uk,us&markets=h2h,totals"
        "&oddsFormat=decimal"
    )
    data, meta = fetch_json(url)
    out: dict[str, dict] = {}
    for m in data:
        home = m.get("home_team", "")
        away = m.get("away_team", "")
        key = match_key(home, away)
        books: list[dict] = []
        pinnacle = None
        totals_lines: list[float] = []
        for bm in m.get("bookmakers", []):
            h2h = None
            totals = None
            for mk in bm.get("markets", []):
                if mk.get("key") == "h2h":
                    odds = {"home": None, "draw": None, "away": None}
                    for oc in mk.get("outcomes", []):
                        nm = oc.get("name", "")
                        if nm == home:
                            odds["home"] = float(oc["price"])
                        elif nm == away:
                            odds["away"] = float(oc["price"])
                        elif nm.lower() == "draw":
                            odds["draw"] = float(oc["price"])
                    if all(odds.values()):
                        h2h = odds
                elif mk.get("key") == "totals":
                    for oc in mk.get("outcomes", []):
                        if oc.get("name") == "Over" and oc.get("point") is not None:
                            totals = {
                                "line": float(oc["point"]),
                                "over": float(oc["price"]),
                            }
                            for oc2 in mk.get("outcomes", []):
                                if oc2.get("name") == "Under":
                                    totals["under"] = float(oc2["price"])
                            break
            if h2h:
                entry = {
                    "book": bm.get("title", bm.get("key", "")),
                    "h2h": h2h,
                    "totals": totals,
                }
                books.append(entry)
                if bm.get("key") == "pinnacle":
                    pinnacle = entry
                if totals and totals.get("line") is not None:
                    totals_lines.append(totals["line"])

        if not books:
            continue

        avg = {
            "home": statistics.mean(b["h2h"]["home"] for b in books),
            "draw": statistics.mean(b["h2h"]["draw"] for b in books),
            "away": statistics.mean(b["h2h"]["away"] for b in books),
        }
        out[key] = {
            "home_en": home,
            "away_en": away,
            "commence_time": m.get("commence_time", ""),
            "bookmaker_count": len(books),
            "consensus_h2h": avg,
            "consensus_probs": de_margin(avg["home"], avg["draw"], avg["away"]),
            "pinnacle": pinnacle,
            "pinnacle_probs": (
                de_margin(
                    pinnacle["h2h"]["home"],
                    pinnacle["h2h"]["draw"],
                    pinnacle["h2h"]["away"],
                )
                if pinnacle
                else None
            ),
            "totals_line_median": statistics.median(totals_lines) if totals_lines else None,
            "books": books,
        }
    return out, meta


def classify_deviation(sp_probs: dict, sharp_probs: dict) -> dict:
    deltas = {
        side: sp_probs[side] - sharp_probs[side] for side in PROB_KEYS
    }
    hottest = max(PROB_KEYS, key=lambda k: deltas[k])
    coldest = min(PROB_KEYS, key=lambda k: deltas[k])
    label = "neutral"
    if deltas[hottest] >= 0.05:
        side_cn = SIDE_CN[hottest]
        strength = "偏热" if deltas[hottest] >= 0.08 else "轻度偏热"
        label = f"sporttery_{hottest}_overheated"
        message = f"体彩{side_cn}{strength} +{deltas[hottest]:.1%} vs 外盘去水"
    elif deltas[coldest] <= -0.05:
        side_cn = SIDE_CN[coldest]
        strength = "偏冷" if deltas[coldest] <= -0.08 else "轻度偏冷"
        label = f"sporttery_{coldest}_underpriced"
        message = f"体彩{side_cn}{strength} {deltas[coldest]:.1%} vs 外盘去水"
    else:
        message = "体彩与外盘定价接近"

    sp_fav = favorite_side(sp_probs)
    sharp_fav = favorite_side(sharp_probs)
    return {
        "label": label,
        "message": message,
        "deltas": deltas,
        "direction_conflict": sp_fav != sharp_fav,
        "sporttery_favorite": sp_fav,
        "sharp_favorite": sharp_fav,
    }


def build_report(sporttery: dict[str, dict], overseas: dict[str, dict]) -> list[dict]:
    rows = []
    keys = sorted(set(sporttery) | set(overseas))
    for key in keys:
        sp = sporttery.get(key)
        ov = overseas.get(key)
        if not sp or not ov:
            continue
        if not sp.get("had_on_sale") and not sp.get("hhad_on_sale"):
            continue

        deviation = None
        sp_probs = None
        if sp.get("had"):
            sp_probs = de_margin(sp["had"]["home"], sp["had"]["draw"], sp["had"]["away"])
            sharp_probs = ov.get("pinnacle_probs") or ov.get("consensus_probs")
            deviation = classify_deviation(sp_probs, sharp_probs)

        sharp_h2h = (
            ov["pinnacle"]["h2h"] if ov.get("pinnacle") else ov.get("consensus_h2h")
        )
        mappings = build_sporttery_mappings(sp, deviation, ov.get("totals_line_median"))

        rows.append(
            {
                "match": f"{sp['home_cn']} vs {sp['away_cn']}",
                "match_id": sp.get("match_id", ""),
                "sporttery_id": sp.get("sporttery_id"),
                "kickoff": sp.get("kickoff", ""),
                "had_on_sale": sp.get("had_on_sale", False),
                "hhad_on_sale": sp.get("hhad_on_sale", False),
                "single_status": sp.get("single_status", {}),
                "sporttery_had": sp.get("had"),
                "sporttery_probs": sp_probs,
                "sporttery_hhad": sp.get("hhad"),
                "sharp_source": "pinnacle" if ov.get("pinnacle") else "consensus",
                "sharp_h2h": sharp_h2h,
                "sharp_probs": ov.get("pinnacle_probs") or ov.get("consensus_probs"),
                "sharp_books": ov.get("bookmaker_count", 0),
                "totals_line_median": ov.get("totals_line_median"),
                "deviation": deviation,
                "sporttery_mappings": mappings,
            }
        )
    return rows


def print_mapping(m: dict, index: int) -> None:
    odds = m.get("odds")
    odds_s = f"@{odds:.2f}" if isinstance(odds, (int, float)) else ""
    line = m.get("line", "")
    line_s = f" [{line}]" if line else ""
    buckets = m.get("buckets")
    if buckets:
        print(
            f"    {index}. {m['play']} {m['pool']} | "
            f"{'/'.join(buckets)}球 | {m.get('ticket_type', '')} | {m.get('bonus_type', '')}"
        )
    else:
        print(
            f"    {index}. {m['play']} {m['pool']}{line_s} | "
            f"{m.get('selection', '')}{odds_s} | {m.get('ticket_type', '')} | {m.get('bonus_type', '')}"
        )
    if m.get("overseas_signal"):
        print(f"       外盘信号: {m['overseas_signal']}")
    print(f"       语义: {m.get('semantic', '')}")
    if m.get("caveat"):
        print(f"       ⚠️ {m['caveat']}")
    if m.get("note"):
        print(f"       ℹ️ {m['note']}")


def print_table(rows: list[dict]) -> None:
    print("=" * 92)
    print(f"  体彩 × 外盘交叉对比 + 竞彩可买映射 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 92)
    if not rows:
        print("  无可对照场次（需体彩与外盘同时有数据）")
        return

    for r in rows:
        dev = r.get("deviation")
        print(f"\n【{r['match_id']}】{r['match']}  {r['kickoff']}")
        sale = []
        if r["had_on_sale"]:
            st = r["single_status"].get("HAD")
            sale.append(f"HAD({'单关' if st == 'single' else '仅过关' if st == 'parlay_only' else '?'})")
        else:
            sale.append("HAD(未开售)")
        if r["hhad_on_sale"]:
            st = r["single_status"].get("HHAD")
            line = (r.get("sporttery_hhad") or {}).get("line", "")
            sale.append(
                f"HHAD{line}({'单关' if st == 'single' else '仅过关' if st == 'parlay_only' else '?'})"
            )
        print(f"  在售: {' | '.join(sale)}")
        print(f"  外盘源: {r['sharp_source']} ({r['sharp_books']}家)")

        if r.get("sporttery_had") and dev:
            sp, sh = r["sporttery_had"], r["sharp_h2h"]
            print(
                f"  {'':8} {'体彩HAD':>8} {'外盘1X2':>8} {'体彩隐含':>10} {'外盘去水':>10} {'偏差':>8}"
            )
            for side, cn in [("home", "主胜"), ("draw", "平局"), ("away", "客胜")]:
                delta = dev["deltas"][side]
                print(
                    f"  {cn:6} {sp[side]:8.2f} {sh[side]:8.2f} "
                    f"{r['sporttery_probs'][side]:9.1%} {r['sharp_probs'][side]:9.1%} "
                    f"{delta:+7.1%}"
                )
            flag = "⚠️" if dev["direction_conflict"] else "✅"
            print(f"  {flag} {dev['message']}")
            if dev["direction_conflict"]:
                fav = SIDE_CN
                print(
                    f"     方向矛盾: 体彩看好{fav[dev['sporttery_favorite']]}，"
                    f"外盘看好{fav[dev['sharp_favorite']]}"
                )
        else:
            print("  HAD未开售 — 跳过胜平负偏差表，仅输出让球映射")

        if r.get("totals_line_median") is not None:
            print(f"  外盘大小球中位线: {r['totals_line_median']} （竞彩无O/U，见TTG映射）")

        print("  ── 竞彩可买映射（外盘信号 → 出票选项）──")
        shown = 0
        max_rows = 5 if not r["had_on_sale"] else 4
        for m in r.get("sporttery_mappings", []):
            if m.get("priority") == "reference":
                continue
            shown += 1
            print_mapping(m, shown)
            if shown >= max_rows:
                break
        if shown == 0:
            print("    (无显著价值映射)")


def main() -> int:
    load_env()
    api_key = os.environ.get("THE_ODDS_API_KEY", "")
    if not api_key:
        print("缺少 THE_ODDS_API_KEY，请写入 .env", file=sys.stderr)
        return 1

    print("拉取体彩赔率 + singleList...", file=sys.stderr)
    sporttery = fetch_sporttery()
    print("拉取外盘赔率...", file=sys.stderr)
    overseas, meta = fetch_odds_api(api_key)
    rows = build_report(sporttery, overseas)

    out_dir = ROOT / "数据"
    out_dir.mkdir(exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rules_reference": "references/sporttery-vs-overseas-rules.md",
        "odds_api_quota": meta,
        "matches": rows,
    }
    out_file = out_dir / "odds_cross_compare.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print_table(rows)
    print(f"\n已保存: {out_file}")
    if meta.get("x-requests-remaining") is not None:
        print(
            f"Odds API 剩余额度: {meta['x-requests-remaining']} "
            f"(已用 {meta.get('x-requests-used', '?')})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())