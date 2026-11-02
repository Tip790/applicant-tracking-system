# Plan: Applicant Tracking System

> Source PRD: [prd/applicant-tracking-system.md](../prd/applicant-tracking-system.md)

## Architectural decisions

Durable decisions that apply across all phases:

- **Stack**: Python + Django + SQLite, managed with uv. Tailwind CSS + DaisyUI via django-tailwind-cli. HTMX is the only JavaScript. Ruff for lint/format. pytest + pytest-django (`uv run pytest`).
- **Project layout**: one Django project (settings package `config`) with a single app, `hiring`, that owns all models, views, forms, templates and the rules module.
- **URLs** (app namespace `hiring`, integer pks, no slugs):
  - `/accounts/login/`, `/accounts/logout/` — Django built-in auth views
  - `/` → redirects to `/applications/`
  - `/applications/` — All Applications table (search + filters as GET params)
  - `/applications/new/?candidate=<pk>` or `/applications/new/?opening=<pk>` — record an application
  - `/applications/<pk>/move/` — POST only, HTMX, target stage in the body
  - `/candidates/`, `/candidates/new/`, `/candidates/<pk>/`, `/candidates/<pk>/edit/`
  - `/candidates/<pk>/archive/`, `/candidates/<pk>/unarchive/`, `/candidates/<pk>/delete/` — POST actions
  - `/openings/`, `/openings/new/`, `/openings/<pk>/`, `/openings/<pk>/edit/`
  - `/openings/<pk>/close/` (GET shows confirmation, POST closes), `/openings/<pk>/reopen/` (POST)
  - `/admin/` — superusers only
- **Models**:
  - `Candidate` — first/last name, email (unique ignoring case, DB constraint on lowercased email), optional phone, source (Website / Job Board / Referral / Other), source details, notes, `archived` flag, timestamps.
  - `JobOpening` — title, department, location, description, status (`open` / `closed`), timestamps; M2M to `Skill`.
  - `Skill` — name, unique ignoring case.
  - `Application` — FK `Candidate`, FK `JobOpening`, current stage, timestamps; DB unique constraint on (candidate, opening).
  - `StageChange` — FK `Application`, from-stage (blank for the initial entry), to-stage, FK user, timestamp.
  - **Stages**: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, Withdrawn. Active = Applied–Offer; final = Hired, Rejected, Withdrawn.
- **Business rules**: all live in one plain module in `hiring` (stage transition rules, performing a move, can-archive / can-delete, can-apply). Views and forms call it; nothing re-implements the rules.
- **Auth**: every app view requires login. All staff have the same abilities in the app. Admin is superuser-only. After login, users go to All Applications.
- **Templates**: the application table row, Actions dropdown and progress tracker are reusable partials shared by the All Applications page and the opening detail page.
- **Tests**: shared fixtures for a logged-in staff client, a candidate, an opening and an application.

---

## Phase 1: Skeleton, login and candidates

**User stories**: 1–12, 14 (page shell)

### What to build

Set up the project end to end: uv, Django, the `hiring` app, Tailwind/DaisyUI via django-tailwind-cli, HTMX, Ruff and pytest. Staff log in with username/password. Every page requires login, and after login staff land on a (still empty) All Applications page. The Django admin is available to superusers only.

Through the first real feature, staff can create, list, search, view and edit candidates. The candidate form has first/last name, email, optional phone, a source dropdown, source details and notes. A new candidate whose email matches an existing one (ignoring case) is rejected with a friendly error that says the candidate already exists and links to the existing record. The database constraint backs this up. The candidate detail page exists and will list applications in a later phase.

### Acceptance criteria

- [ ] `uv run python manage.py runserver`, `uv run pytest` and `uv run ruff check` all work from a fresh clone.
- [ ] Tailwind/DaisyUI styles and HTMX load on a shared base template.
- [ ] Anonymous requests to any app page redirect to the login page. Tests cover every page added in this phase.
- [ ] Logging in redirects to `/applications/`. Logging out works.
- [ ] Non-superuser staff cannot access `/admin/`. Superusers can, and every model is registered there.
- [ ] Staff can create, edit, view and list candidates. The list supports search by name/email.
- [ ] Source is limited to Website, Job Board, Referral, Other.
- [ ] Creating a candidate with an email that differs only in case from an existing one fails with an error linking to the existing candidate (test).
- [ ] The DB rejects a case-insensitive duplicate email even when the form is bypassed (test).

---

## Phase 2: Job openings and skills

**User stories**: 22–25, 28, 29, 31–35

### What to build

Staff can create, list, view and edit job openings (title, department, location, description). The list shows each opening's status. Staff can close an opening and reopen it any number of times, and closed openings show a "closed" badge wherever they appear.

The opening form lets staff pick existing skills and type a new skill name. A new name that matches an existing skill ignoring case reuses that skill rather than creating a duplicate. The opening detail page shows its skills. Superusers can manage skills in admin to clean up near-duplicates.

### Acceptance criteria

- [ ] Staff can create, edit, view and list openings. The list shows status, with a "closed" badge on closed openings.
- [ ] Close and reopen work repeatedly and are POST-only.
- [ ] The opening form can attach existing skills and add a new one in the same submit.
- [ ] Adding "python" when "Python" exists attaches the existing skill and creates no new row (test).
- [ ] The DB rejects a case-insensitive duplicate skill name (test).
- [ ] All new pages require login (test).

---

## Phase 3: Record applications and the All Applications table

**User stories**: 14, 26, 30, 36–38, 40–42, 44–48, 64

### What to build

Staff record a candidate's application to an opening with one form and view, reached two ways. From the candidate page, the candidate is pre-filled and staff pick an opening. The picker only offers open openings the candidate hasn't applied to. From the opening page, the opening is pre-filled and staff pick a candidate. The picker only offers candidates who haven't applied to that opening. A new application starts in Applied and creates the first StageChange (blank from-stage → Applied, recording the user).

The rules module refuses a duplicate (candidate, opening) pair and applications to closed openings, even when the form is bypassed. The DB unique constraint is the final safeguard. The candidate detail page lists their applications and current stages. Closing an opening shows a confirmation with the number of applications still active.

The All Applications page shows a read-only table with these columns: candidate (name and email), opening (with closed badge), source, colored stage badge, stage history and time in current stage. It has search by candidate name, a filter by opening and a filter by stage (including "Active only"). The table and row are partials. The opening detail page reuses the same table, pre-filtered to that opening. An Actions column placeholder is left for Phase 4.

### Acceptance criteria

- [ ] An application can be created from both the candidate page and the opening page. Each redirects back to where it started.
- [ ] Pickers exclude closed openings and pairs that already have an application.
- [ ] A second application for the same pair is refused by the rules and by the DB constraint (tests).
- [ ] Applying to a closed opening is refused (test).
- [ ] A new application has stage Applied and exactly one StageChange (blank → Applied, correct user) (test).
- [ ] The candidate detail page lists their applications with stage badges.
- [ ] The close confirmation shows the correct count of active applications.
- [ ] All Applications shows all required columns, with stage badges colored by stage (e.g. green Hired, red Rejected).
- [ ] Search by candidate name and the opening/stage/"Active only" filters work alone and combined (tests).
- [ ] The opening detail page shows the same table pre-filtered to that opening.
- [ ] Time in current stage and stage history are derived from StageChange rows.

---

## Phase 4: Moving applicants with HTMX

**User stories**: 27, 52–58, 60, 61, 63, 65

### What to build

Add the stage-move function to the rules module. It checks the Flexible rules and gives a human-readable reason when it refuses. From any active stage, an application can move to any other active stage, or to Rejected or Withdrawn. Hired is reachable only from Offer and is final. On success, the function updates the application's stage and creates a StageChange (from, to, user, time) in one transaction.

Each table row gets an Actions dropdown with buttons for only the legal moves: "Advance to [next] →" (primary), "← Back to [previous]" (ghost), "Jump to" buttons for other active stages (small ghost), "Reject" (outlined error) and "Mark withdrawn" (ghost). Hired applications show a "Hired is final" note instead of buttons. Each button POSTs to `/applications/<pk>/move/` via HTMX. On success the response is only the re-rendered row, swapped in place, so search and filters are kept. On a refused move, the response is an error with a DaisyUI alert and the stage is unchanged. The same endpoint and row partial serve both the All Applications page and the opening page. Applications on closed openings move normally.

### Acceptance criteria

- [ ] Every allowed Flexible move succeeds (tests cover active → active, active → Rejected/Withdrawn, Offer → Hired).
- [ ] Illegal moves are refused with a reason: Hired from anything but Offer, any move out of Hired (tests).
- [ ] Each successful move creates exactly one StageChange with the correct from/to/user (test).
- [ ] The stage update and the StageChange are saved together or not at all (one transaction).
- [ ] The dropdown shows only legal moves, with the specified button styles and labels.
- [ ] A successful move returns only the row fragment, not a full page (test).
- [ ] A tampered illegal POST returns an error response with an alert and leaves the stage unchanged (test).
- [ ] The move endpoint is POST-only and requires login (test).
- [ ] Applications on a closed opening can still be moved (test).
- [ ] Moving works from both the All Applications page and the opening page.

---

## Phase 5: Progress tracker and reopen

**User stories**: 43, 49–51, 59

### What to build

The top of the Actions dropdown shows the candidate's name, a stage badge and a numbered 1–6 progress tracker (Applied, Screening, Interview, Final Review, Offer, Hired) built with DaisyUI steps, with the reached steps highlighted. For a rejected application, the reached steps are shown in red with a note such as "Rejected after Interview". For a withdrawn application, the tracker shows the stage they withdrew from. Hired shows the full tracker.

Rejected and Withdrawn applications get a "Reopen to [previous stage]" button (warning style). The rules allow a final-but-not-Hired application to move back only to the stage it held just before, which comes from the StageChange history. This is how a previously rejected candidate "re-applies" to the same opening without creating a second application.

### Acceptance criteria

- [ ] The tracker is a reusable partial. Reached steps are highlighted correctly for every active stage and for Hired.
- [ ] A rejected application shows the reached steps in red and "Rejected after [stage]".
- [ ] A withdrawn application shows the stage it was withdrawn from.
- [ ] Rejected/Withdrawn applications show only "Reopen to [previous stage]".
- [ ] Reopen to the previous stage succeeds and records a StageChange (test).
- [ ] Moving a Rejected/Withdrawn application to any other stage is refused (test).
- [ ] After a reopen, the row re-renders with the correct tracker and buttons.

---

## Phase 6: Archive, unarchive and delete candidates

**User stories**: 13, 15–21, 39 (archived exclusion), 62

### What to build

Staff can archive a candidate from the candidate page. The rules refuse archiving while the candidate has any application in an active stage, and the error lists the blocking applications. Archived candidates are read-only: the edit page is refused, no new applications can be recorded for them, and stage moves on their applications are refused by the move endpoint (with the error alert). The Actions dropdown shows no move buttons for them. Staff can unarchive to restore normal behavior.

The candidate list hides archived candidates by default, and a "Show archived" toggle brings them back with an archived badge. The candidate picker on the opening page's "record application" flow excludes archived candidates. Staff can delete a candidate only when they have zero applications. Otherwise the system refuses and suggests archiving. Permanent deletion of candidates with history stays in admin.

### Acceptance criteria

- [ ] Archiving is refused while any application is active, and the message lists the blocking applications (test).
- [ ] Archiving succeeds once all applications are final. Unarchiving restores editing and moves.
- [ ] Editing an archived candidate is refused (test).
- [ ] Creating an application for an archived candidate is refused, even if the form is bypassed (test).
- [ ] Moving an archived candidate's application is refused with an error alert and no stage change (test).
- [ ] The candidate list hides archived candidates by default. "Show archived" shows them, marked.
- [ ] The candidate picker excludes archived candidates.
- [ ] Deleting a candidate with no applications works. Deleting one with any application is refused with a suggestion to archive (test).
- [ ] Archive, unarchive and delete are POST-only and require login (test).
