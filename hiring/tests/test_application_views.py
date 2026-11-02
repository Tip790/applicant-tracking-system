from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from hiring import rules
from hiring.models import Application, Candidate, JobOpening, Stage, StageChange


def create_url(**params):
    key, value = next(iter(params.items()))
    return reverse("hiring:application_create") + f"?{key}={value}"


# --- Recording an application ----------------------------------------------


@pytest.mark.django_db
def test_record_from_candidate_page_redirects_back_to_candidate(
    staff_client, staff_user, candidate, opening
):
    response = staff_client.post(
        create_url(candidate=candidate.pk),
        {"candidate": candidate.pk, "opening": opening.pk},
    )

    assert response.status_code == 302
    assert response.url == candidate.get_absolute_url()
    application = Application.objects.get(candidate=candidate, opening=opening)
    assert application.stage == Stage.APPLIED
    assert application.stage_changes.get().changed_by == staff_user


@pytest.mark.django_db
def test_record_from_opening_page_redirects_back_to_opening(staff_client, candidate, opening):
    response = staff_client.post(
        create_url(opening=opening.pk),
        {"candidate": candidate.pk, "opening": opening.pk},
    )

    assert response.status_code == 302
    assert response.url == opening.get_absolute_url()
    assert Application.objects.filter(candidate=candidate, opening=opening).exists()


@pytest.mark.django_db
def test_candidate_page_form_picks_an_opening_from_valid_choices(staff_client, candidate, opening):
    JobOpening.objects.create(
        title="Old Role", department="HR", location="Remote", description="x", status="closed"
    )
    response = staff_client.get(create_url(candidate=candidate.pk))
    form = response.context["form"]

    assert form["candidate"].is_hidden
    assert list(form.fields["opening"].queryset) == [opening]


@pytest.mark.django_db
def test_opening_page_form_picks_a_candidate_from_valid_choices(staff_client, application):
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    response = staff_client.get(create_url(opening=application.opening.pk))
    form = response.context["form"]

    assert form["opening"].is_hidden
    assert list(form.fields["candidate"].queryset) == [bob]


@pytest.mark.django_db
def test_tampered_post_to_a_closed_opening_is_refused(staff_client, candidate, opening):
    opening.status = JobOpening.Status.CLOSED
    opening.save()

    response = staff_client.post(
        create_url(candidate=candidate.pk),
        {"candidate": candidate.pk, "opening": opening.pk},
    )

    assert response.status_code == 200  # form shown again with an error
    assert response.context["form"].errors
    assert Application.objects.count() == 0


@pytest.mark.django_db
def test_tampered_duplicate_post_shows_the_rule_reason(staff_client, application):
    response = staff_client.post(
        create_url(opening=application.opening.pk),
        {"candidate": application.candidate.pk, "opening": application.opening.pk},
    )

    assert response.status_code == 200
    assert Application.objects.count() == 1


@pytest.mark.django_db
def test_tampering_with_the_fixed_side_is_refused(staff_client, candidate, opening):
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    # Started from Ann's page, but the hidden candidate field was changed to Bob.
    response = staff_client.post(
        create_url(candidate=candidate.pk),
        {"candidate": bob.pk, "opening": opening.pk},
    )

    assert response.status_code == 200
    assert "candidate" in response.context["form"].errors
    assert Application.objects.count() == 0


@pytest.mark.django_db
def test_record_page_needs_a_candidate_or_opening(staff_client):
    assert staff_client.get(reverse("hiring:application_create")).status_code == 404


# --- Detail pages and the table --------------------------------------------


@pytest.mark.django_db
def test_candidate_page_lists_their_applications_with_stage_badges(staff_client, application):
    html = staff_client.get(application.candidate.get_absolute_url()).content.decode()

    assert "Backend Developer" in html
    assert '<span class="badge badge-sm badge-neutral">Applied</span>' in html
    assert create_url(candidate=application.candidate.pk) in html


@pytest.mark.django_db
def test_opening_page_shows_the_table_pre_filtered_to_that_opening(
    staff_client, staff_user, application
):
    other = JobOpening.objects.create(
        title="Recruiter", department="HR", location="Remote", description="x"
    )
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    rules.create_application(bob, other, staff_user)

    response = staff_client.get(application.opening.get_absolute_url())

    assert list(response.context["applications"]) == [application]
    assert "hiring/partials/application_table.html" in [t.name for t in response.templates]
    assert create_url(opening=application.opening.pk) in response.content.decode()


@pytest.mark.django_db
def test_closed_opening_page_does_not_offer_recording_an_application(staff_client, opening):
    opening.status = JobOpening.Status.CLOSED
    opening.save()
    html = staff_client.get(opening.get_absolute_url()).content.decode()
    assert create_url(opening=opening.pk) not in html


@pytest.mark.django_db
def test_all_applications_shows_every_column(staff_client, application):
    opening = application.opening
    opening.status = JobOpening.Status.CLOSED
    opening.save()

    response = staff_client.get(reverse("hiring:application_list"))
    html = response.content.decode()

    for heading in ["Candidate", "Opening", "Source", "Stage", "Stage history", "Time in stage"]:
        assert f"<th>{heading}</th>" in html
    assert "Ann Lee" in html
    assert "Ann.Lee@example.com" in html
    assert "Backend Developer" in html
    assert ">Closed</span>" in html
    assert "Website" in html
    assert "hiring/partials/application_row.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_stage_badges_are_colored_by_stage(staff_client, staff_user, candidate, opening):
    hired = rules.create_application(candidate, opening, staff_user)
    hired.stage = Stage.HIRED
    hired.save()
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    rejected = rules.create_application(bob, opening, staff_user)
    rejected.stage = Stage.REJECTED
    rejected.save()

    html = staff_client.get(reverse("hiring:application_list")).content.decode()

    assert '<span class="badge badge-sm badge-success">Hired</span>' in html
    assert '<span class="badge badge-sm badge-error">Rejected</span>' in html


@pytest.mark.django_db
def test_history_and_time_in_stage_come_from_stage_changes(staff_client, staff_user, application):
    # Simulate a move to Screening three days ago (moves arrive in Phase 4).
    three_days_ago = timezone.now() - timedelta(days=3)
    StageChange.objects.filter(application=application).update(
        changed_at=three_days_ago - timedelta(days=2)
    )
    move = StageChange.objects.create(
        application=application,
        from_stage=Stage.APPLIED,
        to_stage=Stage.SCREENING,
        changed_by=staff_user,
    )
    StageChange.objects.filter(pk=move.pk).update(changed_at=three_days_ago)
    application.stage = Stage.SCREENING
    application.save()

    assert abs(application.stage_entered_at() - three_days_ago) < timedelta(seconds=1)

    html = staff_client.get(reverse("hiring:application_list")).content.decode()
    assert "Applied</span> → " in html
    assert "Screening</span>" in html
    assert "3\xa0days" in html  # timesince uses a non-breaking space


# --- Close confirmation -----------------------------------------------------


@pytest.mark.django_db
def test_close_confirmation_shows_the_active_application_count(
    staff_client, staff_user, application, opening
):
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    cara = Candidate.objects.create(
        first_name="Cara", last_name="Lee", email="cara@example.com", source="referral"
    )
    rules.create_application(bob, opening, staff_user)
    rejected = rules.create_application(cara, opening, staff_user)
    rejected.stage = Stage.REJECTED
    rejected.save()

    response = staff_client.get(reverse("hiring:opening_close", args=[opening.pk]))

    assert response.status_code == 200
    assert response.context["active_count"] == 2
    assert "2 active applications are still in progress" in " ".join(
        response.content.decode().split()
    )
    opening.refresh_from_db()
    assert opening.status == JobOpening.Status.OPEN


@pytest.mark.django_db
def test_closing_leaves_existing_applications_alone(staff_client, application, opening):
    staff_client.post(reverse("hiring:opening_close", args=[opening.pk]))

    application.refresh_from_db()
    opening.refresh_from_db()
    assert opening.is_closed
    assert application.stage == Stage.APPLIED
