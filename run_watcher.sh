#!/bin/bash
# Start the File Watcher Service

cd "$(dirname "$0")"
python src/watcher.py
