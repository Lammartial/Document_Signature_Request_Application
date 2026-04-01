import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SignatureRequest(models.Model):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In progress"
        SIGNED = "signed", "Signed"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_code = models.CharField(max_length=32, unique=True, editable=False)
    title = models.CharField(max_length=255)
    details = models.TextField(blank=True)
    priority = models.CharField(max_length=16, choices=Priority.choices, default=Priority.MEDIUM)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="signature_requests")
    requester_email = models.EmailField()
    current_step = models.ForeignKey(
        "ApprovalStep",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    cancel_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.reference_code} - {self.title}"

    def save(self, *args, **kwargs):
        if not self.reference_code:
            timestamp = timezone.localtime().strftime("%Y%m%d%H%M%S")
            self.reference_code = f"DSR-{timestamp}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    @property
    def is_open(self) -> bool:
        return self.status in {self.Status.PENDING, self.Status.IN_PROGRESS}


class RequestDocument(models.Model):
    request = models.OneToOneField(SignatureRequest, on_delete=models.CASCADE, related_name="document")
    original_file = models.FileField(upload_to="documents/original/")
    working_file = models.FileField(upload_to="documents/working/", blank=True)
    final_file = models.FileField(upload_to="documents/final/", blank=True)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=255, blank=True)
    converted_to_pdf = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.original_name


class ApprovalStep(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACTIVE = "active", "Active"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        SKIPPED = "skipped", "Skipped"

    request = models.ForeignKey(SignatureRequest, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveIntegerField()
    approver_email = models.EmailField()
    approver_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    acted_at = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)
    signature_data = models.TextField(blank=True)

    class Meta:
        ordering = ("order",)
        unique_together = ("request", "order")

    def __str__(self) -> str:
        return f"{self.request.reference_code} - Step {self.order}"


class AuditLog(models.Model):
    class EventType(models.TextChoices):
        CREATED = "created", "Created"
        SUBMITTED = "submitted", "Submitted"
        APPROVAL_SENT = "approval_sent", "Approval sent"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"
        REMINDER_SENT = "reminder_sent", "Reminder sent"

    request = models.ForeignKey(SignatureRequest, on_delete=models.CASCADE, related_name="audit_logs")
    actor_email = models.EmailField(blank=True)
    event_type = models.CharField(max_length=32, choices=EventType.choices)
    message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)

    def __str__(self) -> str:
        return f"{self.request.reference_code} - {self.event_type}"
