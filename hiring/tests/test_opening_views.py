import pytest
from django.urls import reverse

from hiring.models import JobOpening, Skill


def opening_data(**overrides):
    data = {
        "title": "Frontend Developer",
        "department": "Engineering",
        "location": "Canyon, TX",
        "description": "Build our staff-facing screens.",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_staff_can_create_an_opening(staff_client):
    response = staff_client.post(reverse("hiring:opening_create"), opening_data())

    opening = JobOpening.objects.get(title="Frontend Developer")
    assert response.status_code == 302
    assert response.url == opening.get_absolute_url()
    assert opening.department == "Engineering"
    assert opening.status == JobOpening.Status.OPEN


@pytest.mark.django_db
def test_required_opening_fields_are_enforced(staff_client):
    response = staff_client.post(reverse("hiring:opening_create"), {})
    form = response.context["form"]
    assert set(form.errors) == {"title", "department", "location", "description"}
    assert JobOpening.objects.count() == 0


@pytest.mark.django_db
def test_staff_can_edit_an_opening(staff_client, opening):
    url = reverse("hiring:opening_update", args=[opening.pk])
    response = staff_client.post(url, opening_data(title="Senior Backend Developer"))

    opening.refresh_from_db()
    assert response.url == opening.get_absolute_url()
    assert opening.title == "Senior Backend Developer"


@pytest.mark.django_db
def test_editing_does_not_change_status(staff_client, opening):
    opening.status = JobOpening.Status.CLOSED
    opening.save()
    url = reverse("hiring:opening_update", args=[opening.pk])

    staff_client.post(url, opening_data())

    opening.refresh_from_db()
    assert opening.status == JobOpening.Status.CLOSED


@pytest.mark.django_db
def test_detail_page_shows_opening_and_its_skills(staff_client, opening):
    opening.skills.add(Skill.objects.create(name="Django"))
    html = staff_client.get(opening.get_absolute_url()).content.decode()
    assert "Backend Developer" in html
    assert "Engineering" in html
    assert "Amarillo, TX" in html
    assert "Django" in html


@pytest.mark.django_db
def test_list_shows_status_with_closed_badge(staff_client, opening):
    JobOpening.objects.create(
        title="Recruiter",
        department="HR",
        location="Remote",
        description="Find great people.",
        status=JobOpening.Status.CLOSED,
    )
    response = staff_client.get(reverse("hiring:opening_list"))
    html = response.content.decode()

    assert len(response.context["openings"]) == 2
    assert opening.get_absolute_url() in html
    assert ">Open</span>" in html
    assert ">Closed</span>" in html


@pytest.mark.django_db
def test_detail_page_offers_close_or_reopen_to_match_status(staff_client, opening):
    close_url = reverse("hiring:opening_close", args=[opening.pk])
    reopen_url = reverse("hiring:opening_reopen", args=[opening.pk])

    html = staff_client.get(opening.get_absolute_url()).content.decode()
    assert close_url in html
    assert reopen_url not in html

    staff_client.post(close_url)
    html = staff_client.get(opening.get_absolute_url()).content.decode()
    assert reopen_url in html
    assert close_url not in html
    assert ">Closed</span>" in html
