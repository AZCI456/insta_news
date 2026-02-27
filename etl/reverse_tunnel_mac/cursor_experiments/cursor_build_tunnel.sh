#!/bin/bash

# Reverse SSH Tunnel Setup Script (Cursor experiment)
# Creates a local SOCKS5 proxy and a reverse tunnel so the remote server can use it.
#
# Flow:
# 1) Start local SOCKS5 proxy on localhost:${SOCKS_PORT}
# 2) Create reverse tunnel: remote localhost:${REMOTE_PORT} -> local localhost:${SOCKS_PORT}
# 3) SSH into remote with HTTP(S)_PROXY set to socks5h://localhost:${REMOTE_PORT}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "${SCRIPT_DIR}/../env_handler.sh"

# Handle variable name mismatch: config uses USER, script expects USERNAME
if [[ -n "${USER:-}" && -z "${USERNAME:-}" ]]; then
  USERNAME="$USER"
fi

# Defaults
SOCKS_PORT="${SOCKS_PORT:-1080}"
REMOTE_PORT="${REMOTE_PORT:-8080}"

if [[ -z "${USERNAME:-}" || -z "${SERVER_ADDRESS:-}" ]]; then
  echo "❌ Error: Missing required configuration variables."
  echo "   Required: USER (or USERNAME), SERVER_ADDRESS (and optionally SOCKS_PORT, REMOTE_PORT, SSH_KEY_PATH)"
  echo "   Config file: ${CONFIG_FILE:-<unknown>}"
  exit 1
fi

# SSH key handling (optional)
SSH_KEY_PATH="${SSH_KEY_PATH:-$HOME/.ssh/id_rsa}"
SSH_KEY_PATH="${SSH_KEY_PATH/#\~/$HOME}"

SSH_BASE_OPTS=(-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
if [[ -f "$SSH_KEY_PATH" ]]; then
  SSH_BASE_OPTS+=(-i "$SSH_KEY_PATH")
  echo "🔑 Using SSH key: $SSH_KEY_PATH"
else
  echo "⚠️  Warning: SSH key not found at $SSH_KEY_PATH"
  echo "   You may be prompted for a password."
fi

echo "--- 🛡️ Starting Secure Mask Session ---"
echo "   SOCKS Proxy: localhost:${SOCKS_PORT}"
echo "   Remote Port: ${REMOTE_PORT}"
echo "   Server: ${USERNAME}@${SERVER_ADDRESS}"

cleanup() {
  echo ""
  echo "--- 🛑 Cleaning up tunnels ---"

  if lsof -Pi :"${SOCKS_PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   Stopping SOCKS proxy on port ${SOCKS_PORT}..."
    lsof -ti :"${SOCKS_PORT}" | xargs kill -9 2>/dev/null || true
    sleep 1
  fi

  REVERSE_TUNNEL_PIDS="$(
    ps aux | grep -E "ssh.*-R.*${REMOTE_PORT}:localhost:${SOCKS_PORT}" | grep -v grep | awk '{print $2}'
  )"
  if [[ -n "${REVERSE_TUNNEL_PIDS}" ]]; then
    echo "   Stopping reverse tunnel..."
    echo "${REVERSE_TUNNEL_PIDS}" | xargs kill -9 2>/dev/null || true
  fi

  echo "✅ Cleanup complete"
}

trap cleanup EXIT INT TERM

echo "🔍 Checking port ${SOCKS_PORT} availability..."
if lsof -Pi :"${SOCKS_PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
  echo "⚠️  Port ${SOCKS_PORT} is already in use. Cleaning up old session..."
  lsof -ti :"${SOCKS_PORT}" | xargs kill -9 2>/dev/null || true
  echo "   Waiting for port to be released..."
  for _ in {1..5}; do
    if ! lsof -Pi :"${SOCKS_PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  if lsof -Pi :"${SOCKS_PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Error: Port ${SOCKS_PORT} is still in use after cleanup attempt"
    exit 1
  fi
fi

echo "🚀 Starting local SOCKS5 proxy on port ${SOCKS_PORT}..."
ssh -D "${SOCKS_PORT}" localhost -N -f

echo "   Waiting for SOCKS proxy to initialize..."
for i in {1..5}; do
  if lsof -Pi :"${SOCKS_PORT}" -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "✅ SOCKS proxy is listening on port ${SOCKS_PORT}"
    break
  fi
  if [[ "$i" -eq 5 ]]; then
    echo "❌ Error: SOCKS proxy failed to start"
    exit 1
  fi
  sleep 1
done

echo "🔗 Creating reverse tunnel: ${SERVER_ADDRESS}:${REMOTE_PORT} -> localhost:${SOCKS_PORT}..."

# If you still see auto-executed scripts on login, run with: SKIP_PROFILE=true
SKIP_PROFILE="${SKIP_PROFILE:-false}"
if [[ "$SKIP_PROFILE" == "true" ]]; then
  REMOTE_SHELL="bash --noprofile --norc"
  echo "   (Skipping remote profile files)"
else
  REMOTE_SHELL="bash"
fi

ssh "${SSH_BASE_OPTS[@]}" -R "${REMOTE_PORT}:localhost:${SOCKS_PORT}" "${USERNAME}@${SERVER_ADDRESS}" -t \
  "export HTTP_PROXY='socks5h://localhost:${REMOTE_PORT}' && \
   export HTTPS_PROXY='socks5h://localhost:${REMOTE_PORT}' && \
   export http_proxy='socks5h://localhost:${REMOTE_PORT}' && \
   export https_proxy='socks5h://localhost:${REMOTE_PORT}' && \
   echo '' && \
   echo '✅ Proxy Mask Active' && \
   echo '   HTTP_PROXY='\${HTTP_PROXY} && \
   echo '   HTTPS_PROXY='\${HTTPS_PROXY} && \
   echo '' && \
   echo '💡 Tip: Test with: curl -v https://api.ipify.org?format=json' && \
   echo '' && \
   exec ${REMOTE_SHELL}"

