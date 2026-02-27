#!/bin/bash

# Example cron syntax to run build_tunnel.sh
# (edit crontab with: crontab -e)

# Run every day at 08:05 using system Python user env and log output:
#
# 5 8 * * * /bin/bash -lc 'cd /Users/aaroncoelho-irani/dev/insta_news/etl/bash_scripts && ./build_tunnel.sh >> /Users/aaroncoelho-irani/dev/insta_news/etl/bash_scripts/build_tunnel_cron.log 2>&1'

