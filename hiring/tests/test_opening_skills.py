import pytest
from django.urls import reverse

from hiring.models import JobOpening, Skill


@pytest.mark.django_db
def test_new_skill_that_differs_only_in_case_reuses_the_existing_skill(staff_client):
    python = Skill.objects.create(name="Python")

    staff_client.post(
        reverse("hiring:opening_create"),
        {
            "title": "Data Analyst",
            "department": "Analytics",
            "location": "Remote",
            "description": "Turn data into decisions.",
            "new_skill": "python",
        },
    )

    # No duplicate skill was created...
    assert Skill.objects.count() == 1
    # ...and the existing "Python" skill is attached to the new opening.
    opening = JobOpening.objects.get(title="Data Analyst")
    assert list(opening.skills.all()) == [python]


def edit_data(opening, **overrides):
    data = {
        "title": opening.title,
        "department": opening.department,
        "location": opening.location,
        "description": opening.description,
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_existing_skills_and_a_brand_new_skill_attach_in_one_submit(staff_client, opening):
    django = Skill.objects.create(name="Django")
    sql = Skill.objects.create(name="SQL")
    url = reverse("hiring:opening_update", args=[opening.pk])

    staff_client.post(url, edit_data(opening, skills=[django.pk, sql.pk], new_skill="  HTMX  "))

    htmx = Skill.objects.get(name="HTMX")  # created, with surrounding spaces trimmed
    assert set(opening.skills.all()) == {django, sql, htmx}


@pytest.mark.django_db
def test_unchecking_a_skill_removes_it_from_the_opening(staff_client, opening):
    django = Skill.objects.create(name="Django")
    opening.skills.add(django)
    url = reverse("hiring:opening_update", args=[opening.pk])

    staff_client.post(url, edit_data(opening))

    assert opening.skills.count() == 0
    assert Skill.objects.filter(pk=django.pk).exists()  # the skill itself is kept


@pytest.mark.django_db
def test_blank_new_skill_creates_nothing(staff_client, opening):
    url = reverse("hiring:opening_update", args=[opening.pk])
    staff_client.post(url, edit_data(opening, new_skill="   "))
    assert Skill.objects.count() == 0


@pytest.mark.django_db
def test_new_skill_matching_a_checked_skill_is_not_attached_twice(staff_client, opening):
    python = Skill.objects.create(name="Python")
    url = reverse("hiring:opening_update", args=[opening.pk])

    staff_client.post(url, edit_data(opening, skills=[python.pk], new_skill="PYTHON"))

    assert list(opening.skills.all()) == [python]
    assert Skill.objects.count() == 1
