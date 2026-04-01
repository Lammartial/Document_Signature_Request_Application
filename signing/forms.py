from django import forms

from .models import ApprovalStep, SignatureRequest


class SignatureRequestForm(forms.ModelForm):
    approver_emails = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "one approver email per line"}),
        help_text="Approvers are processed sequentially from top to bottom.",
    )

    class Meta:
        model = SignatureRequest
        fields = ("title", "priority", "details")
        widgets = {
            "details": forms.Textarea(attrs={"rows": 5}),
        }

    def clean_approver_emails(self) -> list[str]:
        raw_value = self.cleaned_data["approver_emails"]
        emails: list[str] = []
        seen: set[str] = set()
        validator = forms.EmailField().clean

        for line in raw_value.splitlines():
            email = line.strip().lower()
            if not email:
                continue
            email = validator(email)
            if email in seen:
                raise forms.ValidationError(f"Duplicate approver email: {email}")
            seen.add(email)
            emails.append(email)

        if not emails:
            raise forms.ValidationError("At least one approver is required.")
        return emails


class RequestDocumentForm(forms.Form):
    document = forms.FileField()


class ApprovalDecisionForm(forms.Form):
    action = forms.ChoiceField(
        choices=(
            (ApprovalStep.Status.APPROVED, "Approve"),
            (ApprovalStep.Status.REJECTED, "Reject"),
        ),
        widget=forms.RadioSelect,
    )
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 4}))
    signature_data = forms.CharField(required=False, widget=forms.HiddenInput())


class CancelRequestForm(forms.ModelForm):
    class Meta:
        model = SignatureRequest
        fields = ("cancel_reason",)
        widgets = {"cancel_reason": forms.Textarea(attrs={"rows": 4})}
