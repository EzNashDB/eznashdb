#!/bin/bash
# Fails if source has translatable strings that aren't yet reflected in locale/.
# Run `python manage.py makemessages --all` and `... makemessages -d djangojs --all`
# locally, then commit the changes, to fix.
set -euo pipefail

IGNORE_ARGS=(
    --ignore=node_modules
    --ignore=.venv
    --ignore=staticfiles
    --ignore=static/vendor
    --ignore=static/dist
    --ignore=.uncommitted
)

.venv/bin/python manage.py makemessages --all --no-location "${IGNORE_ARGS[@]}"
.venv/bin/python manage.py makemessages -d djangojs --all --no-location "${IGNORE_ARGS[@]}"

# makemessages always rewrites the POT-Creation-Date header, even with no real content
# changes - ignore diff hunks that consist only of that line so this doesn't fail on
# every run.
IGNORE_TIMESTAMP=(-I '^"POT-Creation-Date')

if ! git diff --exit-code "${IGNORE_TIMESTAMP[@]}" -- locale/ > /dev/null; then
    echo "Translation catalogs in locale/ are out of date with the source." >&2
    echo "Run 'python manage.py makemessages --all' and" \
        "'python manage.py makemessages -d djangojs --all', then commit the result." >&2
    git diff "${IGNORE_TIMESTAMP[@]}" -- locale/
    exit 1
fi
