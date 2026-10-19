import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LdapSettings",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                ("enabled", models.BooleanField(default=False, verbose_name="enabled")),
                (
                    "server_uri",
                    models.CharField(
                        blank=True,
                        help_text="e.g. ldaps://dc1.example.com; several servers comma separated (failover).",
                        max_length=500,
                        verbose_name="server URI",
                    ),
                ),
                (
                    "start_tls",
                    models.BooleanField(
                        default=False,
                        help_text="Upgrade ldap:// connections to TLS.",
                        verbose_name="StartTLS",
                    ),
                ),
                (
                    "verify_cert",
                    models.BooleanField(
                        default=True,
                        help_text="Check the server's TLS certificate against the trusted CAs.",
                        verbose_name="verify certificate",
                    ),
                ),
                (
                    "ca_cert_file",
                    models.CharField(
                        blank=True,
                        help_text="Path to a PEM file inside the container; empty = system CAs.",
                        max_length=500,
                        verbose_name="CA certificate file",
                    ),
                ),
                ("timeout", models.PositiveSmallIntegerField(default=5, verbose_name="timeout (seconds)")),
                (
                    "bind_dn",
                    models.CharField(
                        blank=True,
                        help_text="Service account used to look up users; empty = anonymous search.",
                        max_length=500,
                        verbose_name="bind DN",
                    ),
                ),
                ("bind_password", models.CharField(blank=True, max_length=500, verbose_name="bind password")),
                (
                    "user_search_base",
                    models.CharField(
                        blank=True,
                        help_text="e.g. OU=Staff,DC=example,DC=com",
                        max_length=500,
                        verbose_name="user search base",
                    ),
                ),
                (
                    "user_filter",
                    models.CharField(
                        default="(&(objectClass=user)(sAMAccountName={username}))",
                        help_text="LDAP filter; {username} is replaced by the (escaped) login name.",
                        max_length=500,
                        verbose_name="user filter",
                    ),
                ),
                (
                    "attr_username",
                    models.CharField(
                        default="sAMAccountName", max_length=100, verbose_name="username attribute"
                    ),
                ),
                (
                    "attr_first_name",
                    models.CharField(
                        default="givenName", max_length=100, verbose_name="first name attribute"
                    ),
                ),
                (
                    "attr_last_name",
                    models.CharField(default="sn", max_length=100, verbose_name="last name attribute"),
                ),
                (
                    "attr_employee_number",
                    models.CharField(
                        blank=True,
                        default="employeeID",
                        max_length=100,
                        verbose_name="employee number attribute",
                    ),
                ),
                (
                    "attr_email",
                    models.CharField(
                        blank=True, default="mail", max_length=100, verbose_name="email attribute"
                    ),
                ),
                (
                    "attr_job_title",
                    models.CharField(
                        blank=True, default="title", max_length=100, verbose_name="job title attribute"
                    ),
                ),
                (
                    "attr_phone",
                    models.CharField(
                        blank=True, default="telephoneNumber", max_length=100, verbose_name="phone attribute"
                    ),
                ),
                (
                    "create_users",
                    models.BooleanField(
                        default=True,
                        help_text="Otherwise only employees that already exist in Argus can sign in via LDAP.",
                        verbose_name="create users on first login",
                    ),
                ),
            ],
            options={
                "verbose_name": "LDAP settings",
                "verbose_name_plural": "LDAP settings",
            },
        ),
        migrations.AddField(
            model_name="user",
            name="ldap_dn",
            field=models.CharField(
                blank=True,
                editable=False,
                help_text="Set for directory accounts; name and numbers are synced from LDAP at every login.",
                max_length=500,
                verbose_name="LDAP DN",
            ),
        ),
    ]
