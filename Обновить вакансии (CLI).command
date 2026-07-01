#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python scripts/scan.py
python scripts/match.py --limit 50
echo ""
echo "✅ Обновление завершено! Обнови страницу в браузере."
echo "Нажми любую клавишу для выхода..."
read -n 1
