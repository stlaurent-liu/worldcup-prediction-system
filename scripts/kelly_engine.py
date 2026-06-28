import json, math
from typing import Dict, List, Optional

UNIT_YUAN = 2  # 体彩竞彩：每注基本投注金额 2 元（官方规则，外盘无此粒度）
DEFAULT_MAX_MULTIPLIER = 50  # App 常见上限；官方条文写 2–99 倍，以出票界面为准
MAX_TICKET_YUAN = 20000  # 单张彩票最大投注金额


def quantize_stake(
    target_yuan: float,
    ticket_count: int = 1,
    max_multiplier: int = DEFAULT_MAX_MULTIPLIER,
    max_ticket_yuan: int = MAX_TICKET_YUAN,
) -> dict:
    """将 Markowitz/Kelly 连续金额映射为合法体彩票面：注数 × 2元 × 倍数。"""
    ticket_count = max(1, int(ticket_count))
    min_face = UNIT_YUAN * ticket_count
    if target_yuan < min_face:
        return {
            'ok': False,
            'ticket_count': ticket_count,
            'unit_yuan': UNIT_YUAN,
            'multiplier': 0,
            'face_value_yuan': 0,
            'ideal_yuan': round(target_yuan, 2),
            'rounding_delta_yuan': -round(target_yuan, 2),
            'formula': None,
            'reason': f'低于最小票面 {min_face}元（{ticket_count}注×{UNIT_YUAN}元×1倍）',
        }
    unit_cost = UNIT_YUAN * ticket_count
    multiplier = max(1, int(round(target_yuan / unit_cost)))
    multiplier = min(multiplier, max_multiplier)
    face_value = unit_cost * multiplier
    while face_value > max_ticket_yuan and multiplier > 1:
        multiplier -= 1
        face_value = unit_cost * multiplier
    if face_value > max_ticket_yuan:
        return {
            'ok': False,
            'ticket_count': ticket_count,
            'unit_yuan': UNIT_YUAN,
            'multiplier': multiplier,
            'face_value_yuan': face_value,
            'ideal_yuan': round(target_yuan, 2),
            'rounding_delta_yuan': face_value - target_yuan,
            'formula': f'{ticket_count}注 × {UNIT_YUAN}元 × {multiplier}倍 = {face_value}元',
            'reason': f'超过单票上限 {max_ticket_yuan}元',
        }
    return {
        'ok': True,
        'ticket_count': ticket_count,
        'unit_yuan': UNIT_YUAN,
        'multiplier': multiplier,
        'face_value_yuan': face_value,
        'ideal_yuan': round(target_yuan, 2),
        'rounding_delta_yuan': round(face_value - target_yuan, 2),
        'formula': f'{ticket_count}注 × {UNIT_YUAN}元 × {multiplier}倍 = {face_value}元',
        'reason': None,
    }


def quantize_budget(
    allocations: Dict,
    budget: int,
    ticket_counts: Optional[Dict] = None,
    priority_order: Optional[List] = None,
    max_multiplier: int = DEFAULT_MAX_MULTIPLIER,
) -> dict:
    """多场理想分配 → 合法票面，尽量贴合总预算（步长均为 2 的整数倍）。"""
    ticket_counts = ticket_counts or {}
    keys = list(allocations.keys())
    if priority_order:
        rank = {k: i for i, k in enumerate(priority_order)}
        keys.sort(key=lambda k: (rank.get(k, 999), -float(allocations[k])))
    else:
        keys.sort(key=lambda k: -float(allocations[k]))

    items = {}
    for k in keys:
        tc = ticket_counts.get(k, 1)
        items[k] = quantize_stake(float(allocations[k]), ticket_count=tc, max_multiplier=max_multiplier)

    def _total() -> int:
        return sum(v['face_value_yuan'] for v in items.values() if v['ok'])

    diff = int(budget) - _total()
    guard = 0
    while diff != 0 and keys and guard < len(keys) * 200:
        guard += 1
        k = keys[guard % len(keys)]
        q = items[k]
        if not q['ok']:
            continue
        step = UNIT_YUAN * q['ticket_count']
        if diff > 0:
            if q['multiplier'] >= max_multiplier:
                continue
            if _total() + step > int(budget):
                continue
            q['multiplier'] += 1
            q['face_value_yuan'] += step
            q['rounding_delta_yuan'] = round(q['face_value_yuan'] - q['ideal_yuan'], 2)
            q['formula'] = f"{q['ticket_count']}注 × {UNIT_YUAN}元 × {q['multiplier']}倍 = {q['face_value_yuan']}元"
            diff -= step
        elif diff < 0 and q['multiplier'] > 1:
            q['multiplier'] -= 1
            q['face_value_yuan'] -= step
            q['rounding_delta_yuan'] = round(q['face_value_yuan'] - q['ideal_yuan'], 2)
            q['formula'] = f"{q['ticket_count']}注 × {UNIT_YUAN}元 × {q['multiplier']}倍 = {q['face_value_yuan']}元"
            diff += step

    total_face = _total()
    unallocated = int(budget) - total_face
    return {
        'budget_yuan': int(budget),
        'total_face_value_yuan': total_face,
        'unallocated_yuan': unallocated,
        'unallocated_note': (
            f'{unallocated}元无法按 2元/注 分配，建议并入最高 EV 项或放弃'
            if unallocated > 0 else None
        ),
        'items': items,
    }


def kelly(prob: float, decimal_odds: float, fraction: float = 0.25) -> dict:
    '''Kelly Criterion仓位计算'''
    if not (0 < prob < 1) or decimal_odds <= 1:
        return {'ok': False, 'full_kelly': None, 'suggested_pct': None}
    b = decimal_odds - 1; q = 1 - prob
    full = (b * prob - q) / b
    suggested = max(0.0, full * fraction)
    if suggested <= 0: tier = '不投'
    elif suggested < 0.05: tier = '轻仓'
    elif suggested < 0.15: tier = '中仓'
    elif suggested < 0.25: tier = '重仓'
    else: tier = '超重仓⚠️'
    return {'ok': True, 'full_kelly': round(full, 4), 'suggested_pct': round(suggested, 4), 'tier': tier}

def evaluate_bet(label: str, model_prob: float, decimal_odds: float) -> dict:
    '''EV + Kelly 联合评估'''
    market_implied = 1 / decimal_odds
    edge = model_prob - market_implied
    ev = model_prob * (decimal_odds - 1) - (1 - model_prob)
    if edge >= 0.08: value_tier = '高价值 🔥'
    elif edge >= 0.04: value_tier = '中高价值 ⭐'
    elif edge >= 0.01: value_tier = '中价值'
    elif edge >= -0.02: value_tier = '中性 ℹ️'
    else: value_tier = '低价值'
    k = kelly(model_prob, decimal_odds)
    return {'label': label, 'model_prob': round(model_prob, 4), 'edge': round(edge, 4), 'ev': round(ev, 6), 'value_tier': value_tier, 'kelly': k, 'recommend': edge > 0.01 and k['suggested_pct'] > 0.03}


if __name__ == '__main__':
    print('=== quantize_stake ===')
    print(json.dumps(quantize_stake(73.5), ensure_ascii=False, indent=2))
    print('=== quantize_budget ===')
    demo = quantize_budget({'A场-主胜': 73.5, 'B场-客胜': 58.2, 'C场-2串1': 68.3}, budget=200)
    print(json.dumps(demo, ensure_ascii=False, indent=2))
