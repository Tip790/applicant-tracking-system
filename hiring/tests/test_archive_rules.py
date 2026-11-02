import pytest

from hiring import rules
from hiring.models import Application, Candidate, JobOpening, Stage


def make_opening(title):
    return JobOpening.objects.create(
        title=title, department="Engineering", location="Remote", description="x"
    )


@pytest.mark.django_db
def test_archiving_is_refused_while_an_application_is_active_and_lists_them(
    candidate, application, staff_user
):
    # Ann has two active applications and one final one.
    rules.move_application(application, Stage.INTERVIEW, staff_user)
    rules.create_application(candidate, make_opening("Frontend Developer"), staff_user)
    rejected = rules.create_application(candidate, make_opening("Data Analyst"), staff_user)
    rules.move_application(rejected, Stage.REJECTED, staff_user)

    with pytest.raises(rules.RuleViolation) as refusal:
        rules.archive_candidate(candidate)

    reason = str(refusal.value)
    assert reason.startswith("Ann Lee can't be archived while these applications are active:")
    assert "Backend Developer (Interview)" in reason
    assert "Frontend Developer (Applied)" in reason
    assert "Data Analyst" not in reason  # final applications don't block archiving
    candidate.refresh_from_db()
    assert candidate.archived is False


@pytest.mark.django_db
def test_deleting_is_refused_once_a_candidate_has_any_application(
    candidate, application, staff_user
):
    # Even a final (Rejected) application is hiring history that must be kept.
    rules.move_application(application, Stage.REJECTED, staff_user)
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )

    with pytest.raises(rules.RuleViolation) as refusal:
        rules.delete_candidate(candidate)

    assert str(refusal.value) == (
        "Ann Lee can't be deleted because they have applications. "
        "Archive the candidate instead to keep their hiring history."
    )
    assert Candidate.objects.filter(pk=candidate.pk).exists()
    assert Application.objects.filter(pk=application.pk).exists()

    # A candidate with no applications (e.g. created by mistake) can be deleted.
    rules.delete_candidate(bob)
    assert not Candidate.objects.filter(pk=bob.pk).exists()
