from django.contrib import admin, messages
from django.db import transaction

from .models import Application, Candidate, JobOpening, Skill, StageChange


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["last_name", "first_name", "email", "source", "archived"]
    list_filter = ["source", "archived"]
    search_fields = ["first_name", "last_name", "email"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]
    actions = ["merge_skills"]

    @admin.action(description="Merge selected skills into the oldest one")
    def merge_skills(self, request, queryset):
        """Move every opening onto the oldest selected skill, then delete the others.

        Useful for near-duplicates such as "JS" and "JavaScript". Rename the kept
        skill afterwards if needed.
        """
        skills = list(queryset.order_by("pk"))
        if len(skills) < 2:
            self.message_user(request, "Select at least two skills to merge.", messages.WARNING)
            return
        keep, duplicates = skills[0], skills[1:]
        with transaction.atomic():
            for duplicate in duplicates:
                for opening in duplicate.openings.all():
                    opening.skills.add(keep)
                duplicate.delete()
        self.message_user(
            request,
            f"Merged {len(duplicates)} skill(s) into “{keep}”.",
            messages.SUCCESS,
        )


@admin.register(JobOpening)
class JobOpeningAdmin(admin.ModelAdmin):
    list_display = ["title", "department", "location", "status"]
    list_filter = ["status", "department"]
    search_fields = ["title", "department", "location"]
    filter_horizontal = ["skills"]


class StageChangeInline(admin.TabularInline):
    model = StageChange
    extra = 0
    readonly_fields = ["changed_at"]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["candidate", "opening", "stage", "created_at"]
    list_filter = ["stage", "opening"]
    search_fields = ["candidate__first_name", "candidate__last_name", "candidate__email"]
    inlines = [StageChangeInline]


@admin.register(StageChange)
class StageChangeAdmin(admin.ModelAdmin):
    list_display = ["application", "from_stage", "to_stage", "changed_by", "changed_at"]
    list_filter = ["to_stage"]
