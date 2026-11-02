import pytest
from django.urls import reverse

from hiring.models import JobOpening


@pytest.mark.django_db
def test_close_and_reopen_work_repeatedly_and_only_on_post(staff_client, opening):
    close_url = reverse("hiring:opening_close", args=[opening.pk])
    reopen_url = reverse("hiring:opening_reopen", args=[opening.pk])

    # A plain GET (e.g. following a link) never closes the opening.
    staff_client.get(close_url)
    opening.refresh_from_db()
    assert opening.status == JobOpening.Status.OPEN

    # Close and reopen twice in a row to show it works any number of times.
    for _ in range(2):
        response = staff_client.post(close_url)
        assert response.url == opening.get_absolute_url()
        opening.refresh_from_db()
        assert opening.status == JobOpening.Status.CLOSED

        # A GET never reopens it either.
        staff_client.get(reopen_url)
        opening.refresh_from_db()
        assert opening.status == JobOpening.Status.CLOSED

        response = staff_client.post(reopen_url)
        assert response.url == opening.get_absolute_url()
        opening.refresh_from_db()
        assert opening.status == JobOpening.Status.OPEN
