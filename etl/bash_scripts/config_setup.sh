#!/bin/bash

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