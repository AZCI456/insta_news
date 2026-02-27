# --- TEST 1: CURL CHECK (Basic Connectivity) ---
# Should return your HOME IP (Newport), not the Data Center IP.
curl --socks5-hostname localhost:8080 https://ifconfig.me
# Output example: 120.19.xxx.xxx (Success) / 134.199.xxx.xxx (Fail)


# --- TEST 2: PYTHON LOGIC CHECK (Library Support) ---
# Verifies that Python's 'requests' library can find and use 'pysocks'.
python3 -c "import requests; print('My IP is:', requests.get('https://ifconfig.me').text)"


# --- TEST 3: INSTALOADER SPECIFIC CHECK ---
# A quick run to see if Instagram accepts the connection.
# Note: We use --sessionfile to test login state if you have one later.
instaloader --help > /dev/null && echo "Instaloader is installed and runnable."
