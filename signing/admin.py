from django.contrib import admin

from .models import ApprovalStep, AuditLog, RequestDocument, SignatureRequest


class RequestDocumentInline(admin.StackedInline):
    model = RequestDocument
    extra = 0


class ApprovalStepInline(admin.TabularInline):
    model = ApprovalStep
    extra = 0
    ordering = ("order",)


@admin.register(SignatureRequest)
class SignatureRequestAdmin(admin.ModelAdmin):
    list_display = ("reference_code", "title", "status", "priority", "requested_by", "created_at")
    list_filter = ("status", "priority", "created_at")
    search_fields = ("reference_code", "title", "requested_by__username", "requester_email")
    inlines = [RequestDocumentInline, ApprovalStepInline]


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("request", "event_type", "actor_email", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("request__reference_code", "actor_email", "message")
