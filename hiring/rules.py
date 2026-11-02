"""Business rules for the hiring app.

Views and forms call these functions so each rule lives in exactly one place.
Database constraints on the models back these rules up.
"""

from .models import Candidate


def find_candidate_by_email(email, exclude_pk=None):
    """Return the candidate whose email matches, ignoring capitalization, or None.

    Pass `exclude_pk` when editing so a candidate doesn't clash with itself.
    """
    candidates = Candidate.objects.filter(email__iexact=email)
    if exclude_pk is not None:
        candidates = candidates.exclude(pk=exclude_pk)
    return candidates.first()
