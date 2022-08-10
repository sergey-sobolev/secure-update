#!/bin/sh

export FLASK_DEBUG=1; python /app/app.py &
cd / ; python /updater/updater.py /updater/config.ini