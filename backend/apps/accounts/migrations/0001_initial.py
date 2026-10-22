import uuid

import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models

import apps.accounts.models.user


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="BackupCode",
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
                ("salt", models.CharField(editable=False, max_length=32)),
                ("code_hash", models.CharField(editable=False, max_length=64)),
                (
                    "used_at",
                    models.DateTimeField(blank=True, editable=False, null=True, verbose_name="used at"),
                ),
            ],
            options={
                "verbose_name": "backup code",
                "verbose_name_plural": "backup codes",
            },
        ),
        migrations.CreateModel(
            name="Department",
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
                ("name", models.CharField(max_length=100, unique=True, verbose_name="name")),
                ("code", models.CharField(blank=True, max_length=20, verbose_name="code")),
                ("cost_center", models.CharField(blank=True, max_length=30, verbose_name="cost center")),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Lower numbers come first; equal numbers by name.",
                        verbose_name="sort order",
                    ),
                ),
            ],
            options={
                "verbose_name": "department",
                "verbose_name_plural": "departments",
                "ordering": ["sort_order", "name"],
            },
        ),
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
        migrations.CreateModel(
            name="Role",
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
                ("name", models.CharField(max_length=100, unique=True, verbose_name="name")),
                ("description", models.TextField(blank=True, verbose_name="description")),
                ("permissions", models.JSONField(blank=True, default=dict, verbose_name="permissions")),
            ],
            options={
                "verbose_name": "role",
                "verbose_name_plural": "roles",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="SignInThrottle",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("key", models.CharField(max_length=200, unique=True)),
                ("failures", models.PositiveIntegerField(default=0)),
                ("window_start", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name="Team",
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
                ("name", models.CharField(max_length=100, unique=True, verbose_name="name")),
                ("code", models.CharField(blank=True, max_length=20, verbose_name="code")),
                (
                    "sort_order",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Lower numbers come first; equal numbers by name.",
                        verbose_name="sort order",
                    ),
                ),
                (
                    "ldap_group_dn",
                    models.CharField(
                        blank=True,
                        help_text="DN of a directory group; its members join the team when they sign in.",
                        max_length=500,
                        verbose_name="LDAP group",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        help_text="Gets new requests and reports that no category or model routes elsewhere.",
                        verbose_name="default team",
                    ),
                ),
            ],
            options={
                "verbose_name": "team",
                "verbose_name_plural": "teams",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="TwoFactor",
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
                (
                    "method",
                    models.CharField(
                        choices=[("email", "Code by email"), ("totp", "Authenticator app")],
                        max_length=10,
                        verbose_name="method",
                    ),
                ),
                (
                    "totp_secret",
                    models.CharField(blank=True, editable=False, max_length=64, verbose_name="app secret"),
                ),
                ("totp_last_step", models.BigIntegerField(default=0, editable=False)),
            ],
            options={
                "verbose_name": "two-factor sign-in",
                "verbose_name_plural": "two-factor sign-ins",
            },
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        error_messages={"unique": "A user with that username already exists."},
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                        verbose_name="username",
                    ),
                ),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="email address")),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined"),
                ),
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
                (
                    "employee_number",
                    models.CharField(blank=True, max_length=30, verbose_name="employee number"),
                ),
                ("job_title", models.CharField(blank=True, max_length=100, verbose_name="job title")),
                ("phone", models.CharField(blank=True, max_length=50, verbose_name="phone")),
                (
                    "is_terminal",
                    models.BooleanField(
                        default=False,
                        help_text="Shared account for the pickup terminal; it only sees prepared hand-outs.",
                        verbose_name="handover terminal",
                    ),
                ),
                (
                    "approval_exempt",
                    models.BooleanField(
                        default=False,
                        help_text="Requests go straight to IT, even for categories that need approval.",
                        verbose_name="exempt from approval",
                    ),
                ),
                (
                    "ldap_dn",
                    models.CharField(
                        blank=True,
                        editable=False,
                        help_text="Set for directory accounts; name and numbers are synced from LDAP at every login.",
                        max_length=500,
                        verbose_name="LDAP DN",
                    ),
                ),
                (
                    "language",
                    models.CharField(
                        choices=[("en", "English"), ("de", "German")],
                        default="de",
                        max_length=5,
                        verbose_name="language",
                    ),
                ),
                (
                    "notification_settings",
                    models.JSONField(blank=True, default=dict, verbose_name="email notifications"),
                ),
                (
                    "app_notification_settings",
                    models.JSONField(blank=True, default=dict, verbose_name="in-app notifications"),
                ),
                (
                    "dashboard_settings",
                    models.JSONField(blank=True, default=dict, verbose_name="dashboard layout"),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "ordering": ["last_name", "first_name", "username"],
            },
            managers=[
                ("objects", apps.accounts.models.user.CaseInsensitiveUserManager()),
            ],
        ),
    ]
