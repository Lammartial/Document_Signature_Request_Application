import django.db.models.deletion
import uuid

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalStep",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("order", models.PositiveIntegerField()),
                ("approver_email", models.EmailField(max_length=254)),
                ("approver_name", models.CharField(blank=True, max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("active", "Active"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("skipped", "Skipped"),
                        ],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("acted_at", models.DateTimeField(blank=True, null=True)),
                ("comments", models.TextField(blank=True)),
                ("signature_data", models.TextField(blank=True)),
            ],
            options={
                "ordering": ("order",),
            },
        ),
        migrations.CreateModel(
            name="SignatureRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reference_code", models.CharField(editable=False, max_length=32, unique=True)),
                ("title", models.CharField(max_length=255)),
                ("details", models.TextField(blank=True)),
                (
                    "priority",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
                        default="medium",
                        max_length=16,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("pending", "Pending"),
                            ("in_progress", "In progress"),
                            ("signed", "Signed"),
                            ("rejected", "Rejected"),
                            ("cancelled", "Cancelled"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                ("requester_email", models.EmailField(max_length=254)),
                ("cancel_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "requested_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="signature_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.AddField(
            model_name="approvalstep",
            name="request",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="steps", to="signing.signaturerequest"),
        ),
        migrations.CreateModel(
            name="AuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("actor_email", models.EmailField(blank=True, max_length=254)),
                (
                    "event_type",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("submitted", "Submitted"),
                            ("approval_sent", "Approval sent"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("cancelled", "Cancelled"),
                            ("completed", "Completed"),
                            ("reminder_sent", "Reminder sent"),
                        ],
                        max_length=32,
                    ),
                ),
                ("message", models.TextField(blank=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "request",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="audit_logs", to="signing.signaturerequest"),
                ),
            ],
            options={
                "ordering": ("created_at",),
            },
        ),
        migrations.CreateModel(
            name="RequestDocument",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("original_file", models.FileField(upload_to="documents/original/")),
                ("working_file", models.FileField(blank=True, upload_to="documents/working/")),
                ("final_file", models.FileField(blank=True, upload_to="documents/final/")),
                ("original_name", models.CharField(max_length=255)),
                ("mime_type", models.CharField(blank=True, max_length=255)),
                ("converted_to_pdf", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "request",
                    models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="document", to="signing.signaturerequest"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="signaturerequest",
            name="current_step",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="+", to="signing.approvalstep"),
        ),
        migrations.AlterUniqueTogether(
            name="approvalstep",
            unique_together={("request", "order")},
        ),
    ]
