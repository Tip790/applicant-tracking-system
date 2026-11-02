from django.contrib import messages
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from . import rules
from .forms import ApplicationForm, CandidateForm, JobOpeningForm
from .models import ACTIVE_STAGES, Application, Candidate, JobOpening, Stage

# Every view here requires login through LoginRequiredMiddleware (see settings).


def applications_for_table():
    """Applications with everything the table partial needs, loaded in a few queries."""
    return Application.objects.select_related("candidate", "opening").prefetch_related(
        "stage_changes"
    )


def application_list(request):
    """All Applications page: one table of every application, with search and filters.

    GET parameters (all optional, combinable):
      q        part of the candidate's first or last name
      opening  an opening pk
      stage    a stage value, or "active" for Applied through Offer
    """
    applications = applications_for_table()

    query = request.GET.get("q", "").strip()
    if query:
        applications = applications.filter(
            Q(candidate__first_name__icontains=query) | Q(candidate__last_name__icontains=query)
        )

    selected_opening = request.GET.get("opening", "")
    if selected_opening.isdigit():
        applications = applications.filter(opening_id=selected_opening)

    selected_stage = request.GET.get("stage", "")
    if selected_stage == "active":
        applications = applications.filter(stage__in=ACTIVE_STAGES)
    elif selected_stage:
        applications = applications.filter(stage=selected_stage)

    return render(
        request,
        "hiring/application_list.html",
        {
            "applications": applications,
            "openings": JobOpening.objects.all(),
            "stage_choices": Stage.choices,
            "query": query,
            "selected_opening": selected_opening,
            "selected_stage": selected_stage,
        },
    )


def application_create(request):
    """Record an application, started from a candidate page or an opening page.

    `?candidate=<pk>` fixes the candidate (pick an opening);
    `?opening=<pk>` fixes the opening (pick a candidate).
    """
    candidate = opening = None
    if request.GET.get("candidate"):
        candidate = get_object_or_404(Candidate, pk=request.GET["candidate"])
        if rules.archived_reason(candidate):
            messages.error(request, rules.archived_reason(candidate))
            return redirect(candidate)
    elif request.GET.get("opening"):
        opening = get_object_or_404(JobOpening, pk=request.GET["opening"])
    else:
        raise Http404("Start from a candidate or an opening.")

    form = ApplicationForm(request.POST or None, candidate=candidate, opening=opening)
    if request.method == "POST" and form.is_valid():
        try:
            rules.create_application(
                form.cleaned_data["candidate"], form.cleaned_data["opening"], request.user
            )
        except rules.RuleViolation as error:
            form.add_error(None, str(error))
        else:
            messages.success(request, "Application recorded.")
            return redirect(candidate or opening)

    return render(
        request,
        "hiring/application_form.html",
        {"form": form, "candidate": candidate, "opening": opening},
    )


@require_POST
def application_move(request, pk):
    """Move one application to the stage in POST["stage"] (sent by HTMX).

    Success: returns only the re-rendered table row, which HTMX swaps in place.
    Refused: returns 422 with an error alert, retargeted to the alert area above
    the table (base.html tells HTMX to swap 422 responses). The row is left alone.
    """
    application = get_object_or_404(applications_for_table(), pk=pk)
    try:
        rules.move_application(application, request.POST.get("stage", ""), request.user)
    except rules.RuleViolation as error:
        response = render(
            request,
            "hiring/partials/move_error_alert.html",
            {"application": application, "reason": str(error)},
            status=422,
        )
        response["HX-Retarget"] = "#move-alert"
        response["HX-Reswap"] = "innerHTML"
        return response
    application = applications_for_table().get(pk=pk)  # fresh history for the row
    return render(request, "hiring/partials/move_success.html", {"application": application})


class CandidateListView(ListView):
    """Candidates, with search. Archived candidates are hidden unless ?show_archived=1."""

    model = Candidate
    context_object_name = "candidates"

    def show_archived(self):
        return self.request.GET.get("show_archived") == "1"

    def get_queryset(self):
        candidates = super().get_queryset()
        if not self.show_archived():
            candidates = candidates.filter(archived=False)
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
        context["show_archived"] = self.show_archived()
        return context


class CandidateDetailView(DetailView):
    model = Candidate

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["applications"] = self.object.applications.select_related("opening")
        return context


class CandidateCreateView(CreateView):
    model = Candidate
    form_class = CandidateForm

    def form_valid(self, form):
        messages.success(self.request, "Candidate created.")
        return super().form_valid(form)


class CandidateUpdateView(UpdateView):
    model = Candidate
    form_class = CandidateForm

    def dispatch(self, request, *args, **kwargs):
        # Archived candidates are read-only: send GET and POST back to their page.
        candidate = get_object_or_404(Candidate, pk=kwargs["pk"])
        if rules.archived_reason(candidate):
            messages.error(request, rules.archived_reason(candidate))
            return redirect(candidate)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Candidate updated.")
        return super().form_valid(form)


@require_POST
def candidate_archive(request, pk):
    """Archive a candidate, unless an application is still active (the message lists them)."""
    candidate = get_object_or_404(Candidate, pk=pk)
    try:
        rules.archive_candidate(candidate)
    except rules.RuleViolation as error:
        messages.error(request, str(error))
    else:
        messages.success(request, "Candidate archived. Their record is now read-only.")
    return redirect(candidate)


@require_POST
def candidate_unarchive(request, pk):
    """Bring an archived candidate back so they can be edited and moved again."""
    candidate = get_object_or_404(Candidate, pk=pk)
    rules.unarchive_candidate(candidate)
    messages.success(request, "Candidate unarchived.")
    return redirect(candidate)


@require_POST
def candidate_delete(request, pk):
    """Delete a candidate who has no applications; otherwise suggest archiving."""
    candidate = get_object_or_404(Candidate, pk=pk)
    try:
        rules.delete_candidate(candidate)
    except rules.RuleViolation as error:
        messages.error(request, str(error))
        return redirect(candidate)
    messages.success(request, f"{candidate} was deleted.")
    return redirect("hiring:candidate_list")


class JobOpeningListView(ListView):
    model = JobOpening
    context_object_name = "openings"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("skills")


class JobOpeningDetailView(DetailView):
    model = JobOpening
    context_object_name = "opening"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # The same table as All Applications, pre-filtered to this opening.
        context["applications"] = applications_for_table().filter(opening=self.object)
        return context


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


def opening_close(request, pk):
    """GET shows a confirmation with the number of active applications; POST closes.

    Closing only stops new applications. Applications in progress keep moving.
    """
    opening = get_object_or_404(JobOpening, pk=pk)
    if request.method == "POST":
        opening.status = JobOpening.Status.CLOSED
        opening.save(update_fields=["status", "updated_at"])
        messages.success(request, "Opening closed. It no longer accepts new applications.")
        return redirect(opening)
    return render(
        request,
        "hiring/jobopening_confirm_close.html",
        {"opening": opening, "active_count": rules.count_active_applications(opening)},
    )


@require_POST
def opening_reopen(request, pk):
    """Reopen a closed opening so it accepts new applications again."""
    opening = get_object_or_404(JobOpening, pk=pk)
    opening.status = JobOpening.Status.OPEN
    opening.save(update_fields=["status", "updated_at"])
    messages.success(request, "Opening reopened.")
    return redirect(opening)
