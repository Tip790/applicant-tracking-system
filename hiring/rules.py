"""Business rules for the hiring app.

Views and forms call these functions so each rule lives in exactly one place.
Database constraints on the models back these rules up.
"""

from django.db import IntegrityError, transaction

from .models import ACTIVE_STAGES, Application, Candidate, JobOpening, Skill, Stage, StageChange


class RuleViolation(Exception):
    """Raised when an action breaks a business rule. The message explains why."""


def find_candidate_by_email(email, exclude_pk=None):
    """Return the candidate whose email matches, ignoring capitalization, or None.

    Pass `exclude_pk` when editing so a candidate doesn't clash with itself.
    """
    candidates = Candidate.objects.filter(email__iexact=email)
    if exclude_pk is not None:
        candidates = candidates.exclude(pk=exclude_pk)
    return candidates.first()


def get_or_create_skill(name):
    """Return the skill with this name, ignoring capitalization, creating it if needed.

    "python" reuses an existing "Python" instead of making a duplicate.
    """
    name = name.strip()
    existing = Skill.objects.filter(name__iexact=name).first()
    if existing:
        return existing
    return Skill.objects.create(name=name)


# --- Applications ---------------------------------------------------------


def application_refusal_reason(candidate, opening):
    """Return why this candidate can't apply to this opening, or None if they can."""
    if opening.is_closed:
        return f"{opening} is closed and isn't accepting new applications."
    if Application.objects.filter(candidate=candidate, opening=opening).exists():
        return f"{candidate} has already applied to {opening}."
    # Phase 6 adds: archived candidates can't apply.
    return None


def openings_candidate_can_apply_to(candidate):
    """Open openings this candidate hasn't applied to yet (the opening picker)."""
    return JobOpening.objects.filter(status=JobOpening.Status.OPEN).exclude(
        applications__candidate=candidate
    )


def candidates_who_can_apply_to(opening):
    """Candidates who haven't applied to this opening yet (the candidate picker)."""
    return Candidate.objects.exclude(applications__opening=opening)


def create_application(candidate, opening, user):
    """Record a new application in Applied, with the first StageChange of its history.

    Raises RuleViolation if the application isn't allowed.
    Both rows are saved together or not at all.
    """
    reason = application_refusal_reason(candidate, opening)
    if reason:
        raise RuleViolation(reason)
    try:
        with transaction.atomic():
            application = Application.objects.create(
                candidate=candidate, opening=opening, stage=Stage.APPLIED
            )
            StageChange.objects.create(
                application=application,
                from_stage="",
                to_stage=Stage.APPLIED,
                changed_by=user,
            )
    except IntegrityError:
        # Two people submitted the same pair at the same moment; the DB constraint caught it.
        raise RuleViolation(f"{candidate} has already applied to {opening}.") from None
    return application


def count_active_applications(opening):
    """How many of this opening's applications are still in progress."""
    return opening.applications.filter(stage__in=ACTIVE_STAGES).count()
