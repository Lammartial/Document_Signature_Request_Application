from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import CreateView, DetailView, TemplateView

from .forms import ApprovalDecisionForm, CancelRequestForm, RequestDocumentForm, SignatureRequestForm
from .models import ApprovalStep, SignatureRequest
from .services import approve_step, cancel_request, create_request, reject_step


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "signing/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_email = self.request.user.email or "__missing__"
        context["my_requests"] = SignatureRequest.objects.filter(requested_by=self.request.user)
        context["pending_steps"] = ApprovalStep.objects.filter(
            approver_email__iexact=user_email,
            status=ApprovalStep.Status.ACTIVE,
        )
        return context


class SignatureRequestCreateView(LoginRequiredMixin, CreateView):
    template_name = "signing/request_form.html"
    form_class = SignatureRequestForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault("document_form", RequestDocumentForm())
        return context

    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        form = self.get_form()
        document_form = RequestDocumentForm(request.POST, request.FILES)
        if form.is_valid() and document_form.is_valid():
            signature_request = create_request(
                requested_by=request.user,
                title=form.cleaned_data["title"],
                details=form.cleaned_data["details"],
                priority=form.cleaned_data["priority"],
                approver_emails=form.cleaned_data["approver_emails"],
                document=document_form.cleaned_data["document"],
            )
            messages.success(request, "Request created and first approver notified.")
            return redirect("signing:request-detail", pk=signature_request.pk)

        return self.render_to_response(self.get_context_data(form=form, document_form=document_form))


class SignatureRequestDetailView(LoginRequiredMixin, DetailView):
    model = SignatureRequest
    template_name = "signing/request_detail.html"
    context_object_name = "request_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_form"] = CancelRequestForm(instance=self.object)
        active_step = self.object.steps.filter(status=ApprovalStep.Status.ACTIVE).first()
        user_email = (self.request.user.email or "").lower()
        if active_step and active_step.approver_email.lower() == user_email:
            context["decision_form"] = ApprovalDecisionForm()
            context["active_step"] = active_step
        return context


@login_required
def approval_decision_view(request: HttpRequest, pk: int) -> HttpResponse:
    step = get_object_or_404(ApprovalStep, pk=pk)
    user_email = (request.user.email or "").lower()
    if step.approver_email.lower() != user_email:
        messages.error(request, "You are not allowed to act on this step.")
        return redirect("signing:request-detail", pk=step.request_id)

    form = ApprovalDecisionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        action = form.cleaned_data["action"]
        comments = form.cleaned_data["comments"]
        signature_data = form.cleaned_data["signature_data"]
        if action == ApprovalStep.Status.APPROVED:
            approve_step(step, comments=comments, signature_data=signature_data)
            messages.success(request, "Approval recorded.")
        else:
            reject_step(step, comments=comments)
            messages.success(request, "Rejection recorded.")
        return redirect("signing:request-detail", pk=step.request_id)

    return render(request, "signing/approval_form.html", {"form": form, "step": step})


@login_required
def cancel_request_view(request: HttpRequest, pk) -> HttpResponse:
    request_obj = get_object_or_404(SignatureRequest, pk=pk, requested_by=request.user)
    form = CancelRequestForm(request.POST or None, instance=request_obj)
    if request.method == "POST" and form.is_valid():
        cancel_request(
            request_obj,
            actor_email=request.user.email,
            reason=form.cleaned_data["cancel_reason"],
        )
        messages.success(request, "Request cancelled.")
    return redirect(reverse("signing:request-detail", kwargs={"pk": request_obj.pk}))
