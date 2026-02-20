cat <<EOF > ~/Library/LaunchAgents/com.aaron.buildtunnel.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.aaron.buildtunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/aaroncoelho-irani/dev/insta_news/etl/bash_scripts/build_tunnel.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>5</integer>
    </dict>
    <key>AbandonProcessGroup</key>
    <true/>
</dict>
</plist>
EOF

# Load the agent
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.aaron.buildtunnel.plist
