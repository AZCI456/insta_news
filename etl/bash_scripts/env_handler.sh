#!/bin/bash

# --- Choose Platform-specific Path 
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    CONFIG_DIR="$APPDATA/insta_news"
else
    CONFIG_DIR="$HOME/.config/insta_news"
fi

# Ensure the directory exists
mkdir -p "$CONFIG_DIR"

# Define the config file path
CONFIG_FILE="$CONFIG_DIR/droplet_config.txt"


# --- Load Variables from the Config File ---
# This file should contain: REMOTE_IP="192.168.1.1", etc.
if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
else
    echo "⚠️ Warning: $CONFIG_FILE not found. Exiting Program with error status 1"
    exit 1
fi