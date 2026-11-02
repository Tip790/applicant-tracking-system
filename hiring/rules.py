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


# --- Stage moves ----------------------------------------------------------


def previous_stage(application):
    """The stage the application held just before its current one, from its history.

    Returns None when the history doesn't show how it reached its current stage.
    """
    changes = list(application.stage_changes.all())  # list() uses prefetched rows
    if changes and changes[-1].to_stage == application.stage and changes[-1].from_stage:
        return Stage(changes[-1].from_stage)
    return None


def move_refusal_reason(application, to_stage):
    """Return why this move isn't allowed, or None if it is ("Flexible" rules).

    - From an active stage: any other active stage, Rejected or Withdrawn.
    - Hired only from Offer, and Hired is final.
    - Rejected or Withdrawn: only "reopen" back to the stage held just before.
    """
    current = application.stage
    if current == Stage.HIRED:
        return "Hired is final. This application can't be moved."
    if to_stage == Stage.HIRED and current != Stage.OFFER:
        return "Hired is only reachable from Offer."
    if current not in ACTIVE_STAGES:
        reopen_to = previous_stage(application)
        if reopen_to is None:
            return f"{application.get_stage_display()} applications can't be moved."
        if to_stage != reopen_to:
            return (
                f"{application.get_stage_display()} applications can only be reopened "
                f"to {reopen_to.label}."
            )
        return None
    if to_stage == current:
        return f"This application is already in {application.get_stage_display()}."
    if to_stage not in Stage.values:
        return "That isn't a hiring stage."
    # Phase 6 adds: archived candidates' applications can't be moved.
    return None


# The 1–6 progress order. "Advance" and "Back" step through this list.
PIPELINE = [*ACTIVE_STAGES, Stage.HIRED]


def move_options(application):
    """The moves the Actions dropdown offers, grouped by button style.

    Returns None when no move is allowed (e.g. Hired). Every option is checked
    with move_refusal_reason, so the buttons always match what the server allows.
    """

    def allowed(stage):
        return stage if stage and move_refusal_reason(application, stage) is None else None

    if application.stage in (Stage.REJECTED, Stage.WITHDRAWN):
        reopen = allowed(previous_stage(application))
        return {"reopen": reopen} if reopen else None
    if application.stage not in ACTIVE_STAGES:
        return None
    position = PIPELINE.index(application.stage)
    advance = allowed(PIPELINE[position + 1])
    back = allowed(PIPELINE[position - 1]) if position > 0 else None
    jumps = [
        stage
        for stage in ACTIVE_STAGES
        if stage not in (application.stage, advance, back) and allowed(stage)
    ]
    return {
        "advance": advance,
        "back": back,
        "jumps": jumps,
        "reject": allowed(Stage.REJECTED),
        "withdraw": allowed(Stage.WITHDRAWN),
    }


def progress_steps(application):
    """The 1–6 progress tracker: each pipeline stage and whether it was reached.

    Rejected and Withdrawn applications show the steps up to the stage they left from.
    """
    if application.stage in PIPELINE:
        last_reached = application.stage
    else:
        last_reached = previous_stage(application)
    reached_count = PIPELINE.index(last_reached) + 1 if last_reached in PIPELINE else 0
    return [
        {"stage": stage, "reached": position < reached_count}
        for position, stage in enumerate(PIPELINE)
    ]


def move_application(application, to_stage, user):
    """Move an application to another stage and record the move in its history.

    Raises RuleViolation if the move isn't allowed.
    The new stage and its StageChange are saved together or not at all.
    """
    reason = move_refusal_reason(application, to_stage)
    if reason:
        raise RuleViolation(reason)
    from_stage = application.stage
    with transaction.atomic():
        application.stage = to_stage
        application.save(update_fields=["stage", "updated_at"])
        StageChange.objects.create(
            application=application,
            from_stage=from_stage,
            to_stage=to_stage,
            changed_by=user,
        )
    return application


def count_active_applications(opening):
    """How many of this opening's applications are still in progress."""
    return opening.applications.filter(stage__in=ACTIVE_STAGES).count()
