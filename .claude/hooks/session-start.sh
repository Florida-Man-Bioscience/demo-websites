#!/bin/bash
# SessionStart hook: install the voice-agent's Python dependencies so tests,
# linters, and the server can run in Claude Code on the web sessions.
set -euo pipefail

# Web/remote sessions only — local machines manage their own environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

AGENT_DIR="$CLAUDE_PROJECT_DIR/voice-agent"
VENV="$AGENT_DIR/.venv"

# Idempotent: reuses the cached venv on subsequent sessions; `pip install`
# (not `pip install --require-virtualenv`/`ci`) is a no-op when satisfied.
python3 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip
"$VENV/bin/pip" install --quiet -r "$AGENT_DIR/requirements.txt"

# Put the venv on PATH for the rest of the session so `python`, `uvicorn`,
# and `pytest` resolve to it.
echo "export PATH=\"$VENV/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
echo "export VIRTUAL_ENV=\"$VENV\"" >> "$CLAUDE_ENV_FILE"

echo "voice-agent dependencies ready in $VENV"
