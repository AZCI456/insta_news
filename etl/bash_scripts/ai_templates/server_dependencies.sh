# --- CRITICAL: DISABLE PROXY FOR INSTALLATION ---
# If you don't do this, pip will try to tunnel through a connection
# it doesn't understand yet and fail with "OSError".
unset HTTP_PROXY
unset HTTPS_PROXY

# --- INSTALLATION COMMANDS ---
# 1. Update package list (Standard Linux practice)
apt-get update

# 2. Install Python3 and Pip (if not already present)
apt-get install python3-pip -y

# 3. Install Python Libraries
#    - instaloader: The scraping logic
#    - pysocks: REQUIRED for SOCKS5 proxy support (fixes "Missing dependencies" error)
#    - requests: For general HTTP calls
pip3 install instaloader pysocks requests

# --- RE-ENABLE PROXY FOR SCRAPING ---
# Now that tools are installed, turn the tunnel back on.
export HTTP_PROXY="socks5h://localhost:8080"
export HTTPS_PROXY="socks5h://localhost:8080"
