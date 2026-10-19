#!/bin/sh
# Prepare the database, then hand over to the CMD (supervisord).
set -eu

python manage.py wait_for_db --timeout 60
python manage.py migrate --noinput
python manage.py ensure_superuser

if [ "${APP_DEMO_DATA:-false}" = "true" ]; then
    # Only seeds an empty database; refuses (and we continue) once data exists.
    python manage.py seed_demo || echo "Demo data not seeded (database not empty)."
fi

exec "$@"
