from django.db import models
from django.utils import timezone


class SignInThrottle(models.Model):
    """Wrong passwords or codes per account in the current window; see ``services.throttle``.

    Kept in the database so every worker process counts the same attempts.
    """

    key = models.CharField(max_length=200, unique=True)
    failures = models.PositiveIntegerField(default=0)
    window_start = models.DateTimeField(default=timezone.now, db_index=True)

    def __str__(self) -> str:
        return f"{self.key}: {self.failures}"
