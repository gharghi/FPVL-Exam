#!/bin/bash

if pgrep -f "bot.py" > /dev/null
then
    echo "The script is already running."
else
    echo "Starting the script."
    python bot.py &
fi