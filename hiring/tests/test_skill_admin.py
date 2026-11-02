import pytest
from django.urls import reverse

from hiring.models import JobOpening, Skill


@pytest.mark.django_db
def test_superuser_can_merge_duplicate_skills_in_admin(client, django_user_model, opening):
    boss = django_user_model.objects.create_superuser(username="boss", password="pass12345")
    client.force_login(boss)
    javascript = Skill.objects.create(name="JavaScript")
    js = Skill.objects.create(name="JS")
    other = JobOpening.objects.create(
        title="Designer", department="Design", location="Remote", description="Design."
    )
    opening.skills.add(javascript)
    other.skills.add(js)

    client.post(
        reverse("admin:hiring_skill_changelist"),
        {"action": "merge_skills", "_selected_action": [javascript.pk, js.pk]},
    )

    # The oldest skill is kept, the duplicate is gone, and both openings use the kept one.
    assert list(Skill.objects.all()) == [javascript]
    assert list(opening.skills.all()) == [javascript]
    assert list(other.skills.all()) == [javascript]
