import pytest
from django.urls import reverse

from hiring import rules
from hiring.models import Candidate, JobOpening, Stage


def apply_at_stage(candidate, opening, user, stage):
    """Create an application, then put it straight into `stage`.

    Stage moves arrive in Phase 4, so tests set later stages directly for now.
    """
    application = rules.create_application(candidate, opening, user)
    application.stage = stage
    application.save(update_fields=["stage"])
    return application


def shown(response):
    """The (first name, opening title) pairs in the table."""
    return {(a.candidate.first_name, a.opening.title) for a in response.context["applications"]}


@pytest.mark.django_db
def test_search_and_filters_work_alone_and_combined(staff_client, staff_user, candidate, opening):
    recruiter = JobOpening.objects.create(
        title="Recruiter", department="HR", location="Remote", description="Find people."
    )
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    cara = Candidate.objects.create(
        first_name="Cara", last_name="Lee", email="cara@example.com", source="referral"
    )

    apply_at_stage(candidate, opening, staff_user, Stage.APPLIED)  # Ann Lee
    apply_at_stage(candidate, recruiter, staff_user, Stage.INTERVIEW)  # Ann Lee
    apply_at_stage(bob, opening, staff_user, Stage.HIRED)
    apply_at_stage(cara, recruiter, staff_user, Stage.REJECTED)

    url = reverse("hiring:application_list")
    everyone = {
        ("Ann", "Backend Developer"),
        ("Ann", "Recruiter"),
        ("Bob", "Backend Developer"),
        ("Cara", "Recruiter"),
    }
    assert shown(staff_client.get(url)) == everyone

    # Search by candidate name (first or last, any case).
    assert shown(staff_client.get(url, {"q": "lee"})) == {
        ("Ann", "Backend Developer"),
        ("Ann", "Recruiter"),
        ("Cara", "Recruiter"),
    }

    # Filter by opening.
    assert shown(staff_client.get(url, {"opening": opening.pk})) == {
        ("Ann", "Backend Developer"),
        ("Bob", "Backend Developer"),
    }

    # Filter by one stage, and by "Active only".
    assert shown(staff_client.get(url, {"stage": Stage.REJECTED})) == {("Cara", "Recruiter")}
    assert shown(staff_client.get(url, {"stage": "active"})) == {
        ("Ann", "Backend Developer"),
        ("Ann", "Recruiter"),
    }

    # All three combined.
    combined = {"q": "lee", "opening": recruiter.pk, "stage": "active"}
    assert shown(staff_client.get(url, combined)) == {("Ann", "Recruiter")}
