import pytest
from django.apps import apps
from django.contrib import admin
from django.urls import reverse


def app_page_urls(candidate):
    """Every app page added so far. Add new pages here as phases add them."""
    return [
        reverse("hiring:home"),
        reverse("hiring:application_list"),
        reverse("hiring:candidate_list"),
        reverse("hiring:candidate_create"),
        reverse("hiring:candidate_detail", args=[candidate.pk]),
        reverse("hiring:candidate_update", args=[candidate.pk]),
    ]


@pytest.mark.django_db
def test_anonymous_users_are_sent_to_login_for_every_page(client, candidate):
    login_url = reverse("login")
    for url in app_page_urls(candidate):
        response = client.get(url)
        assert response.status_code == 302, url
        assert response.url.startswith(f"{login_url}?next="), url


@pytest.mark.django_db
def test_logged_in_staff_can_open_every_page(staff_client, candidate):
    for url in app_page_urls(candidate):
        response = staff_client.get(url, follow=True)
        assert response.status_code == 200, url


@pytest.mark.django_db
def test_login_page_is_public(client):
    assert client.get(reverse("login")).status_code == 200


@pytest.mark.django_db
def test_logging_in_redirects_to_all_applications(client, staff_user):
    response = client.post(reverse("login"), {"username": "staff", "password": "pass12345"})
    assert response.status_code == 302
    assert response.url == reverse("hiring:application_list")


@pytest.mark.django_db
def test_root_redirects_to_all_applications(staff_client):
    response = staff_client.get(reverse("hiring:home"))
    assert response.url == reverse("hiring:application_list")


@pytest.mark.django_db
def test_logging_out_ends_the_session(staff_client):
    response = staff_client.post(reverse("logout"))
    assert response.url == reverse("login")

    response = staff_client.get(reverse("hiring:application_list"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("login"))


@pytest.mark.django_db
def test_non_superuser_cannot_use_admin_even_if_marked_staff(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="clerk", password="pass12345", is_staff=True
    )
    client.force_login(user)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302
    assert response.url.startswith(reverse("admin:login"))


@pytest.mark.django_db
def test_superuser_can_use_admin(client, django_user_model):
    boss = django_user_model.objects.create_superuser(username="boss", password="pass12345")
    client.force_login(boss)
    assert client.get(reverse("admin:index")).status_code == 200


def test_every_hiring_model_is_registered_in_admin():
    for model in apps.get_app_config("hiring").get_models():
        assert admin.site.is_registered(model), model.__name__
