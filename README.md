# applicant-tracking-system
CIDM 3312 Project #1 Applicant Tracking System

An internal, login-only applicant tracking system for hiring staff.
Built with Django, SQLite, Tailwind CSS + DaisyUI (django-tailwind-cli) and HTMX.

## Setup (fresh clone)

Requires [uv](https://docs.astral.sh/uv/).

```sh
uv sync                                   # install dependencies
uv run python manage.py migrate           # create the SQLite database
uv run python manage.py createsuperuser   # admin account (can use /admin/)
uv run python manage.py tailwind build    # build the CSS (downloads the Tailwind CLI once)
```

Staff accounts that are not superusers can be added in `/admin/` (Users → Add user).
They can use the whole app but not the admin site.

## Running

```sh
uv run python manage.py runserver            # serve the app at http://127.0.0.1:8000/
uv run python manage.py tailwind runserver   # same, but rebuilds CSS as templates change
```

## Checks

```sh
uv run pytest         # tests
uv run ruff check .   # lint
uv run ruff format .  # format
```
