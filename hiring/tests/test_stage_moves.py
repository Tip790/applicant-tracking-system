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
@pytest.mark.parametrize("start", [Stage.REJECTED, Stage.WITHDRAWN])
def test_rejected_and_withdrawn_cannot_move_yet(application, staff_user, start):
    # Phase 5 adds "Reopen to [previous stage]"; until then nothing moves them.
    set_stage(application, start)
    with pytest.raises(rules.RuleViolation, match="can't be moved"):
        rules.move_application(application, Stage.APPLIED, staff_user)


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
def test_final_stages_offer_no_moves_yet(application, stage):
    set_stage(application, stage)
    assert rules.move_options(application) is None
