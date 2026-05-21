#!/usr/bin/env bash
set -euo pipefail

# Optional full-stack smoke for judge/demo readiness.
# It is intentionally opt-in because it starts local services and can be slower
# than the default unit-test suite. It runs in credential-free fallback mode:
# EDGE_TRIAGE_LIVE_MODEL=0 exercises the guarded API path without requiring
# multi-GB GGUF artifacts, Hugging Face credentials, Kaggle credentials, or GPU.

if [[ "${EDGE_TRIAGE_RUN_E2E:-}" != "1" ]]; then
  echo "Refusing to run optional E2E smoke without EDGE_TRIAGE_RUN_E2E=1" >&2
  echo "Run: EDGE_TRIAGE_RUN_E2E=1 scripts/e2e_smoke.sh" >&2
  exit 2
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

STATIC_PORT="${EDGE_TRIAGE_E2E_STATIC_PORT:-}"
API_PORT="${EDGE_TRIAGE_E2E_API_PORT:-}"
TMP_DIR="$(mktemp -d)"
STATIC_PID=""
API_PID=""

cleanup() {
  local code=$?
  if [[ -n "$STATIC_PID" ]] && kill -0 "$STATIC_PID" 2>/dev/null; then
    kill "$STATIC_PID" 2>/dev/null || true
  fi
  if [[ -n "$API_PID" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  rm -rf "$TMP_DIR"
  exit "$code"
}
trap cleanup EXIT

wait_for_url() {
  local url="$1"
  for _ in $(seq 1 60); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "Timed out waiting for $url" >&2
  return 1
}

pick_free_port() {
  python3 - <<'PY'
import socket
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

require_free_port() {
  local port="$1"
  python3 - "$port" <<'PY'
import socket, sys
port = int(sys.argv[1])
with socket.socket() as sock:
    try:
        sock.bind(("127.0.0.1", port))
    except OSError as exc:
        raise SystemExit(f"Port {port} is not free: {exc}")
PY
}

if [[ -z "$STATIC_PORT" ]]; then
  STATIC_PORT="$(pick_free_port)"
else
  require_free_port "$STATIC_PORT"
fi

if [[ -z "$API_PORT" ]]; then
  API_PORT="$(pick_free_port)"
else
  require_free_port "$API_PORT"
fi

# Validate compose syntax even though the default smoke uses local processes for speed.
docker compose --env-file .env.example config >/dev/null

if [[ "${EDGE_TRIAGE_E2E_DOCKER:-}" == "1" ]]; then
  docker compose up -d --build edge-triage-demo
  curl -fsSI "http://127.0.0.1:${STATIC_PORT}/" >/dev/null
  docker compose down
fi

python3 -m http.server "$STATIC_PORT" --bind 127.0.0.1 --directory site >"$TMP_DIR/static.log" 2>&1 &
STATIC_PID="$!"

EDGE_TRIAGE_LIVE_MODEL=0 \
EDGE_TRIAGE_PUBLIC_API_ENABLED=1 \
EDGE_TRIAGE_RATE_LIMIT_PER_MINUTE=60 \
EDGE_TRIAGE_RATE_LIMIT_PER_DAY=1000 \
EDGE_TRIAGE_ALLOWED_ORIGINS="http://127.0.0.1:${STATIC_PORT},http://localhost:${STATIC_PORT}" \
uv run uvicorn live_api:app --host 127.0.0.1 --port "$API_PORT" >"$TMP_DIR/api.log" 2>&1 &
API_PID="$!"

wait_for_url "http://127.0.0.1:${STATIC_PORT}/"
wait_for_url "http://127.0.0.1:${API_PORT}/healthz"

uv run python - "$TMP_DIR/sample.png" <<'PY'
from pathlib import Path
from PIL import Image
path = Path(__import__('sys').argv[1])
Image.new('RGB', (24, 24), color=(220, 80, 50)).save(path)
PY

curl -fsS \
  -F "image=@${TMP_DIR}/sample.png;type=image/png" \
  -F "note=Bridge damaged after flood; families waiting near school." \
  "http://127.0.0.1:${API_PORT}/api/triage" \
  -o "$TMP_DIR/triage.json"

python3 - "$TMP_DIR/triage.json" <<'PY'
import json, sys
payload = json.load(open(sys.argv[1]))
allowed = {
    "affected_injured_or_dead_people",
    "infrastructure_and_utility_damage",
    "rescue_volunteering_or_donation_effort",
    "not_humanitarian",
}
assert payload["label"] in allowed, payload
assert isinstance(payload.get("next_action"), str) and payload["next_action"], payload
assert payload.get("live_model") is False, payload
assert "disclaimer" in payload, payload
print("E2E smoke passed:", payload["label"], payload["latency_ms"])
PY
