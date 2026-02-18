# --- STEP 1: ON YOUR MAC (LOCAL) ---
# 1. Prevent Mac from sleeping (Optional but recommended for automation)
#    - Schedule wake up at 8:00 AM every day
sudo pmset repeat wake MTWRFSU 08:00:00

# 2. Start the Local SOCKS5 Proxy
#    - Opens port 1080 on your Mac to act as the "exit node"
#    - (-D) Dynamic Forwarding, (-N) No command/Silent
ssh -D 1080 localhost -N

# 3. Create the Reverse Tunnel to Server
#    - Connects to Droplet and forwards Server:8080 -> Mac:1080
#    - Replace [USER] and [IP] with your Droplet details
#    - (-R) Reverse Port Forward, (-f) Background mode
ssh -R 8080:localhost:1080 [USER]@[DROPLET_IP] -N -f


# --- STEP 2: ON YOUR SERVER (REMOTE) ---
# 4. SSH into the Server normally to control it - or just login on termius
ssh [USER]@[DROPLET_IP]

# 5. Enable the "Mask" for the current session
#    - Tells Linux to route all HTTP/HTTPS traffic through the tunnel
#    - 'socks5h' ensures DNS lookups happen on the Mac (Preventing Leaks)
export HTTP_PROXY="socks5h://localhost:8080"
export HTTPS_PROXY="socks5h://localhost:8080"
