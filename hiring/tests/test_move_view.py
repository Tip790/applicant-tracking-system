import pytest
from django.urls import reverse

from hiring.models import JobOpening, Stage


def move_url(application):
    return reverse("hiring:application_move", args=[application.pk])


@pytest.mark.django_db
def test_tampered_illegal_move_returns_an_error_alert_and_changes_nothing(
    staff_client, application
):
    # The dropdown never offers Hired from Applied, so this POST was hand-made.
    response = staff_client.post(
        move_url(application), {"stage": Stage.HIRED}, headers={"HX-Request": "true"}
    )

    assert response.status_code == 422
    assert response["HX-Retarget"] == "#move-alert"
    html = response.content.decode()
    assert 'role="alert"' in html
    assert "alert-error" in html
    assert "Hired is only reachable from Offer." in html

    application.refresh_from_db()
    assert application.stage == Stage.APPLIED
    assert application.stage_changes.count() == 1


@pytest.mark.django_db
def test_successful_move_returns_only_the_row_fragment(staff_client, staff_user, application):
    response = staff_client.post(
        move_url(application), {"stage": Stage.SCREENING}, headers={"HX-Request": "true"}
    )

    assert response.status_code == 200
    html = response.content.decode()
    assert html.lstrip().startswith(f'<tr id="application-{application.pk}"')
    assert "<html" not in html
    assert "<table" not in html
    assert "navbar" not in html
    assert '<span class="badge badge-sm badge-info whitespace-nowrap">Screening</span>' in html
    # Any old error alert is cleared out-of-band.
    assert '<div id="move-alert" hx-swap-oob="true"></div>' in html

    application.refresh_from_db()
    assert application.stage == Stage.SCREENING
    assert application.stage_changes.last().changed_by == staff_user


@pytest.mark.django_db
def test_move_is_post_only(staff_client, application):
    response = staff_client.get(move_url(application))
    assert response.status_code == 405
    application.refresh_from_db()
    assert application.stage == Stage.APPLIED


@pytest.mark.django_db
def test_moving_a_missing_application_is_404(staff_client):
    response = staff_client.post(
        reverse("hiring:application_move", args=[999]), {"stage": Stage.SCREENING}
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_applications_on_a_closed_opening_can_still_move(staff_client, application, opening):
    opening.status = JobOpening.Status.CLOSED
    opening.save()

    response = staff_client.post(move_url(application), {"stage": Stage.SCREENING})

    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == Stage.SCREENING


# --- The Actions dropdown ---------------------------------------------------


def actions_html(staff_client, application, page_url):
    """The rendered Actions dropdown for one application on a page."""
    html = staff_client.get(page_url).content.decode()
    start = html.index(f'id="actions-{application.pk}"')
    return html[start : html.index("</td>", start)]


@pytest.mark.django_db
def test_dropdown_shows_only_legal_moves_with_their_styles(staff_client, application):
    application.stage = Stage.INTERVIEW
    application.save()
    dropdown = " ".join(
        actions_html(staff_client, application, reverse("hiring:application_list")).split()
    )

    assert f'hx-post="{move_url(application)}"' in dropdown
    assert (
        'value="final_review" class="btn btn-primary btn-sm">Advance to Final Review →' in dropdown
    )
    assert 'value="screening" class="btn btn-ghost btn-sm">← Back to Screening' in dropdown
    assert "Jump to" in dropdown
    assert 'value="applied" class="btn btn-ghost btn-xs">Applied' in dropdown
    assert 'value="offer" class="btn btn-ghost btn-xs">Offer' in dropdown
    assert 'value="rejected" class="btn btn-outline btn-error btn-sm flex-1">Reject' in dropdown
    assert 'value="withdrawn" class="btn btn-ghost btn-sm flex-1">Mark withdrawn' in dropdown
    assert 'value="hired"' not in dropdown
    assert 'value="interview"' not in dropdown


@pytest.mark.django_db
def test_hired_dropdown_shows_a_final_note_instead_of_buttons(staff_client, application):
    application.stage = Stage.HIRED
    application.save()
    dropdown = actions_html(staff_client, application, reverse("hiring:application_list"))

    assert "Hired is final." in dropdown
    assert "<button" not in dropdown  # the popover holds no move buttons


def move(staff_client, application, stage):
    return staff_client.post(
        move_url(application), {"stage": stage}, headers={"HX-Request": "true"}
    )


@pytest.mark.django_db
def test_dropdown_tracker_highlights_reached_steps(staff_client, application):
    application.stage = Stage.INTERVIEW
    application.save()
    dropdown = actions_html(staff_client, application, reverse("hiring:application_list"))

    assert dropdown.count('class="step step-primary"') == 3
    assert dropdown.count('class="step"') == 3
    for label in ["Applied", "Screening", "Interview", "Final Review", "Offer", "Hired"]:
        assert f">{label}</li>" in dropdown


@pytest.mark.django_db
def test_hired_dropdown_shows_the_full_tracker(staff_client, application):
    application.stage = Stage.HIRED
    application.save()
    dropdown = actions_html(staff_client, application, reverse("hiring:application_list"))

    assert dropdown.count('class="step step-primary"') == 6


@pytest.mark.django_db
def test_rejected_dropdown_shows_red_steps_a_note_and_only_reopen(staff_client, application):
    move(staff_client, application, Stage.INTERVIEW)
    move(staff_client, application, Stage.REJECTED)
    dropdown = " ".join(
        actions_html(staff_client, application, reverse("hiring:application_list")).split()
    )

    assert dropdown.count('class="step step-error"') == 3
    assert dropdown.count('class="step"') == 3
    assert "Rejected after Interview" in dropdown
    assert 'value="interview" class="btn btn-warning btn-sm">Reopen to Interview' in dropdown
    assert dropdown.count('name="stage"') == 1  # Reopen is the only move


@pytest.mark.django_db
def test_withdrawn_dropdown_shows_the_stage_it_was_withdrawn_from(staff_client, application):
    move(staff_client, application, Stage.SCREENING)
    move(staff_client, application, Stage.WITHDRAWN)
    dropdown = " ".join(
        actions_html(staff_client, application, reverse("hiring:application_list")).split()
    )

    assert dropdown.count('class="step step-warning"') == 2
    assert "Withdrawn from Screening" in dropdown
    assert "Reopen to Screening" in dropdown
    assert dropdown.count('name="stage"') == 1


@pytest.mark.django_db
def test_reopen_rerenders_the_row_with_the_right_tracker_and_buttons(staff_client, application):
    move(staff_client, application, Stage.INTERVIEW)
    move(staff_client, application, Stage.REJECTED)

    response = move(staff_client, application, Stage.INTERVIEW)

    assert response.status_code == 200
    html = " ".join(response.content.decode().split())
    assert html.startswith(f'<tr id="application-{application.pk}"')
    assert '<span class="badge badge-sm badge-primary whitespace-nowrap">Interview</span>' in html
    assert html.count('class="step step-primary"') == 3
    assert "step-error" not in html
    assert "Rejected after" not in html
    assert "Advance to Final Review →" in html
    assert "Reopen to" not in html
    application.refresh_from_db()
    assert application.stage == Stage.INTERVIEW


@pytest.mark.django_db
def test_tampered_reopen_to_the_wrong_stage_returns_an_error_alert(staff_client, application):
    move(staff_client, application, Stage.INTERVIEW)
    move(staff_client, application, Stage.REJECTED)

    response = move(staff_client, application, Stage.OFFER)

    assert response.status_code == 422
    assert "Rejected applications can only be reopened to Interview." in response.content.decode()
    application.refresh_from_db()
    assert application.stage == Stage.REJECTED


@pytest.mark.django_db
def test_opening_page_uses_the_same_dropdown_and_move_endpoint(staff_client, application):
    dropdown = actions_html(staff_client, application, application.opening.get_absolute_url())
    assert f'hx-post="{move_url(application)}"' in dropdown
    assert "Advance to Screening →" in dropdown
