from django import forms
from django.utils.html import format_html

from . import rules
from .models import Candidate, JobOpening


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "source",
            "source_details",
            "notes",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "input w-full"}),
            "last_name": forms.TextInput(attrs={"class": "input w-full"}),
            "email": forms.EmailInput(attrs={"class": "input w-full"}),
            "phone": forms.TextInput(attrs={"class": "input w-full"}),
            "source": forms.Select(attrs={"class": "select w-full"}),
            "source_details": forms.TextInput(attrs={"class": "input w-full"}),
            "notes": forms.Textarea(attrs={"class": "textarea w-full", "rows": 4}),
        }

    def clean_email(self):
        email = self.cleaned_data["email"]
        existing = rules.find_candidate_by_email(email, exclude_pk=self.instance.pk)
        if existing:
            raise forms.ValidationError(
                format_html(
                    'A candidate with this email already exists: <a href="{}" class="link">{}</a>.',
                    existing.get_absolute_url(),
                    existing,
                )
            )
        return email


class JobOpeningForm(forms.ModelForm):
    new_skill = forms.CharField(
        max_length=100,
        required=False,
        label="Add a new skill",
        help_text="Not in the list? Type it here. A name that matches an existing skill "
        "(ignoring capitalization) reuses that skill.",
        widget=forms.TextInput(attrs={"class": "input w-full"}),
    )

    class Meta:
        model = JobOpening
        fields = ["title", "department", "location", "description", "skills"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "input w-full"}),
            "department": forms.TextInput(attrs={"class": "input w-full"}),
            "location": forms.TextInput(attrs={"class": "input w-full"}),
            "description": forms.Textarea(attrs={"class": "textarea w-full", "rows": 5}),
            "skills": forms.CheckboxSelectMultiple(attrs={"class": "checkbox checkbox-sm"}),
        }

    def save(self, commit=True):
        # Views always save with commit=True, so the opening exists before we add the skill.
        opening = super().save(commit=commit)
        new_skill = self.cleaned_data.get("new_skill", "").strip()
        if commit and new_skill:
            opening.skills.add(rules.get_or_create_skill(new_skill))
        return opening
