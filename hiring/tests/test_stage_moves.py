import pytest
from django.db import IntegrityError

from hiring import rules
from hiring.models import ACTIVE_STAGES, Application, Stage, StageChange

# Every move the Flexible rules allow: active → any other active stage,
# active → Rejected or Withdrawn, and Offer → Hired.
ALLOWED_MOVES = [
    (start, target)
    for start in ACTIVE_STAGES
    for target in [*ACTIVE_STAGES, Stage.REJECTED, Stage.WITHDRAWN]
    if start != target
] + [(Stage.OFFER, Stage.HIRED)]


@pytest.mark.django_db
def test_legal_move_updates_stage_and_records_one_stage_change(application, django_user_model):
    mover = django_user_model.objects.create_user(username="mover", password="pass12345")

    rules.move_application(application, Stage.SCREENING, mover)

    application.refresh_from_db()
    assert application.stage == Stage.SCREENING

    changes = list(application.stage_changes.all())
    assert len(changes) == 2  # creation in Applied, then this move
    move = changes[-1]
    assert move.from_stage == Stage.APPLIED
    assert move.to_stage == Stage.SCREENING
    assert move.changed_by == mover


def set_stage(application, stage):
    """Put an application straight into a stage for test setup (no history row)."""
    application.stage = stage
    application.save()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("start", "target", "reason"),
    [
        (Stage.APPLIED, Stage.HIRED, "Hired is only reachable from Offer."),
        (Stage.FINAL_REVIEW, Stage.HIRED, "Hired is only reachable from Offer."),
        (Stage.HIRED, Stage.OFFER, "Hired is final. This application can't be moved."),
        (Stage.HIRED, Stage.REJECTED, "Hired is final. This application can't be moved."),
    ],
)
def test_illegal_moves_are_refused_with_a_reason_and_change_nothing(
    application, staff_user, start, target, reason
):
    set_stage(application, start)
    history_before = application.stage_changes.count()

    with pytest.raises(rules.RuleViolation) as refusal:
        rules.move_application(application, target, staff_user)

    assert str(refusal.value) == reason
    application.refresh_from_db()
    assert application.stage == start
    assert application.stage_changes.count() == history_before


@pytest.mark.django_db
@pytest.mark.parametrize(("start", "target"), ALLOWED_MOVES)
def test_every_allowed_flexible_move_succeeds(application, staff_user, start, target):
    set_stage(application, start)

    rules.move_application(application, target, staff_user)

    application.refresh_from_db()
    assert application.stage == target
    last = application.stage_changes.last()
    assert (last.from_stage, last.to_stage, last.changed_by) == (start, target, staff_user)


@pytest.mark.django_db
@pytest.mark.parametrize("final_stage", [Stage.REJECTED, Stage.WITHDRAWN])
def test_reopen_returns_to_the_previous_stage_and_records_a_stage_change(
    application, staff_user, django_user_model, final_stage
):
    rules.move_application(application, Stage.INTERVIEW, staff_user)
    rules.move_application(application, final_stage, staff_user)
    reopener = django_user_model.objects.create_user(username="reopener", password="pass12345")

    assert rules.move_refusal_reason(application, Stage.INTERVIEW) is None
    rules.move_application(application, Stage.INTERVIEW, reopener)

    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW
    changes = list(application.stage_changes.all())
    assert len(changes) == 4  # Applied, → Interview, → final stage, reopen
    reopen = changes[-1]
    assert (reopen.from_stage, reopen.to_stage, reopen.changed_by) == (
        final_stage,
        Stage.INTERVIEW,
        reopener,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("final_stage", [Stage.REJECTED, Stage.WITHDRAWN])
@pytest.mark.parametrize(
    "target",
    # Every stage except Interview (the reopen target) and Hired (refused by its own rule).
    [stage for stage in Stage if stage not in (Stage.INTERVIEW, Stage.HIRED)],
)
def test_rejected_or_withdrawn_can_only_move_back_to_the_previous_stage(
    application, staff_user, final_stage, target
):
    rules.move_application(application, Stage.INTERVIEW, staff_user)
    rules.move_application(application, final_stage, staff_user)
    history_before = application.stage_changes.count()

    with pytest.raises(rules.RuleViolation) as refusal:
        rules.move_application(application, target, staff_user)

    assert str(refusal.value) == (
        f"{final_stage.label} applications can only be reopened to Interview."
    )
    application.refresh_from_db()
    assert application.stage == final_stage
    assert application.stage_changes.count() == history_before


@pytest.mark.django_db
def test_moving_to_the_current_stage_or_an_unknown_stage_is_refused(application, staff_user):
    with pytest.raises(rules.RuleViolation, match="already in Applied"):
        rules.move_application(application, Stage.APPLIED, staff_user)
    with pytest.raises(rules.RuleViolation, match="isn't a hiring stage"):
        rules.move_application(application, "promoted", staff_user)
    assert application.stage_changes.count() == 1


@pytest.mark.django_db
def test_stage_and_history_are_saved_together_or_not_at_all(application, staff_user, monkeypatch):
    def broken_create(**kwargs):
        raise IntegrityError("simulated failure while saving the history row")

    monkeypatch.setattr(StageChange.objects, "create", broken_create)

    with pytest.raises(IntegrityError):
        rules.move_application(application, Stage.SCREENING, staff_user)

    assert Application.objects.get(pk=application.pk).stage == Stage.APPLIED


@pytest.mark.django_db
def test_move_options_for_an_early_stage(application):
    options = rules.move_options(application)  # Applied
    assert options["advance"] == Stage.SCREENING
    assert options["back"] is None
    assert options["jumps"] == [Stage.INTERVIEW, Stage.FINAL_REVIEW, Stage.OFFER]
    assert options["reject"] == Stage.REJECTED
    assert options["withdraw"] == Stage.WITHDRAWN


@pytest.mark.django_db
def test_move_options_for_a_middle_stage(application):
    set_stage(application, Stage.INTERVIEW)
    options = rules.move_options(application)
    assert options["advance"] == Stage.FINAL_REVIEW
    assert options["back"] == Stage.SCREENING
    assert options["jumps"] == [Stage.APPLIED, Stage.OFFER]


@pytest.mark.django_db
def test_move_options_offer_advances_to_hired_and_hired_is_never_a_jump(application):
    set_stage(application, Stage.OFFER)
    options = rules.move_options(application)
    assert options["advance"] == Stage.HIRED
    assert options["back"] == Stage.FINAL_REVIEW
    assert Stage.HIRED not in options["jumps"]

    set_stage(application, Stage.INTERVIEW)
    options = rules.move_options(application)
    assert Stage.HIRED not in [options["advance"], options["back"], *options["jumps"]]


@pytest.mark.django_db
@pytest.mark.parametrize("stage", [Stage.HIRED, Stage.REJECTED, Stage.WITHDRAWN])
def test_no_moves_for_hired_or_when_history_has_no_previous_stage(application, stage):
    # set_stage skips the history, so Rejected/Withdrawn have no stage to reopen to.
    set_stage(application, stage)
    assert rules.move_options(application) is None


@pytest.mark.django_db
@pytest.mark.parametrize("final_stage", [Stage.REJECTED, Stage.WITHDRAWN])
def test_move_options_for_rejected_or_withdrawn_offer_only_reopen(
    application, staff_user, final_stage
):
    rules.move_application(application, Stage.SCREENING, staff_user)
    rules.move_application(application, final_stage, staff_user)

    assert rules.move_options(application) == {"reopen": Stage.SCREENING}


def reached_stages(application):
    return [step["stage"] for step in rules.progress_steps(application) if step["reached"]]


@pytest.mark.django_db
@pytest.mark.parametrize("position", range(len(rules.PIPELINE)))
def test_tracker_reaches_every_step_up_to_the_current_stage(application, position):
    set_stage(application, rules.PIPELINE[position])
    steps = rules.progress_steps(application)

    assert [step["stage"] for step in steps] == rules.PIPELINE
    assert reached_stages(application) == rules.PIPELINE[: position + 1]


@pytest.mark.django_db
@pytest.mark.parametrize("final_stage", [Stage.REJECTED, Stage.WITHDRAWN])
def test_tracker_for_rejected_or_withdrawn_stops_at_the_stage_they_left(
    application, staff_user, final_stage
):
    rules.move_application(application, Stage.INTERVIEW, staff_user)
    rules.move_application(application, final_stage, staff_user)

    assert reached_stages(application) == [Stage.APPLIED, Stage.SCREENING, Stage.INTERVIEW]
