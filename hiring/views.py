from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import CandidateForm, JobOpeningForm
from .models import Candidate, JobOpening

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


class JobOpeningListView(ListView):
    model = JobOpening
    context_object_name = "openings"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("skills")


class JobOpeningDetailView(DetailView):
    model = JobOpening
    context_object_name = "opening"


class JobOpeningCreateView(CreateView):
    model = JobOpening
    form_class = JobOpeningForm

    def form_valid(self, form):
        messages.success(self.request, "Opening created.")
        return super().form_valid(form)


class JobOpeningUpdateView(UpdateView):
    model = JobOpening
    form_class = JobOpeningForm

    def form_valid(self, form):
        messages.success(self.request, "Opening updated.")
        return super().form_valid(form)


@require_POST
def opening_close(request, pk):
    """Close an opening so it stops accepting new applications."""
    opening = get_object_or_404(JobOpening, pk=pk)
    opening.status = JobOpening.Status.CLOSED
    opening.save(update_fields=["status", "updated_at"])
    messages.success(request, "Opening closed. It no longer accepts new applications.")
    return redirect(opening)


@require_POST
def opening_reopen(request, pk):
    """Reopen a closed opening so it accepts new applications again."""
    opening = get_object_or_404(JobOpening, pk=pk)
    opening.status = JobOpening.Status.OPEN
    opening.save(update_fields=["status", "updated_at"])
    messages.success(request, "Opening reopened.")
    return redirect(opening)
