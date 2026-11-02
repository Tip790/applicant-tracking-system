from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "hiring"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="hiring:application_list"), name="home"),
    path("applications/", views.application_list, name="application_list"),
    path("applications/new/", views.application_create, name="application_create"),
    path("candidates/", views.CandidateListView.as_view(), name="candidate_list"),
    path("candidates/new/", views.CandidateCreateView.as_view(), name="candidate_create"),
    path("candidates/<int:pk>/", views.CandidateDetailView.as_view(), name="candidate_detail"),
    path("candidates/<int:pk>/edit/", views.CandidateUpdateView.as_view(), name="candidate_update"),
    path("openings/", views.JobOpeningListView.as_view(), name="opening_list"),
    path("openings/new/", views.JobOpeningCreateView.as_view(), name="opening_create"),
    path("openings/<int:pk>/", views.JobOpeningDetailView.as_view(), name="opening_detail"),
    path("openings/<int:pk>/edit/", views.JobOpeningUpdateView.as_view(), name="opening_update"),
    path("openings/<int:pk>/close/", views.opening_close, name="opening_close"),
    path("openings/<int:pk>/reopen/", views.opening_reopen, name="opening_reopen"),
]
