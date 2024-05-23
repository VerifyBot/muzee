#!/bin/bash

REMOTE_USER = "nir"
REMOTE_HOST = "nirush.me"
LOCAL_PATH = "/mnt/c/users/nirch/pycharmprojects/muzee"
REMOTE_PATH = "/home/muzee/src"

# upload the server
rsync -rav -e ssh --include='*.[py|json|md|ini|txt]' --exclude='{venv,__pycache__,cache,.idea}' "$LOCAL_PATH/server" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH"