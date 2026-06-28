"""世界杯 cron 自动到期：2026-07-20 最后一跑后卸载，2030 需手动 reinstall。"""
from __future__ import annotations

import subprocess
from datetime import date, datetime
from pathlib import Path

# 决赛 2026-07-19（美东）；北京时间 07-20 23:00 为最后一次赛果同步
TOURNAMENT_CRON_LAST_DAY = date(2026, 7, 20)


def cron_expired() -> bool:
    """已超过最后运行日 → 立即卸载并跳过。"""
    return date.today() > TOURNAMENT_CRON_LAST_DAY


def retire_after_this_run() -> bool:
    """最后一日 23:00 场跑完后卸载（含两条 cron）。"""
    now = datetime.now()
    if date.today() > TOURNAMENT_CRON_LAST_DAY:
        return True
    if date.today() == TOURNAMENT_CRON_LAST_DAY and now.hour >= 23:
        return True
    return False


def retire_cron(reason: str) -> None:
    script = Path(__file__).resolve().parent / "setup_wc2026_cron.sh"
    log = Path(__file__).resolve().parent.parent / "logs" / "wc2026_results_sync.log"
    msg = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] AUTO-RETIRE cron: {reason}\n"
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(msg)
    subprocess.run(["bash", str(script), "--remove"], check=False)
    print(msg.strip())


def guard_cron_at_start(job_name: str) -> None:
    if cron_expired():
        retire_cron(f"{job_name}: tournament ended ({TOURNAMENT_CRON_LAST_DAY}), past last run day")
        raise SystemExit(0)


def maybe_retire_cron_after_run(job_name: str) -> None:
    if retire_after_this_run():
        retire_cron(
            f"{job_name}: final run completed on {TOURNAMENT_CRON_LAST_DAY} (re-enable in 2030 via setup_wc2026_cron.sh --install)"
        )