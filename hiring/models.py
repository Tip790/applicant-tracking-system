from django.conf import settings
from django.db import models
from django.db.models.functions import Lower
from django.urls import reverse


class Candidate(models.Model):
    class Source(models.TextChoices):
        WEBSITE = "website", "Website"
        JOB_BOARD = "job_board", "Job Board"
        REFERRAL = "referral", "Referral"
        OTHER = "other", "Other"

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    source = models.CharField(max_length=20, choices=Source)
    source_details = models.CharField(
        max_length=200,
        blank=True,
        help_text='Specifics, e.g. "Indeed" or "referred by Maria in Sales".',
    )
    notes = models.TextField(blank=True)
    archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        constraints = [
            # One candidate per email, ignoring capitalization.
            models.UniqueConstraint(
                Lower("email"),
                name="unique_candidate_email_ignore_case",
            ),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def get_absolute_url(self):
        return reverse("hiring:candidate_detail", args=[self.pk])


class Skill(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ["name"]
        constraints = [
            # One skill per name, ignoring capitalization ("Python" == "python").
            models.UniqueConstraint(
                Lower("name"),
                name="unique_skill_name_ignore_case",
            ),
        ]

    def __str__(self):
        return self.name


class JobOpening(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    title = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    description = models.TextField()
    status = models.CharField(max_length=10, choices=Status, default=Status.OPEN)
    skills = models.ManyToManyField(Skill, blank=True, related_name="openings")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("hiring:opening_detail", args=[self.pk])

    @property
    def is_closed(self):
        return self.status == self.Status.CLOSED


class Stage(models.TextChoices):
    """The hiring stages, in process order."""

    APPLIED = "applied", "Applied"
    SCREENING = "screening", "Screening"
    INTERVIEW = "interview", "Interview"
    FINAL_REVIEW = "final_review", "Final Review"
    OFFER = "offer", "Offer"
    HIRED = "hired", "Hired"
    REJECTED = "rejected", "Rejected"
    WITHDRAWN = "withdrawn", "Withdrawn"


# Stages where the applicant is still in progress. Hired, Rejected and Withdrawn are final.
ACTIVE_STAGES = [
    Stage.APPLIED,
    Stage.SCREENING,
    Stage.INTERVIEW,
    Stage.FINAL_REVIEW,
    Stage.OFFER,
]


class Application(models.Model):
    # CASCADE so a superuser can permanently delete records from admin.
    # The app's own delete view (Phase 6) only deletes candidates with no applications.
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name="applications")
    opening = models.ForeignKey(JobOpening, on_delete=models.CASCADE, related_name="applications")
    stage = models.CharField(max_length=20, choices=Stage, default=Stage.APPLIED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            # A candidate can apply to each opening at most once.
            models.UniqueConstraint(
                fields=["candidate", "opening"],
                name="unique_application_per_candidate_and_opening",
            ),
        ]

    def __str__(self):
        return f"{self.candidate} → {self.opening}"

    @property
    def is_active(self):
        return self.stage in ACTIVE_STAGES

    def stage_entered_at(self):
        """When the application moved into its current stage, from the StageChange history."""
        changes = list(self.stage_changes.all())
        return changes[-1].changed_at if changes else self.created_at


class StageChange(models.Model):
    """One row per stage move, starting with the application's creation in Applied."""

    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="stage_changes"
    )
    from_stage = models.CharField(max_length=20, choices=Stage, blank=True)
    to_stage = models.CharField(max_length=20, choices=Stage)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="stage_changes"
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["changed_at", "pk"]

    def __str__(self):
        start = self.get_from_stage_display() or "(new)"
        return f"{self.application}: {start} → {self.get_to_stage_display()}"
