import pytest
from django.db import IntegrityError

from hiring.models import Candidate


@pytest.mark.django_db
def test_database_rejects_email_that_differs_only_in_case(candidate):
    # The `candidate` fixture already uses "Ann.Lee@example.com".
    # Calling objects.create() skips the form, so only the database can stop this.
    with pytest.raises(IntegrityError):
        Candidate.objects.create(
            first_name="Annie",
            last_name="Lee",
            email="ann.lee@EXAMPLE.com",
            source=Candidate.Source.REFERRAL,
        )
