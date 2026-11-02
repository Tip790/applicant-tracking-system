from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import CandidateForm
from .models import Candidate

# Every view here requires login through LoginRequiredMiddleware (see settings).


def application_list(request):
    """All Applications page. The table is built in Phase 3."""
    return render(request, "hiring/application_list.html")


class CandidateListView(ListView):
    model = Candidate
    context_object_name = "candidates"

    def get_queryset(self):
        candidates = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        if query:
            candidates = candidates.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(email__icontains=query)
            )
        return candidates

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class CandidateDetailView(DetailView):
    model = Candidate


class CandidateCreateView(CreateView):
    model = Candidate
    form_class = CandidateForm

    def form_valid(self, form):
        messages.success(self.request, "Candidate created.")
        return super().form_valid(form)


class CandidateUpdateView(UpdateView):
    model = Candidate
    form_class = CandidateForm

    def form_valid(self, form):
        messages.success(self.request, "Candidate updated.")
        return super().form_valid(form)
