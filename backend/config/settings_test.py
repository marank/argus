"""Settings for the tests: the development settings with a fast password hasher.

Used by pytest and django-stubs (pyproject.toml), so the tests don't depend on the
variables of whoever runs them. CI adds DB_HOST to run them on PostgreSQL.
"""

import os

# Before the settings are read: a SECRET_KEY in the environment must not switch debug off.
os.environ.setdefault("DEBUG", "true")

from .settings import *  # noqa: F403

# Argon2 is deliberately slow; the tests create and sign in users all the time.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
# No nightly dump from a test that happens to run the backup task.
BACKUP_DIR = ""
