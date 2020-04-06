#!/bin/bash
python manage.py migrate --noinput

ARGS=""

ARGS="$ARGS --log-to-terminal"
ARGS="$ARGS --port 8080"
ARGS="$ARGS --enable-sendfile"
ARGS="$ARGS --startup-log"
ARGS="$ARGS --access-log"
ARGS="$ARGS --url-alias /static static"
# Also make sure the static files are available under netboot
ARGS="$ARGS --url-alias /netboot/aarch64/static static"
ARGS="$ARGS --url-alias /netboot/x86_64/static static"
ARGS="$ARGS --url-alias /netboot/debug/aarch64/static static"
ARGS="$ARGS --url-alias /netboot/debug/x86_64/static static"

exec mod_wsgi-express start-server $ARGS wsgi.py
