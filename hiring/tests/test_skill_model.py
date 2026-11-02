import pytest
from django.db import IntegrityError

from hiring.models import Skill


@pytest.mark.django_db
def test_database_rejects_skill_name_that_differs_only_in_case():
    Skill.objects.create(name="Python")
    # Calling objects.create() skips the form, so only the database can stop this.
    with pytest.raises(IntegrityError):
        Skill.objects.create(name="PYTHON")
