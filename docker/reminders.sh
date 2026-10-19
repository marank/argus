#!/bin/sh
# Sends time-based email reminders (returns due, overdue, licenses ending) once an hour.
# Each reminder is sent only once, so restarts and catch-ups are harmless.
set -u
sleep 60
while true; do
    python manage.py send_reminders || echo "send_reminders failed" >&2
    sleep 3600
done
