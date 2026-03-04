#!/bin/bash
export $(grep -v '^#' .env | xargs)
OFFSET=$(gh variable get BOT_OFFSET -R jwjo48/daily-paper-digest || echo 0)
while true; do
  export BOT_OFFSET=$OFFSET
  echo "Running bot with offset $BOT_OFFSET..."
  python3 bot_server.py > /tmp/bot.log 2>&1
  NEW_OFFSET=$(grep -o "다음 offset=[0-9]*" /tmp/bot.log | grep -o "[0-9]*" | tail -n 1)
  if [ ! -z "$NEW_OFFSET" ]; then
    OFFSET=$NEW_OFFSET
  fi
  sleep 2
done
