import uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower
from django.utils.translation import gettext_lazy as _


class CaseInsensitiveUserManager(UserManager):
    """Usernames are compared without regard to case, like in Active Directory.

    ``get_by_natural_key`` is what the login (``ModelBackend``) and management
    commands use; the stored username keeps the spelling it was created with.
    """

    def get_by_natural_key(self, username):
        return self.get(**{f"{self.model.USERNAME_FIELD}__iexact": username})


class User(AbstractUser):
    """Employee account. ``is_staff`` marks members of the IT department."""

    objects = CaseInsensitiveUserManager()

    class Language(models.TextChoices):
        ENGLISH = "en", _("English")
        GERMAN = "de", _("German")

    id = models.UUIDField(_("ID"), primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(
        "accounts.Department",
        verbose_name=_("department"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="members",
    )
    employee_number = models.CharField(_("employee number"), max_length=30, blank=True)
    job_title = models.CharField(_("job title"), max_length=100, blank=True)
    phone = models.CharField(_("phone"), max_length=50, blank=True)
    is_terminal = models.BooleanField(
        _("handover terminal"),
        default=False,
        help_text=_("Shared account for the pickup terminal; it only sees prepared hand-outs."),
    )
    terminal_location = models.ForeignKey(
        "masterdata.Location",
        verbose_name=_("terminal site"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
        help_text=_("Pickup terminal only: lists pickups at this location and below; empty lists all."),
    )
    ldap_dn = models.CharField(
        _("LDAP DN"),
        max_length=500,
        blank=True,
        editable=False,
        help_text=_("Set for directory accounts; name and numbers are synced from LDAP at every login."),
    )
    language = models.CharField(
        _("language"), max_length=5, choices=Language.choices, default=Language.GERMAN
    )
    # Email notifications the user switched off: {event: false}; missing means on.
    notification_settings = models.JSONField(_("email notifications"), default=dict, blank=True)

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["last_name", "first_name", "username"]
        constraints = [
            # "Anna" and "anna" are the same person; only one of them may exist.
            models.UniqueConstraint(
                Lower("username"),
                name="unique_username_ignoring_case",
                violation_error_message=_("A user with this username already exists."),
            ),
        ]

    def __str__(self) -> str:
        return self.display_name

    @property
    def display_name(self) -> str:
        return self.get_full_name() or self.username

    @property
    def is_ldap_user(self) -> bool:
        return bool(self.ldap_dn)

    @property
    def is_it_staff(self) -> bool:
        return self.is_staff or self.is_superuser
