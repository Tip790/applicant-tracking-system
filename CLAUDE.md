# CLAUDE.md

An internal, login-only applicant tracking system for hiring staff (CIDM 3312 Project #1).

## Stack
- Python + Django, SQLite database
- uv as the package manager
- Tailwind CSS + DaisyUI via django-tailwind-cli
- HTMX as the only JavaScript
- Ruff for linting and formatting
- pytest + pytest-django for tests

## Architecture decisions
- Every app view requires login. All staff share the same abilities. Django admin is for superusers only.
- Business rules live in one place that views and forms both use.
- Database constraints back up form validation.
- Prefer standard Django patterns and avoid clever abstractions. The developer is a beginner.

## References
- PRD: `prd/applicant-tracking-system.md`
- Plan: `plans/applicant-tracking-system.md`
- Prototypes: `prototypes/` (throwaway references, never promote into production code)
