#!/bin/bash

# maybe default my IP - makes changing easier less typing

# --- Platform-specific Path Definition (The #ifdef equivalent) ---
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows (using APPDATA environment variable)
    CONFIG_PATH="$APPDATA/app_name"
else
    # Linux / macOS
    CONFIG_PATH="$HOME/.config/insta_news"
fi

# --- Namespace/Setup (The std::filesystem equivalent) ---
DEST_FILE="$CONFIG_PATH/droplet_config.txt"


# view the existing file contents and exit 
if [[ "$#" -gt 0 && "$1" == "-v" ]]; then
    cat "$DEST_FILE"
    exit 0
fi

# Ensure the directory exists (The fs::create_directories equivalent)
if [[ ! -d "$CONFIG_PATH" ]]; then
    mkdir -p "$CONFIG_PATH"
fi

# --- Main Logic ---
while true; do
    echo -n "Enter Droplet username (e.g. root): "
    read USERNAME

    # Check if input is not empty
    if [[ -z "$USERNAME" ]]; then
        echo "Error: Username cannot be empty."
    else
        # Save to file (equivalent to writing to an fstream)
        echo "USER=$USERNAME" > "$DEST_FILE"
        echo "Saved to: $DEST_FILE"
        break
    fi
done

# A more robust Bash-friendly IP Regex
IP_REGEX='^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$'

# 3. IP Address Loop
while true; do
    read -p "Enter your IPv4 address: " ip_addr
    if [[ $ip_addr =~ $IP_REGEX ]]; then    
        echo "SERVER_ADDRESS=$ip_addr" >> "$DEST_FILE"
        echo "Success! Config saved to $DEST_FILE"
        break
    else
        echo "Invalid format. Please enter a valid IPv4."
    fi
done


# Set default ports (reference: build_tunnel.sh)
SOCKS_PORT=1080
REMOTE_PORT=8080
# Allow override or entry of SOCKS_PORT and REMOTE_PORT
read -p "Enter SOCKS proxy local port [default: $SOCKS_PORT]: " input_socks_port
if [[ ! -z "$input_socks_port" ]]; then
    SOCKS_PORT="$input_socks_port"
fi

read -p "Enter REMOTE tunnel port [default: $REMOTE_PORT]: " input_remote_port
if [[ ! -z "$input_remote_port" ]]; then
    REMOTE_PORT="$input_remote_port"
fi

echo "SOCKS_PORT=$SOCKS_PORT" >> "$DEST_FILE"
echo "REMOTE_PORT=$REMOTE_PORT" >> "$DEST_FILE"

echo "Final config saved to $DEST_FILE:"
echo "-----------------------"
cat "$DEST_FILE"