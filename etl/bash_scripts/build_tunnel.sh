#!/bin/bash

# could also call it dig tunnel heh heh

# cleanup function - runs at early exit (ctrl + c etc)
trap "lsof -ti :$SOCKS_PORT | xargs kill -9 2>/dev/null" EXIT

# source config file
source "$(dirname "$0")/env_handler.sh"

echo "--- 🛡️ Starting Secure Mask Session ---"

# 1. Check if SOCKS_PORT is already in use - kill it if it is still active (avoids port in already in use error)
if lsof -Pi :$SOCKS_PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ Port $SOCKS_PORT is already in use. Cleaning up old session..."
    lsof -ti :$SOCKS_PORT | xargs kill -9
fi

# 2. Start local SOCKS5 proxy in background
ssh -D $SOCKS_PORT localhost -N -f

# 3. Create the Reverse Tunnel and log in
echo "🔗 Tunneling through $SERVER_ADDRESS..."

ssh -R ${REMOTE_PORT}:localhost:${SOCKS_PORT} ${USER}@${SERVER_ADDRESS} -t \
    "export HTTP_PROXY='socks5h://localhost:${REMOTE_PORT}'; \
     export HTTPS_PROXY='socks5h://localhost:${REMOTE_PORT}'; \
     echo '✅ Proxy Mask Active (socks5h)'; \
     bash --login;
     cd dev/insta_news/etl/tests && source .venv/bin/activate && python3 insta_scraper_concept.py;
     exit;"

# 4. Cleanup
echo "--- 🛑 Closing Tunnels ---"
lsof -ti :$SOCKS_PORT | xargs kill -9 2>/dev/null