from celery import shared_task

from .models import ApprovalStep, SignatureRequest
from .services import send_approval_notification


@shared_task
def send_step_notification(step_id: int) -> None:
    step = ApprovalStep.objects.get(pk=step_id)
    send_approval_notification(step)


@shared_task
def send_pending_reminders() -> int:
    count = 0
    for step in ApprovalStep.objects.filter(status=ApprovalStep.Status.ACTIVE):
        send_approval_notification(step)
        count += 1
    return count


@shared_task
def expire_stale_requests() -> int:
    return SignatureRequest.objects.filter(status=SignatureRequest.Status.PENDING).count()
