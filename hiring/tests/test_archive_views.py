from html import unescape

import pytest
from django.urls import reverse

from hiring import rules
from hiring.models import Application, Candidate, JobOpening, Stage


def archive_url(candidate):
    return reverse("hiring:candidate_archive", args=[candidate.pk])


def unarchive_url(candidate):
    return reverse("hiring:candidate_unarchive", args=[candidate.pk])


def delete_url(candidate):
    return reverse("hiring:candidate_delete", args=[candidate.pk])


def page_text(response):
    """The page's HTML with whitespace collapsed and entities (e.g. &#x27;) turned back."""
    return " ".join(unescape(response.content.decode()).split())


@pytest.fixture
def archived(candidate, application, staff_user):
    """Ann Lee, archived after her only application was rejected."""
    rules.move_application(application, Stage.REJECTED, staff_user)
    return rules.archive_candidate(candidate)


# --- Archive and unarchive --------------------------------------------------


@pytest.mark.django_db
def test_archive_is_refused_on_the_page_while_an_application_is_active(
    staff_client, candidate, application
):
    response = staff_client.post(archive_url(candidate), follow=True)

    assert response.redirect_chain[-1][0] == candidate.get_absolute_url()
    html = page_text(response)
    assert "alert-error" in html
    assert "Ann Lee can't be archived while these applications are active:" in html
    assert "Backend Developer (Applied)" in html
    candidate.refresh_from_db()
    assert candidate.archived is False


@pytest.mark.django_db
def test_archive_succeeds_once_every_application_is_final(
    staff_client, staff_user, candidate, application
):
    rules.move_application(application, Stage.WITHDRAWN, staff_user)

    response = staff_client.post(archive_url(candidate), follow=True)

    candidate.refresh_from_db()
    assert candidate.archived is True
    html = page_text(response)
    assert "Candidate archived." in html
    assert ">Archived</span>" in html
    assert unarchive_url(candidate) in html


@pytest.mark.django_db
def test_candidate_with_no_applications_can_be_archived(staff_client, candidate):
    staff_client.post(archive_url(candidate))
    candidate.refresh_from_db()
    assert candidate.archived is True


@pytest.mark.django_db
def test_unarchive_restores_editing_and_moves(staff_client, archived, application):
    staff_client.post(unarchive_url(archived))

    archived.refresh_from_db()
    assert archived.archived is False
    # Editing is allowed again...
    edit = staff_client.get(reverse("hiring:candidate_update", args=[archived.pk]))
    assert edit.status_code == 200
    # ...and so is the reopen move.
    response = staff_client.post(
        reverse("hiring:application_move", args=[application.pk]), {"stage": Stage.APPLIED}
    )
    assert response.status_code == 200
    application.refresh_from_db()
    assert application.stage == Stage.APPLIED


# --- Archived candidates are read-only ---------------------------------------


@pytest.mark.django_db
def test_editing_an_archived_candidate_is_refused(staff_client, archived):
    url = reverse("hiring:candidate_update", args=[archived.pk])

    get_response = staff_client.get(url)
    post_response = staff_client.post(
        url,
        {
            "first_name": "Changed",
            "last_name": "Lee",
            "email": archived.email,
            "source": "website",
        },
        follow=True,
    )

    assert get_response.status_code == 302
    assert get_response.url == archived.get_absolute_url()
    assert "Ann Lee is archived. Unarchive the candidate to make changes." in page_text(
        post_response
    )
    archived.refresh_from_db()
    assert archived.first_name == "Ann"


@pytest.mark.django_db
def test_rules_refuse_an_application_for_an_archived_candidate(archived, staff_user):
    other = JobOpening.objects.create(
        title="Recruiter", department="HR", location="Remote", description="x"
    )

    with pytest.raises(rules.RuleViolation, match="is archived"):
        rules.create_application(archived, other, staff_user)
    assert Application.objects.filter(opening=other).count() == 0


@pytest.mark.django_db
def test_tampered_post_for_an_archived_candidate_is_refused(staff_client, archived):
    other = JobOpening.objects.create(
        title="Recruiter", department="HR", location="Remote", description="x"
    )
    # Started from the opening page, with the archived candidate's pk typed in by hand.
    response = staff_client.post(
        reverse("hiring:application_create") + f"?opening={other.pk}",
        {"candidate": archived.pk, "opening": other.pk},
    )

    assert response.status_code == 200
    assert response.context["form"].errors
    assert Application.objects.filter(opening=other).count() == 0


@pytest.mark.django_db
def test_record_page_from_an_archived_candidate_redirects_back(staff_client, archived):
    response = staff_client.get(reverse("hiring:application_create") + f"?candidate={archived.pk}")
    assert response.status_code == 302
    assert response.url == archived.get_absolute_url()


@pytest.mark.django_db
def test_candidate_picker_excludes_archived_candidates(staff_client, archived):
    other = JobOpening.objects.create(
        title="Recruiter", department="HR", location="Remote", description="x"
    )
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )

    assert set(rules.candidates_who_can_apply_to(other)) == {bob}
    response = staff_client.get(reverse("hiring:application_create") + f"?opening={other.pk}")
    assert list(response.context["form"].fields["candidate"].queryset) == [bob]


@pytest.mark.django_db
def test_archived_candidate_page_offers_only_unarchive(staff_client, archived):
    html = page_text(staff_client.get(archived.get_absolute_url()))

    assert "This candidate is archived and read-only." in html
    assert unarchive_url(archived) in html
    assert archive_url(archived) not in html
    assert reverse("hiring:candidate_update", args=[archived.pk]) not in html
    assert "Record application" not in html


@pytest.mark.django_db
def test_archived_dropdown_shows_a_note_instead_of_move_buttons(
    staff_client, archived, application
):
    html = staff_client.get(reverse("hiring:application_list")).content.decode()
    start = html.index(f'id="actions-{application.pk}"')
    dropdown = " ".join(unescape(html[start : html.index("</td>", start)]).split())

    assert "Ann Lee is archived. Unarchive the candidate to move this application." in dropdown
    assert 'name="stage"' not in dropdown
    assert application.move_options() is None


# --- The candidate list -----------------------------------------------------


@pytest.mark.django_db
def test_candidate_list_hides_archived_candidates_by_default(staff_client, archived):
    bob = Candidate.objects.create(
        first_name="Bob", last_name="Stone", email="bob@example.com", source="website"
    )

    hidden = staff_client.get(reverse("hiring:candidate_list"))
    shown = staff_client.get(reverse("hiring:candidate_list") + "?show_archived=1")

    assert list(hidden.context["candidates"]) == [bob]
    assert set(shown.context["candidates"]) == {archived, bob}
    html = page_text(shown)
    assert ">Archived</span>" in html
    assert 'name="show_archived" value="1" class="checkbox checkbox-sm" checked' in html


@pytest.mark.django_db
def test_show_archived_combines_with_search(staff_client, archived):
    response = staff_client.get(reverse("hiring:candidate_list") + "?q=ann&show_archived=1")
    assert list(response.context["candidates"]) == [archived]


# --- Delete -------------------------------------------------------------------


@pytest.mark.django_db
def test_candidate_with_no_applications_can_be_deleted(staff_client, candidate):
    page = page_text(staff_client.get(candidate.get_absolute_url()))
    assert delete_url(candidate) in page

    response = staff_client.post(delete_url(candidate), follow=True)

    assert response.redirect_chain[-1][0] == reverse("hiring:candidate_list")
    assert "Ann Lee was deleted." in page_text(response)
    assert not Candidate.objects.filter(pk=candidate.pk).exists()


@pytest.mark.django_db
def test_deleting_a_candidate_with_applications_is_refused_with_a_suggestion(
    staff_client, candidate, application
):
    page = page_text(staff_client.get(candidate.get_absolute_url()))
    assert delete_url(candidate) not in page  # the button is only offered when allowed

    response = staff_client.post(delete_url(candidate), follow=True)

    assert response.redirect_chain[-1][0] == candidate.get_absolute_url()
    assert "Archive the candidate instead to keep their hiring history." in page_text(response)
    assert Candidate.objects.filter(pk=candidate.pk).exists()
    assert Application.objects.filter(pk=application.pk).exists()
