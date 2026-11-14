#!/usr/bin/env bash
# Reproducible install of the Factorio Learning Environment (FLE) client side.
# - Python 3.12 venv at ./.venv (FLE supports 3.10-3.13; 3.12 is what we tested)
# - factorio-learning-environment==0.4.3 (latest on PyPI as of 2026-11)
# - a2a-sdk<1   (GOTCHA: FLE 0.4.3 imports a2a.types.TextPart, removed in a2a-sdk 1.x)
# - sprites for the PNG renderer (downloaded from HuggingFace into ./.fle/sprites)
# - Factorio server docker image factoriotools/factorio:2.0.73
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ ! -x .venv/bin/python ]; then
  uv venv -p 3.12 .venv
fi
uv pip install -p .venv "factorio-learning-environment==0.4.3" "a2a-sdk<1"
# Optional: FLE's own MCP server (python -m fle.env.protocols._mcp). The 0.4.3 [mcp] extra
# forgets fastmcp, and fastmcp>=2.14 rejects FLE's FastMCP(dependencies=...) kwarg.
if [ "${WITH_MCP:-0}" = 1 ]; then
  uv pip install -p .venv "fastmcp<2.14" dulwich "a2a-sdk<1"
fi

# Sprites (~370MB download incl. spritemaps; only .fle/sprites (~22MB) is used at render time)
if [ ! -d .fle/sprites ] || [ -z "$(ls -A .fle/sprites 2>/dev/null)" ]; then
  .venv/bin/fle sprites
fi
# Entity sprites need `basisu`; reuse the dataset's pre-transcoded cache instead (see script).
if ! ls .fle/sprites/burner-mining-drill_north.png >/dev/null 2>&1; then
  .venv/bin/python -W ignore setup/fix_sprites.py | tail -2
fi
# Also expose sprites at ~/.fle/sprites (FLE's fallback lookup) so rendering works from any cwd.
mkdir -p "$HOME/.fle"
ln -sfn "$ROOT/.fle/sprites" "$HOME/.fle/sprites"

# `fle` writes a placeholder .env into cwd on first CLI run; it is not needed.
rm -f "$ROOT/.env"

docker pull factoriotools/factorio:2.0.73
echo "install done"
