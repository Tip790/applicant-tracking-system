import pytest
from django.urls import reverse

from hiring.models import Candidate


def make_candidate(first, last, email):
    return Candidate.objects.create(
        first_name=first, last_name=last, email=email, source=Candidate.Source.WEBSITE
    )


@pytest.mark.django_db
def test_candidate_search_matches_name_or_email(staff_client):
    ann = make_candidate("Ann", "Lee", "ann.lee@example.com")
    bob = make_candidate("Bob", "Stone", "bob@acme.io")
    cara = make_candidate("Cara", "Leeds", "cara@example.com")

    def search(query):
        response = staff_client.get(reverse("hiring:candidate_list"), {"q": query})
        return set(response.context["candidates"])

    assert search("bob") == {bob}  # first name
    assert search("LEE") == {ann, cara}  # last name, ignoring case
    assert search("acme.io") == {bob}  # email
    assert search("") == {ann, bob, cara}  # empty search shows everyone
