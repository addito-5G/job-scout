#!/usr/bin/env bash
# Одноразовая настройка GitHub CLI для git/gh из терминала и Cursor.
set -euo pipefail

TOKEN_FILE="${HOME}/.config/gh/token"
ZSHENV="${HOME}/.zshenv"
MARKER="# >>> github-cli token >>>"

mkdir -p "${HOME}/.config/gh"
chmod 700 "${HOME}/.config/gh"

if gh auth status &>/dev/null 2>&1; then
  echo "✅ GitHub CLI уже авторизован: $(gh api user -q .login)"
  exit 0
fi

if [[ -f "${TOKEN_FILE}" ]]; then
  echo "🔑 Найден ${TOKEN_FILE}, логиним gh..."
  gh auth login --with-token < "${TOKEN_FILE}"
  gh auth status
  exit 0
fi

echo ""
echo "Одноразовая настройка GitHub CLI"
echo "================================"
echo "Нужен Personal Access Token (classic) с правами: repo, read:org, gist"
echo ""
echo "Откроется страница создания токена в браузере..."
if command -v open &>/dev/null; then
  open "https://github.com/settings/tokens/new?description=gh-cli-local&scopes=repo,read:org,gist"
fi

read -rsp "Вставьте токен сюда (ввод скрыт) и нажмите Enter: " token
echo ""

if [[ -z "${token}" ]]; then
  echo "❌ Токен пустой. Запустите скрипт снова: bash scripts/setup_github_auth.sh"
  exit 1
fi

printf '%s' "${token}" > "${TOKEN_FILE}"
chmod 600 "${TOKEN_FILE}"

gh auth login --with-token < "${TOKEN_FILE}"

if ! grep -qF "${MARKER}" "${ZSHENV}" 2>/dev/null; then
  cat >> "${ZSHENV}" <<'EOF'

# >>> github-cli token >>>
if [[ -f "$HOME/.config/gh/token" ]]; then
  export GH_TOKEN="$(<"$HOME/.config/gh/token")"
  export GITHUB_TOKEN="$GH_TOKEN"
fi
# <<< github-cli token <<<
EOF
  echo "📝 Добавлено в ~/.zshenv — GH_TOKEN будет доступен в Cursor и терминале"
fi

echo ""
gh auth status
echo "✅ Готово. Больше настраивать не нужно."
