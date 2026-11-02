from django import forms
from django.utils.html import format_html

from . import rules
from .models import Candidate


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
