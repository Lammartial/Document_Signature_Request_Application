from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import ApprovalStep, SignatureRequest
from .services import approve_step, create_request, reject_step


User = get_user_model()


class WorkflowServiceTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="requester",
            email="requester@example.com",
            password="password123",
        )
        self.document = SimpleUploadedFile(
            "contract.pdf",
            b"%PDF-1.4 test content",
            content_type="application/pdf",
        )

    def test_create_request_activates_first_step(self) -> None:
        request = create_request(
            requested_by=self.user,
            title="Vendor contract",
            details="Need sequential signatures.",
            priority=SignatureRequest.Priority.HIGH,
            approver_emails=["a@example.com", "b@example.com"],
            document=self.document,
        )

        self.assertEqual(request.status, SignatureRequest.Status.IN_PROGRESS)
        self.assertEqual(request.current_step.order, 1)
        self.assertEqual(request.steps.count(), 2)
        self.assertEqual(request.steps.get(order=1).status, ApprovalStep.Status.ACTIVE)

    def test_approve_moves_to_next_step(self) -> None:
        request = create_request(
            requested_by=self.user,
            title="Vendor contract",
            details="Need sequential signatures.",
            priority=SignatureRequest.Priority.HIGH,
            approver_emails=["a@example.com", "b@example.com"],
            document=self.document,
        )

        approve_step(request.steps.get(order=1), comments="Looks good")
        request.refresh_from_db()

        self.assertEqual(request.current_step.order, 2)
        self.assertEqual(request.steps.get(order=2).status, ApprovalStep.Status.ACTIVE)

    def test_reject_ends_request(self) -> None:
        request = create_request(
            requested_by=self.user,
            title="Vendor contract",
            details="Need sequential signatures.",
            priority=SignatureRequest.Priority.HIGH,
            approver_emails=["a@example.com", "b@example.com"],
            document=self.document,
        )

        reject_step(request.steps.get(order=1), comments="Missing information")
        request.refresh_from_db()

        self.assertEqual(request.status, SignatureRequest.Status.REJECTED)
        self.assertIsNone(request.current_step)
