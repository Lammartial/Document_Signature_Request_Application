from django.urls import path

from . import views


app_name = "signing"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("requests/new/", views.SignatureRequestCreateView.as_view(), name="request-create"),
    path("requests/<uuid:pk>/", views.SignatureRequestDetailView.as_view(), name="request-detail"),
    path("requests/<uuid:pk>/cancel/", views.cancel_request_view, name="request-cancel"),
    path("steps/<int:pk>/decision/", views.approval_decision_view, name="approval-decision"),
]
