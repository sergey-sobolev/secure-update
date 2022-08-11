#!/bin/bash

unzip -o $1 -d $2
# touch the file to ensure flask re-reads it - this is to improve e2e test stability
sleep 0.2
touch $2/*.py