from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel


class LdapSettings(TimeStampedModel):
    """Directory login, configured in the app (one row).

    Every field can also be set through an environment variable ``LDAP_<FIELD>``
    (e.g. ``LDAP_SERVER_URI``, ``LDAP_ATTR_EMPLOYEE_NUMBER``); a set variable wins over
    the value stored here. See ``apps.accounts.services.ldap``.
    """

    enabled = models.BooleanField(_("enabled"), default=False)
    server_uri = models.CharField(
        _("server URI"),
        max_length=500,
        blank=True,
        help_text=_("e.g. ldaps://dc1.example.com; several servers comma separated (failover)."),
    )
    start_tls = models.BooleanField(
        _("StartTLS"), default=False, help_text=_("Upgrade ldap:// connections to TLS.")
    )
    verify_cert = models.BooleanField(
        _("verify certificate"),
        default=True,
        help_text=_("Check the server's TLS certificate against the trusted CAs."),
    )
    ca_cert_file = models.CharField(
        _("CA certificate file"),
        max_length=500,
        blank=True,
        help_text=_("Path to a PEM file inside the container; empty = system CAs."),
    )
    timeout = models.PositiveSmallIntegerField(_("timeout (seconds)"), default=5)

    bind_dn = models.CharField(
        _("bind DN"),
        max_length=500,
        blank=True,
        help_text=_("Service account used to look up users; empty = anonymous search."),
    )
    bind_password = models.CharField(_("bind password"), max_length=500, blank=True)

    user_search_base = models.CharField(
        _("user search base"), max_length=500, blank=True, help_text=_("e.g. OU=Staff,DC=example,DC=com")
    )
    user_filter = models.CharField(
        _("user filter"),
        max_length=500,
        default="(&(objectClass=user)(sAMAccountName={username}))",
        help_text=_("LDAP filter; {username} is replaced by the (escaped) login name."),
    )

    attr_username = models.CharField(_("username attribute"), max_length=100, default="sAMAccountName")
    attr_first_name = models.CharField(_("first name attribute"), max_length=100, default="givenName")
    attr_last_name = models.CharField(_("last name attribute"), max_length=100, default="sn")
    attr_employee_number = models.CharField(
        _("employee number attribute"), max_length=100, blank=True, default="employeeID"
    )
    attr_email = models.CharField(_("email attribute"), max_length=100, blank=True, default="mail")
    attr_job_title = models.CharField(_("job title attribute"), max_length=100, blank=True, default="title")
    attr_phone = models.CharField(_("phone attribute"), max_length=100, blank=True, default="telephoneNumber")

    create_users = models.BooleanField(
        _("create users on first login"),
        default=True,
        help_text=_("Otherwise only employees that already exist in Argus can sign in via LDAP."),
    )

    class Meta:
        verbose_name = _("LDAP settings")
        verbose_name_plural = _("LDAP settings")

    def __str__(self) -> str:
        return str(_("LDAP settings"))

    @classmethod
    def load(cls) -> LdapSettings:
        """The single settings row, created with defaults on first access."""
        obj = cls.objects.order_by("created_at").first()
        return obj or cls.objects.create()
