#!/bin/bash

REMOTE_USER = "nir"
REMOTE_HOST = "nirush.me"
LOCAL_PATH = "/mnt/c/users/nirch/pycharmprojects/muzee"

# upload the server
cd "$LOCAL_PATH/ui/muzee" && npm run build && firebase deploy && cd -