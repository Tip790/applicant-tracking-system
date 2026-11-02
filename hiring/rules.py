"""Business rules for the hiring app.

Views and forms call these functions so each rule lives in exactly one place.
Database constraints on the models back these rules up.
"""

from .models import Candidate, Skill


def find_candidate_by_email(email, exclude_pk=None):
    """Return the candidate whose email matches, ignoring capitalization, or None.

    Pass `exclude_pk` when editing so a candidate doesn't clash with itself.
    """
    candidates = Candidate.objects.filter(email__iexact=email)
    if exclude_pk is not None:
        candidates = candidates.exclude(pk=exclude_pk)
    return candidates.first()


def get_or_create_skill(name):
    """Return the skill with this name, ignoring capitalization, creating it if needed.

    "python" reuses an existing "Python" instead of making a duplicate.
    """
    name = name.strip()
    existing = Skill.objects.filter(name__iexact=name).first()
    if existing:
        return existing
    return Skill.objects.create(name=name)
