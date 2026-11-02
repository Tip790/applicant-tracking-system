from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = "hiring"

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="hiring:application_list"), name="home"),
    path("applications/", views.application_list, name="application_list"),
    path("candidates/", views.CandidateListView.as_view(), name="candidate_list"),
    path("candidates/new/", views.CandidateCreateView.as_view(), name="candidate_create"),
    path("candidates/<int:pk>/", views.CandidateDetailView.as_view(), name="candidate_detail"),
    path("candidates/<int:pk>/edit/", views.CandidateUpdateView.as_view(), name="candidate_update"),
]
