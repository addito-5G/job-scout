#!/usr/bin/env bash
# Установка ежедневного автообновления Job Scout (macOS launchd, 09:00 по времени системы).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="$ROOT/scripts/com.jobscout.daily.plist"
PLIST_DST="$HOME/Library/LaunchAgents/com.jobscout.daily.plist"
LOG_DIR="$ROOT/data"

mkdir -p "$LOG_DIR"
touch "$LOG_DIR/cron.log"

sed "s|__PROJECT_ROOT__|$ROOT|g" "$PLIST_SRC" > "$PLIST_DST"

launchctl bootout "gui/$(id -u)/com.jobscout.daily" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DST"
launchctl enable "gui/$(id -u)/com.jobscout.daily"

echo "✅ Расписание установлено: com.jobscout.daily"
echo "   Запуск: каждый день в 09:00 (локальное время Mac)"
echo "   Лог: $LOG_DIR/cron.log"
echo ""
echo "Проверка вручную:"
echo "  cd $ROOT && source venv/bin/activate && python scripts/daily_update.py --trigger scheduled"
echo ""
echo "Удалить расписание:"
echo "  launchctl bootout gui/$(id -u)/com.jobscout.daily"
