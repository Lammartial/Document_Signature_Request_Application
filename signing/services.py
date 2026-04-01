from __future__ import annotations

from typing import Iterable

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import UploadedFile
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from .models import ApprovalStep, AuditLog, RequestDocument, SignatureRequest


User = get_user_model()


def _log_event(
    request: SignatureRequest,
    event_type: str,
    actor_email: str = "",
    message: str = "",
    metadata: dict | None = None,
) -> None:
    AuditLog.objects.create(
        request=request,
        actor_email=actor_email,
        event_type=event_type,
        message=message,
        metadata=metadata or {},
    )


@transaction.atomic
def create_request(
    *,
    requested_by: User,
    title: str,
    details: str,
    priority: str,
    approver_emails: Iterable[str],
    document: UploadedFile,
) -> SignatureRequest:
    signature_request = SignatureRequest.objects.create(
        title=title,
        details=details,
        priority=priority,
        status=SignatureRequest.Status.PENDING,
        requested_by=requested_by,
        requester_email=requested_by.email or requested_by.username,
    )
    RequestDocument.objects.create(
        request=signature_request,
        original_file=document,
        original_name=document.name,
        mime_type=getattr(document, "content_type", ""),
    )

    steps: list[ApprovalStep] = []
    for order, email in enumerate(approver_emails, start=1):
        step = ApprovalStep.objects.create(
            request=signature_request,
            order=order,
            approver_email=email,
            status=ApprovalStep.Status.PENDING,
        )
        steps.append(step)

    first_step = steps[0]
    first_step.status = ApprovalStep.Status.ACTIVE
    first_step.save(update_fields=["status"])
    signature_request.current_step = first_step
    signature_request.status = SignatureRequest.Status.IN_PROGRESS
    signature_request.save(update_fields=["current_step", "status", "updated_at"])

    _log_event(
        signature_request,
        AuditLog.EventType.CREATED,
        actor_email=signature_request.requester_email,
        message="Request created and first approver activated.",
    )
    send_approval_notification(first_step)
    return signature_request


@transaction.atomic
def approve_step(step: ApprovalStep, *, comments: str = "", signature_data: str = "") -> SignatureRequest:
    if step.status != ApprovalStep.Status.ACTIVE:
        raise ValueError("Only the active approval step can be approved.")

    step.status = ApprovalStep.Status.APPROVED
    step.comments = comments
    step.signature_data = signature_data
    step.acted_at = timezone.now()
    step.save(update_fields=["status", "comments", "signature_data", "acted_at"])

    request = step.request
    _log_event(
        request,
        AuditLog.EventType.APPROVED,
        actor_email=step.approver_email,
        message=f"Step {step.order} approved.",
    )

    next_step = request.steps.filter(order__gt=step.order).order_by("order").first()
    if next_step:
        next_step.status = ApprovalStep.Status.ACTIVE
        next_step.save(update_fields=["status"])
        request.current_step = next_step
        request.status = SignatureRequest.Status.IN_PROGRESS
        request.save(update_fields=["current_step", "status", "updated_at"])
        send_approval_notification(next_step)
    else:
        request.current_step = None
        request.status = SignatureRequest.Status.SIGNED
        request.completed_at = timezone.now()
        request.save(update_fields=["current_step", "status", "completed_at", "updated_at"])
        _log_event(
            request,
            AuditLog.EventType.COMPLETED,
            actor_email=step.approver_email,
            message="Request fully signed.",
        )
        send_completion_notification(request)

    return request


@transaction.atomic
def reject_step(step: ApprovalStep, *, comments: str = "") -> SignatureRequest:
    if step.status != ApprovalStep.Status.ACTIVE:
        raise ValueError("Only the active approval step can be rejected.")

    step.status = ApprovalStep.Status.REJECTED
    step.comments = comments
    step.acted_at = timezone.now()
    step.save(update_fields=["status", "comments", "acted_at"])

    request = step.request
    request.current_step = None
    request.status = SignatureRequest.Status.REJECTED
    request.completed_at = timezone.now()
    request.save(update_fields=["current_step", "status", "completed_at", "updated_at"])

    _log_event(
        request,
        AuditLog.EventType.REJECTED,
        actor_email=step.approver_email,
        message=f"Step {step.order} rejected the request.",
    )
    send_completion_notification(request)
    return request


@transaction.atomic
def cancel_request(request: SignatureRequest, *, actor_email: str, reason: str) -> SignatureRequest:
    if request.status in {
        SignatureRequest.Status.SIGNED,
        SignatureRequest.Status.REJECTED,
        SignatureRequest.Status.CANCELLED,
    }:
        raise ValueError("Completed requests cannot be cancelled.")

    request.status = SignatureRequest.Status.CANCELLED
    request.cancel_reason = reason
    request.current_step = None
    request.completed_at = timezone.now()
    request.save(update_fields=["status", "cancel_reason", "current_step", "completed_at", "updated_at"])
    _log_event(
        request,
        AuditLog.EventType.CANCELLED,
        actor_email=actor_email,
        message="Request cancelled by requester.",
    )
    send_completion_notification(request)
    return request


def send_approval_notification(step: ApprovalStep) -> None:
    request = step.request
    send_mail(
        subject=f"[{request.reference_code}] Signature required for {request.title}",
        message=(
            f"You are approver #{step.order} for request {request.reference_code}.\n\n"
            f"Open the application to review the document and approve or reject it."
        ),
        from_email=None,
        recipient_list=[step.approver_email],
    )
    _log_event(
        request,
        AuditLog.EventType.APPROVAL_SENT,
        actor_email=step.approver_email,
        message=f"Approval sent to step {step.order}.",
    )


def send_completion_notification(request: SignatureRequest) -> None:
    send_mail(
        subject=f"[{request.reference_code}] Request {request.get_status_display()}",
        message=(
            f"Request {request.reference_code} has finished with status: {request.get_status_display()}.\n\n"
            f"Title: {request.title}"
        ),
        from_email=None,
        recipient_list=[request.requester_email],
    )
