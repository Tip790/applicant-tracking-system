import pytest
from django.urls import reverse

from hiring.forms import CandidateForm
from hiring.models import Candidate


def candidate_data(**overrides):
    data = {
        "first_name": "Maria",
        "last_name": "Garcia",
        "email": "maria@example.com",
        "phone": "555-0100",
        "source": Candidate.Source.REFERRAL,
        "source_details": "referred by Sam in Sales",
        "notes": "Strong portfolio.",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_staff_can_create_a_candidate(staff_client):
    response = staff_client.post(reverse("hiring:candidate_create"), candidate_data())

    maria = Candidate.objects.get(email="maria@example.com")
    assert response.status_code == 302
    assert response.url == maria.get_absolute_url()
    assert maria.source == Candidate.Source.REFERRAL
    assert maria.source_details == "referred by Sam in Sales"
    assert maria.archived is False


@pytest.mark.django_db
def test_phone_is_optional(staff_client):
    staff_client.post(reverse("hiring:candidate_create"), candidate_data(phone=""))
    assert Candidate.objects.filter(email="maria@example.com").exists()


@pytest.mark.django_db
def test_required_fields_are_enforced(staff_client):
    response = staff_client.post(reverse("hiring:candidate_create"), {})
    form = response.context["form"]
    assert set(form.errors) == {"first_name", "last_name", "email", "source"}
    assert Candidate.objects.count() == 0


def test_source_is_limited_to_the_four_choices():
    form = CandidateForm()
    choices = [label for value, label in form.fields["source"].choices if value]
    assert choices == ["Website", "Job Board", "Referral", "Other"]


@pytest.mark.django_db
def test_unknown_source_is_rejected(staff_client):
    response = staff_client.post(
        reverse("hiring:candidate_create"), candidate_data(source="newspaper")
    )
    assert "source" in response.context["form"].errors
    assert Candidate.objects.count() == 0


@pytest.mark.django_db
def test_detail_page_shows_candidate_information(staff_client, candidate):
    response = staff_client.get(candidate.get_absolute_url())
    html = response.content.decode()
    assert "Ann Lee" in html
    assert "Ann.Lee@example.com" in html
    assert "Website" in html


@pytest.mark.django_db
def test_list_page_shows_candidates(staff_client, candidate):
    response = staff_client.get(reverse("hiring:candidate_list"))
    assert candidate in response.context["candidates"]
    assert candidate.get_absolute_url() in response.content.decode()


@pytest.mark.django_db
def test_staff_can_edit_a_candidate(staff_client, candidate):
    url = reverse("hiring:candidate_update", args=[candidate.pk])
    data = candidate_data(email=candidate.email, first_name="Annabel")

    response = staff_client.post(url, data)

    candidate.refresh_from_db()
    assert response.url == candidate.get_absolute_url()
    assert candidate.first_name == "Annabel"


@pytest.mark.django_db
def test_editing_can_change_only_the_capitalization_of_own_email(staff_client, candidate):
    url = reverse("hiring:candidate_update", args=[candidate.pk])
    response = staff_client.post(url, candidate_data(email="ann.lee@example.com"))

    candidate.refresh_from_db()
    assert response.status_code == 302
    assert candidate.email == "ann.lee@example.com"


@pytest.mark.django_db
def test_editing_to_another_candidates_email_is_refused(staff_client, candidate):
    other = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )
    url = reverse("hiring:candidate_update", args=[other.pk])

    response = staff_client.post(url, candidate_data(email="ANN.LEE@example.com"))

    other.refresh_from_db()
    assert response.status_code == 200
    assert other.email == "bob@example.com"
    assert candidate.get_absolute_url() in response.content.decode()
