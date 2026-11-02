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
- Login is enforced globally by `LoginRequiredMiddleware`; new views need no decorator. Add each new page to `app_page_urls` in `hiring/tests/test_auth.py`.
- State-changing actions are function views with `@require_POST`; add each to `app_post_action_urls` in `hiring/tests/test_auth.py`.
- Business rules go in `hiring/rules.py`. Create skills only through `rules.get_or_create_skill` (case-insensitive reuse).
- Show an opening's status with `hiring/partials/opening_status_badge.html` wherever it appears.
- DaisyUI is v5: use `input`/`select`/`textarea` (no `-bordered`), and no `form-control`/`label-text`.
- Change stages only through `rules.move_application`. `rules.move_refusal_reason` is the one stage-rule check; the Actions buttons come from `rules.move_options`, which uses it.
- HTMX row actions: on success return only the row partial (`hx-target="#application-<pk>"`, `hx-swap="outerHTML"`). On a refusal return 422 with an alert and `HX-Retarget: #move-alert`. `base.html` configures HTMX to swap 422 and sends the CSRF token via `hx-headers`.
- Dropdowns inside the table use DaisyUI's popover dropdown (`popovertarget` + CSS anchor) so the scrolling card doesn't clip them.

## Commands
- `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`
- `uv run python manage.py tailwind runserver` (serves and rebuilds CSS; the built CSS is git-ignored)

## References
- PRD: `prd/applicant-tracking-system.md`
- Plan: `plans/applicant-tracking-system.md`
- Prototypes: `prototypes/` (throwaway references, never promote into production code)
