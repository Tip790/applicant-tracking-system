import pytest

from hiring.models import Candidate, JobOpening


@pytest.fixture
def staff_user(django_user_model):
    """An ordinary staff member (not a superuser)."""
    return django_user_model.objects.create_user(username="staff", password="pass12345")


@pytest.fixture
def staff_client(client, staff_user):
    """A test client logged in as an ordinary staff member."""
    client.force_login(staff_user)
    return client


@pytest.fixture
def candidate(db):
    return Candidate.objects.create(
        first_name="Ann",
        last_name="Lee",
        email="Ann.Lee@example.com",
        source=Candidate.Source.WEBSITE,
    )


@pytest.fixture
def opening(db):
    """An open job opening with no skills."""
    return JobOpening.objects.create(
        title="Backend Developer",
        department="Engineering",
        location="Amarillo, TX",
        description="Build and maintain our Django services.",
    )
