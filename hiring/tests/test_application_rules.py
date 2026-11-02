import pytest
from django.db import IntegrityError

from hiring import rules
from hiring.models import Application, Candidate, JobOpening, Stage


@pytest.mark.django_db
def test_new_application_starts_in_applied_with_one_stage_change(candidate, opening, staff_user):
    application = rules.create_application(candidate, opening, staff_user)

    application.refresh_from_db()
    assert application.stage == Stage.APPLIED

    changes = list(application.stage_changes.all())
    assert len(changes) == 1
    assert changes[0].from_stage == ""
    assert changes[0].to_stage == Stage.APPLIED
    assert changes[0].changed_by == staff_user


@pytest.mark.django_db
def test_rules_refuse_a_second_application_for_the_same_pair(candidate, opening, staff_user):
    rules.create_application(candidate, opening, staff_user)

    # The reason the form will show.
    reason = rules.application_refusal_reason(candidate, opening)
    assert reason == "Ann Lee has already applied to Backend Developer."

    # Calling the rules directly (bypassing any form) is refused with that reason.
    with pytest.raises(rules.RuleViolation, match="already applied"):
        rules.create_application(candidate, opening, staff_user)
    assert Application.objects.count() == 1


@pytest.mark.django_db
def test_db_rejects_a_duplicate_pair_even_when_the_rules_are_bypassed(application):
    with pytest.raises(IntegrityError):
        Application.objects.create(candidate=application.candidate, opening=application.opening)


@pytest.mark.django_db
def test_rules_refuse_an_application_to_a_closed_opening(candidate, opening, staff_user):
    opening.status = JobOpening.Status.CLOSED
    opening.save()

    assert "is closed" in rules.application_refusal_reason(candidate, opening)
    with pytest.raises(rules.RuleViolation, match="is closed"):
        rules.create_application(candidate, opening, staff_user)
    assert Application.objects.count() == 0


@pytest.mark.django_db
def test_opening_picker_offers_only_open_openings_not_yet_applied_to(
    candidate, opening, staff_user
):
    closed = JobOpening.objects.create(
        title="Old Role", department="HR", location="Remote", description="x", status="closed"
    )
    other = JobOpening.objects.create(
        title="Recruiter", department="HR", location="Remote", description="x"
    )
    rules.create_application(candidate, opening, staff_user)

    offered = set(rules.openings_candidate_can_apply_to(candidate))
    assert offered == {other}
    assert closed not in offered


@pytest.mark.django_db
def test_candidate_picker_offers_only_candidates_not_yet_applied(application, opening):
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    assert set(rules.candidates_who_can_apply_to(opening)) == {bob}


@pytest.mark.django_db
def test_count_active_applications_ignores_final_stages(application, opening, staff_user):
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    rejected = rules.create_application(bob, opening, staff_user)
    rejected.stage = Stage.REJECTED
    rejected.save()

    assert rules.count_active_applications(opening) == 1
