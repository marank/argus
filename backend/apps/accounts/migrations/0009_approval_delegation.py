import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0008_session_hours"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalDelegation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid7,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="created at")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="updated at")),
                ("starts_on", models.DateField(verbose_name="from")),
                (
                    "ends_on",
                    models.DateField(
                        blank=True, help_text="Empty: until removed.", null=True, verbose_name="until"
                    ),
                ),
                (
                    "approver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="delegations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="approver",
                    ),
                ),
                (
                    "delegate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_delegations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="delegate",
                    ),
                ),
            ],
            options={
                "verbose_name": "approval delegation",
                "verbose_name_plural": "approval delegations",
                "ordering": ["starts_on", "created_at"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("approver", models.F("delegate")), _negated=True),
                        name="delegate_is_not_the_approver",
                        violation_error_message="You cannot delegate to yourself.",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("ends_on__isnull", True),
                            ("ends_on__gte", models.F("starts_on")),
                            _connector="OR",
                        ),
                        name="delegation_period_in_order",
                        violation_error_message="The end must not be before the start.",
                    ),
                ],
            },
        ),
    ]
