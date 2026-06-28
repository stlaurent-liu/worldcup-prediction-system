#!/usr/bin/env bash
set -euo pipefail

TARGET="/Users/laurent/Desktop/skills/world-cup-prediction"
LINKS=(
  "/Users/laurent/.grok/skills/world-cup-prediction"
  "/Users/laurent/.hermes/skills/world-cup-prediction"
  "/Users/laurent/.codex/skills/world-cup-prediction"
)

for p in "${LINKS[@]}"; do
  mkdir -p "$(dirname "$p")"
  if [ -e "$p" ] || [ -L "$p" ]; then
    rm "$p"
    echo "Removed: $p"
  fi
  ln -s "$TARGET" "$p"
  echo "Created: $p -> $TARGET"
done

echo "--- ls -la ---"
ls -la "${LINKS[@]}"

echo "--- verify SKILL.md ---"
for p in "${LINKS[@]}"; do
  if [ -f "$p/SKILL.md" ]; then
    echo "OK: $p/SKILL.md"
  else
    echo "FAIL: $p/SKILL.md"
    exit 1
  fi
done