import pytest
from django.urls import reverse

from hiring.models import Candidate


@pytest.mark.django_db
def test_duplicate_email_error_links_to_existing_candidate(staff_client, candidate):
    # The `candidate` fixture already uses "Ann.Lee@example.com".
    response = staff_client.post(
        reverse("hiring:candidate_create"),
        {
            "first_name": "Annie",
            "last_name": "Lee",
            "email": "ANN.LEE@example.com",
            "source": Candidate.Source.REFERRAL,
        },
    )

    # The form is shown again (no redirect) and nothing new is saved.
    assert response.status_code == 200
    assert Candidate.objects.count() == 1

    # The error says the candidate exists and links to the existing record.
    html = response.content.decode()
    assert "already exists" in html
    assert f'href="{candidate.get_absolute_url()}"' in html
