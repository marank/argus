import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0002_initial"),
        ("inventory", "0001_initial"),
        ("masterdata", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetRequest",
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
                ("number", models.CharField(blank=True, max_length=30, unique=True, verbose_name="number")),
                ("title", models.CharField(max_length=200, verbose_name="purpose")),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                (
                    "duration",
                    models.CharField(
                        choices=[("temporary", "Temporary"), ("permanent", "Permanent")],
                        default="temporary",
                        max_length=10,
                        verbose_name="duration",
                    ),
                ),
                ("start_date", models.DateField(verbose_name="needed from")),
                (
                    "requested_pickup_date",
                    models.DateField(blank=True, null=True, verbose_name="preferred pickup day"),
                ),
                ("end_date", models.DateField(blank=True, null=True, verbose_name="needed until")),
                (
                    "origin",
                    models.CharField(
                        choices=[
                            ("request", "Request"),
                            ("direct", "Direct hand-out"),
                            ("quick", "Quick assignment"),
                        ],
                        default="request",
                        max_length=10,
                        verbose_name="origin",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending_approval", "Awaiting approval"),
                            ("submitted", "Submitted"),
                            ("confirmed", "Confirmed"),
                            ("ready", "Ready for pickup"),
                            ("handed_out", "Handed out"),
                            ("completed", "Completed"),
                            ("rejected", "Rejected"),
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="submitted",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                (
                    "approval",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("", "Not required"),
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        default="",
                        max_length=10,
                        verbose_name="approval",
                    ),
                ),
                (
                    "approval_decided_at",
                    models.DateTimeField(blank=True, null=True, verbose_name="approval decided at"),
                ),
                ("approval_comment", models.TextField(blank=True, verbose_name="approval comment")),
                ("pickup_at", models.DateTimeField(blank=True, null=True, verbose_name="pickup at")),
                (
                    "handover_mode",
                    models.CharField(
                        choices=[
                            ("pickup", "Pickup with signature"),
                            ("collect", "Simple pickup"),
                            ("delivery", "Delivered by IT"),
                        ],
                        default="pickup",
                        help_text="Pickup requests appear on the pickup terminal once they are ready.",
                        max_length=10,
                        verbose_name="handover",
                    ),
                ),
                (
                    "skip_device_check",
                    models.BooleanField(
                        default=False,
                        help_text="The pickup terminal starts with who collects, without checking the devices.",
                        verbose_name="skip device check",
                    ),
                ),
                ("it_comment", models.TextField(blank=True, verbose_name="IT comment")),
                (
                    "reminded_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="When IT last reminded the employee to return the devices.",
                        null=True,
                        verbose_name="reminded at",
                    ),
                ),
                ("confirmed_at", models.DateTimeField(blank=True, null=True, verbose_name="confirmed at")),
                ("handed_out_at", models.DateTimeField(blank=True, null=True, verbose_name="handed out at")),
                ("completed_at", models.DateTimeField(blank=True, null=True, verbose_name="completed at")),
                (
                    "approver",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="approver",
                    ),
                ),
                (
                    "assigned_team",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="asset_requests",
                        to="accounts.team",
                        verbose_name="team",
                    ),
                ),
                (
                    "assignee",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_asset_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="assignee",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="created by",
                    ),
                ),
                (
                    "follows",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="requests.assetrequest",
                        verbose_name="follows",
                    ),
                ),
                (
                    "handled_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="handled_asset_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="handled by",
                    ),
                ),
                (
                    "pickup_location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="masterdata.location",
                        verbose_name="pickup location",
                    ),
                ),
                (
                    "prepared_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="Who marked the request ready; shown as handing out at the pickup terminal.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="prepared by",
                    ),
                ),
                (
                    "reminded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="reminded by",
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="asset_requests",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="requester",
                    ),
                ),
            ],
            options={
                "verbose_name": "request",
                "verbose_name_plural": "requests",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="AssetRequestEvent",
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
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("created", "Requested"),
                            ("direct", "Direct hand-out recorded"),
                            ("quick", "Quick assignment recorded"),
                            ("approved", "Approved"),
                            ("declined", "Not approved"),
                            ("confirmed", "Confirmed"),
                            ("rejected", "Rejected"),
                            ("cancelled", "Cancelled"),
                            ("assigned", "Assignment changed"),
                            ("allocated", "Allocated"),
                            ("released", "Allocation removed"),
                            ("ready", "Ready for pickup"),
                            ("reopened", "Back in preparation"),
                            ("rescheduled", "Handover changed"),
                            ("handed_out", "Handed out"),
                            ("returned", "Taken back"),
                            ("extended", "Loan extended"),
                            ("reminded", "Reminded to return"),
                            ("completed", "Completed"),
                        ],
                        max_length=20,
                        verbose_name="kind",
                    ),
                ),
                (
                    "at",
                    models.DateTimeField(db_index=True, default=django.utils.timezone.now, verbose_name="at"),
                ),
                ("data", models.JSONField(blank=True, default=dict, verbose_name="details")),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="by",
                    ),
                ),
                (
                    "asset_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="requests.assetrequest",
                        verbose_name="request",
                    ),
                ),
            ],
            options={
                "verbose_name": "request event",
                "verbose_name_plural": "request events",
                "ordering": ["at"],
            },
        ),
        migrations.CreateModel(
            name="AssetRequestItem",
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
                (
                    "description",
                    models.CharField(
                        blank=True,
                        help_text="Free text for something that is not in the catalog.",
                        max_length=255,
                        verbose_name="description",
                    ),
                ),
                (
                    "quantity_requested",
                    models.PositiveIntegerField(default=1, verbose_name="requested quantity"),
                ),
                (
                    "quantity_confirmed",
                    models.PositiveIntegerField(blank=True, null=True, verbose_name="confirmed quantity"),
                ),
                ("note", models.CharField(blank=True, max_length=255, verbose_name="note")),
                ("position", models.PositiveSmallIntegerField(default=0, verbose_name="position")),
                (
                    "asset_model",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="masterdata.assetmodel",
                        verbose_name="model",
                    ),
                ),
                (
                    "asset_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="requests.assetrequest",
                        verbose_name="request",
                    ),
                ),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="masterdata.category",
                        verbose_name="category",
                    ),
                ),
            ],
            options={
                "verbose_name": "request line",
                "verbose_name_plural": "request lines",
                "ordering": ["position"],
            },
        ),
        migrations.CreateModel(
            name="DeviceReturn",
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
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                ("returned_at", models.DateTimeField(auto_now_add=True, verbose_name="returned at")),
                (
                    "asset_request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="returns",
                        to="requests.assetrequest",
                        verbose_name="request",
                    ),
                ),
                (
                    "returned_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="taken back by",
                    ),
                ),
            ],
            options={
                "verbose_name": "return",
                "verbose_name_plural": "returns",
                "ordering": ["returned_at"],
            },
        ),
        migrations.CreateModel(
            name="AssetRequestAllocation",
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
                ("quantity", models.PositiveIntegerField(default=1, verbose_name="quantity")),
                ("allocated_at", models.DateTimeField(auto_now_add=True, verbose_name="allocated at")),
                (
                    "handout_note",
                    models.CharField(
                        blank=True,
                        help_text="E.g. a scratch on the lid.",
                        max_length=255,
                        verbose_name="hand-out note",
                    ),
                ),
                ("handed_out_at", models.DateTimeField(blank=True, null=True, verbose_name="handed out at")),
                ("returned_at", models.DateTimeField(blank=True, null=True, verbose_name="returned at")),
                ("returned_damaged", models.BooleanField(default=False, verbose_name="returned damaged")),
                (
                    "return_note",
                    models.CharField(
                        blank=True,
                        help_text="E.g. the condition when it came back.",
                        max_length=255,
                        verbose_name="return note",
                    ),
                ),
                (
                    "allocated_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="allocated by",
                    ),
                ),
                (
                    "asset",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="asset_request_allocations",
                        to="inventory.asset",
                        verbose_name="asset",
                    ),
                ),
                (
                    "consumable",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="asset_request_allocations",
                        to="inventory.consumable",
                        verbose_name="consumable",
                    ),
                ),
                (
                    "license",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="asset_request_allocations",
                        to="inventory.license",
                        verbose_name="license",
                    ),
                ),
                (
                    "license_assignment",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="asset_request_allocation",
                        to="inventory.licenseassignment",
                        verbose_name="license assignment",
                    ),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="allocations",
                        to="requests.assetrequestitem",
                        verbose_name="request line",
                    ),
                ),
                (
                    "device_return",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="allocations",
                        to="requests.devicereturn",
                        verbose_name="return",
                    ),
                ),
            ],
            options={
                "verbose_name": "allocation",
                "verbose_name_plural": "allocations",
                "ordering": ["allocated_at", "asset__inventory_number"],
            },
        ),
        migrations.CreateModel(
            name="Handover",
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
                (
                    "method",
                    models.CharField(
                        choices=[
                            ("signature", "Signed at pickup terminal"),
                            ("delivered", "Delivered by IT"),
                            ("direct", "Handed out by IT"),
                        ],
                        max_length=10,
                        verbose_name="method",
                    ),
                ),
                (
                    "received_by_name",
                    models.CharField(
                        help_text="Kept as text so the record stays readable if the account is removed.",
                        max_length=150,
                        verbose_name="received by (name)",
                    ),
                ),
                (
                    "signature",
                    models.TextField(
                        blank=True, help_text="PNG image as data URL.", verbose_name="signature"
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="notes")),
                ("location", models.CharField(blank=True, max_length=150, verbose_name="delivered to")),
                ("handed_out_at", models.DateTimeField(auto_now_add=True, verbose_name="handed out at")),
                (
                    "asset_request",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="handover",
                        to="requests.assetrequest",
                        verbose_name="request",
                    ),
                ),
                (
                    "handed_out_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="handed out by",
                    ),
                ),
                (
                    "received_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="received_handovers",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="received by",
                    ),
                ),
                (
                    "recorded_by",
                    models.ForeignKey(
                        blank=True,
                        help_text="The account the hand-out was recorded with, e.g. the pickup terminal.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="recorded by",
                    ),
                ),
            ],
            options={
                "verbose_name": "handover",
                "verbose_name_plural": "handovers",
            },
        ),
    ]
