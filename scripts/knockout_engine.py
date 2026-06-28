#!/usr/bin/env python3
"""淘汰赛增强：缺阵 Elo 扣减 + 点球大战贝叶斯模型（借鉴 targetFuseLab 思路）。"""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 103 场世界杯点球大战历史收缩先验（targetFuseLab / literature）
PK_PRIOR_N = 103
PK_PRIOR_WIN_RATE = 0.50
PK_ELO_SCALE = 250  # 点球环节 Elo 影响弱于常规 400

# 2026 东道主小组赛主场加成（Elo 点）
HOST_NATIONS = {"墨西哥", "美国", "United States", "Canada"}
HOST_GROUP_ELO_BONUS = 100

ABSENCE_ELO_PENALTY = {
    "star_goalkeeper": 50,
    "star_striker": 45,
    "star_midfielder": 35,
    "star_defender": 30,
    "suspension": 25,
    "regular_starter": 15,
    "doubtful": 8,
}

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"
ABSENCES_FILE = CONFIG_DIR / "squad_absences.json"

# 中英文队名互查（squad_absences.json 用中文键，蒙特卡洛用英文）
TEAM_CN_TO_EN = {
    "西班牙": "Spain",
    "法国": "France",
    "阿根廷": "Argentina",
    "英格兰": "England",
    "德国": "Germany",
    "巴西": "Brazil",
    "葡萄牙": "Portugal",
    "荷兰": "Netherlands",
    "哥伦比亚": "Colombia",
    "摩洛哥": "Morocco",
    "比利时": "Belgium",
    "乌拉圭": "Uruguay",
    "日本": "Japan",
    "克罗地亚": "Croatia",
    "美国": "United States",
    "墨西哥": "Mexico",
    "瑞士": "Switzerland",
    "塞内加尔": "Senegal",
    "奥地利": "Austria",
    "挪威": "Norway",
    "厄瓜多尔": "Ecuador",
    "土耳其": "Türkiye",
    "澳大利亚": "Australia",
    "加拿大": "Canada",
    "韩国": "South Korea",
    "伊朗": "Iran",
    "瑞典": "Sweden",
    "捷克": "Czechia",
    "苏格兰": "Scotland",
    "埃及": "Egypt",
    "科特迪瓦": "Ivory Coast",
    "巴拿马": "Panama",
    "沙特阿拉伯": "Saudi Arabia",
    "巴拉圭": "Paraguay",
    "阿尔及利亚": "Algeria",
    "加纳": "Ghana",
    "突尼斯": "Tunisia",
    "波黑": "Bosnia-Herzegovina",
    "卡塔尔": "Qatar",
    "海地": "Haiti",
    "佛得角": "Cape Verde",
    "约旦": "Jordan",
    "乌兹别克斯坦": "Uzbekistan",
    "刚果(金)": "DR Congo",
    "新西兰": "New Zealand",
    "伊拉克": "Iraq",
    "南非": "South Africa",
    "库拉索": "Curaçao",
}
TEAM_EN_TO_CN = {v: k for k, v in TEAM_CN_TO_EN.items()}
TEAM_EN_TO_CN["USA"] = "美国"


def expected_elo_score(elo_a: float, elo_b: float, scale: float = 400.0) -> float:
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / scale))


def host_bonus(team: str, stage: str = "group") -> float:
    if stage != "group":
        return 0.0
    if team in HOST_NATIONS:
        return HOST_GROUP_ELO_BONUS
    return 0.0


def canonical_team_key(team: str) -> str:
    """统一为英文 canonical key，便于中英文缺阵表互查。"""
    if team in TEAM_CN_TO_EN:
        return TEAM_CN_TO_EN[team]
    return team


def load_absences() -> Dict[str, List[dict]]:
    if not ABSENCES_FILE.exists():
        return {}
    with open(ABSENCES_FILE, encoding="utf-8") as f:
        data = json.load(f)
    out: Dict[str, List[dict]] = {}
    for k, v in data.items():
        if k.startswith("_"):
            continue
        key = canonical_team_key(k)
        out[key] = v
    return out


def get_team_absences(
    team: str, absences_by_team: Optional[Dict[str, List[dict]]] = None
) -> List[dict]:
    absences_by_team = absences_by_team or load_absences()
    return absences_by_team.get(canonical_team_key(team), [])


def absence_elo_penalty(absences: List[dict]) -> Tuple[float, List[str]]:
    total = 0.0
    notes: List[str] = []
    for item in absences or []:
        tier = item.get("tier", "doubtful")
        pen = ABSENCE_ELO_PENALTY.get(tier, 10)
        total += pen
        player = item.get("player", "?")
        notes.append(f"{player}({tier} -{pen})")
    return total, notes


def adjust_elo_with_absences(
    team: str,
    base_elo: float,
    absences_by_team: Optional[Dict[str, List[dict]]] = None,
    stage: str = "knockout",
) -> dict:
    absences = get_team_absences(team, absences_by_team)
    penalty, detail = absence_elo_penalty(absences)
    bonus = host_bonus(team, stage)
    adjusted = base_elo - penalty + bonus
    return {
        "team": team,
        "base_elo": round(base_elo, 1),
        "adjusted_elo": round(adjusted, 1),
        "absence_penalty": round(penalty, 1),
        "host_bonus": round(bonus, 1),
        "absence_detail": detail,
        "has_absences": bool(absences),
    }


def penalty_shootout_win_prob(elo_a: float, elo_b: float) -> float:
    """贝叶斯收缩：历史 103 场点球先验 + Elo 软信号。"""
    p_elo = expected_elo_score(elo_a, elo_b, scale=PK_ELO_SCALE)
    # 向 0.5 收缩，避免小样本 Elo 差过度放大
    shrunk = (PK_PRIOR_N * PK_PRIOR_WIN_RATE + p_elo) / (PK_PRIOR_N + 1)
    return round(shrunk, 4)


def knockout_match_probs(
    team_a: str,
    team_b: str,
    elo_a: float,
    elo_b: float,
    stage: str = "knockout",
    absences_by_team: Optional[Dict[str, List[dict]]] = None,
) -> dict:
    """返回常规时间胜平负 + 点球晋级概率（含/不含缺阵双轨）。"""
    absences_by_team = absences_by_team or load_absences()

    def _track(elo_x: float, elo_y: float, label: str) -> dict:
        diff = elo_x - elo_y
        p_w = expected_elo_score(elo_x, elo_y)
        draw_base = 0.24 * math.exp(-(abs(diff) / 500) ** 1.5)
        p_d = draw_base
        p_l = max(0.0, 1.0 - p_w - p_d)
        p_pk = penalty_shootout_win_prob(elo_x, elo_y)
        p_advance = p_w + p_d * p_pk
        return {
            "label": label,
            "p_win": round(p_w, 4),
            "p_draw": round(p_d, 4),
            "p_loss": round(p_l, 4),
            "p_pk_win_if_draw": p_pk,
            "p_advance": round(p_advance, 4),
        }

    adj_a = adjust_elo_with_absences(team_a, elo_a, absences_by_team, stage)
    adj_b = adjust_elo_with_absences(team_b, elo_b, absences_by_team, stage)

    base = _track(elo_a, elo_b, "base")
    adjusted = _track(adj_a["adjusted_elo"], adj_b["adjusted_elo"], "with_absences")

    delta_advance = round(adjusted["p_advance"] - base["p_advance"], 4)
    return {
        "team_a": team_a,
        "team_b": team_b,
        "stage": stage,
        "team_a_elo": adj_a,
        "team_b_elo": adj_b,
        "base": base,
        "adjusted": adjusted,
        "absence_delta_advance": delta_advance,
        "recommendation": (
            "缺阵显著影响晋级概率，优先采 adjusted 轨道"
            if abs(delta_advance) >= 0.04
            else "缺阵影响有限，可采 base 轨道"
        ),
    }


def resolve_knockout_winner(
    team_a: str,
    team_b: str,
    elo_a: float,
    elo_b: float,
    use_absences: bool = True,
) -> str:
    """蒙特卡洛用：平局走点球模型而非 50/50。"""
    info = knockout_match_probs(team_a, team_b, elo_a, elo_b)
    track = info["adjusted"] if use_absences else info["base"]
    import random

    r = random.random()
    if r < track["p_win"]:
        return team_a
    if r < track["p_win"] + track["p_draw"]:
        return team_a if random.random() < track["p_pk_win_if_draw"] else team_b
    return team_b


if __name__ == "__main__":
    demo = knockout_match_probs("France", "Argentina", 1820, 1800)
    print(json.dumps(demo, ensure_ascii=False, indent=2))