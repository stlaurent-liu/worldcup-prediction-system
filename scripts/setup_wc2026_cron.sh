#!/usr/bin/env bash
# 安装世界杯赛果每日自动同步 cron（本机 crontab）
# 用法: bash setup_wc2026_cron.sh [--install|--remove|--status]
# 自动到期：2026-07-20 23:00 最后一场跑完后卸载；2030 世界杯前手动 --install 重启

set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3}"
SYNC_SCRIPT="$SKILL_ROOT/scripts/wc2026_results_sync.py"
ODDS_SCRIPT="$SKILL_ROOT/scripts/odds_snapshot_cron.py"
LOG_DIR="$SKILL_ROOT/logs"
mkdir -p "$LOG_DIR"

# 北京时间 12:00 — 覆盖前一夜北美晚场；23:00 — 覆盖当日场
RESULTS_CRON="0 12,23 * * * cd $SKILL_ROOT/scripts && WC2026_DB_PATH=$SKILL_ROOT/data/football_database.sqlite $PYTHON $SYNC_SCRIPT >> $LOG_DIR/wc2026_results_sync.log 2>&1"
# 赔率快照每 2 小时（赛前监控）
ODDS_CRON="0 */2 * * * cd $SKILL_ROOT/scripts && WC2026_DB_PATH=$SKILL_ROOT/data/football_database.sqlite $PYTHON $ODDS_SCRIPT >> $LOG_DIR/odds_snapshot.log 2>&1"

MARK_BEGIN="# wc2026-prediction-cron-begin"
MARK_END="# wc2026-prediction-cron-end"
CRON_EXPIRES="# wc2026-cron-expires: 2026-07-20 (auto-remove after 23:00 run)"

install_cron() {
  local tmp
  tmp="$(mktemp)"
  crontab -l 2>/dev/null | grep -v "$MARK_BEGIN" | grep -v "$MARK_END" | grep -v "wc2026-cron-expires" | grep -v "wc2026_results_sync" | grep -v "odds_snapshot_cron" || true > "$tmp"
  {
    cat "$tmp"
    echo "$MARK_BEGIN"
    echo "$CRON_EXPIRES"
    echo "$RESULTS_CRON"
    echo "$ODDS_CRON"
    echo "$MARK_END"
  } | crontab -
  rm -f "$tmp"
  echo "Installed cron jobs:"
  echo "  - Results sync: 12:00 & 23:00 daily (Asia/Shanghai if system TZ set)"
  echo "  - Odds snapshot: every 2 hours"
  echo "  - Auto-retire: 2026-07-20 23:00 run完成后自动 --remove"
  echo "  - 2030 世界杯: 手动 bash $0 --install"
  echo "Logs: $LOG_DIR/"
}

remove_cron() {
  local tmp
  tmp="$(mktemp)"
  crontab -l 2>/dev/null | grep -v "$MARK_BEGIN" | grep -v "$MARK_END" | grep -v "wc2026-cron-expires" | grep -v "wc2026_results_sync" | grep -v "odds_snapshot_cron" || true > "$tmp"
  crontab "$tmp"
  rm -f "$tmp"
  echo "Removed wc2026 cron entries."
}

case "${1:---install}" in
  --install) install_cron ;;
  --remove)  remove_cron ;;
  --status)
    echo "=== expiry ==="
    echo "  Last run day: 2026-07-20 (23:00 BJT slot triggers auto-remove)"
    echo "=== crontab ==="
    crontab -l 2>/dev/null | sed -n "/$MARK_BEGIN/,/$MARK_END/p" || echo "(not installed)"
    echo "=== last sync log ==="
    tail -n 20 "$LOG_DIR/wc2026_results_sync.log" 2>/dev/null || echo "(no log yet)"
    ;;
  *) echo "Usage: $0 [--install|--remove|--status]" ; exit 1 ;;
esac