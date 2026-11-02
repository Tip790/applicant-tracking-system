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
