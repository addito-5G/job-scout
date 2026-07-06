#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
pip install -e . -q
python scripts/scan.py --match-limit 50
echo ""
echo "✅ Обновление завершено! Обнови страницу в браузере."
echo "Нажми любую клавишу для выхода..."
read -n 1
