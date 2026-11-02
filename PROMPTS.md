# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-11-02 — Phase 3: record applications and the All Applications table

### Prompts
1. `/implement @prd/applicant-tracking-system.md  @plans/applicant-tracking-system.md  implement Phase 3`
2. `approved, go ahead add new test to the plan's acceptance criteria`
3. `approved, go ahead`
4. `approved, go ahead`
5. `continue`
6. `approved, go ahead`
7. `continue`
8. `approved, go ahead`
9. `continue`
10. `manual verification passed, go ahead`

### Summary
- **Outcome:** Phase 3 was built on top of Phase 2:
  - `Application` model (candidate, opening, stage, timestamps) with a database constraint allowing one application per candidate and opening. `StageChange` model (from-stage, to-stage, who, when). A `Stage` choice list and an `ACTIVE_STAGES` list. Migration `0003`, plus admin registration with the stage history shown inline.
  - `hiring/rules.py` gained `create_application` (saves the application in Applied and its first StageChange in one transaction), `application_refusal_reason` (refuses closed openings and duplicate pairs), the two picker querysets, `count_active_applications`, and a `RuleViolation` exception carrying a readable reason. A database `IntegrityError` from a simultaneous duplicate is turned into the same message.
  - One `ApplicationForm` and `application_create` view at `/applications/new/?candidate=` or `?opening=`. The fixed side is a hidden field that accepts only that record. The other side is a picker of valid choices. Saving returns to the page you started from.
  - `/openings/<pk>/close/` now shows a confirmation with the number of active applications on GET and closes on POST. The "Close opening" button became a link to it.
  - Partials for the stage badge, the applications table and the table row. All Applications has name search and opening/stage/"Active only" filters. The opening page reuses the table, limited to that opening. The candidate page lists its applications with stage badges. Stage history and time in stage come from StageChange rows. The Actions column is a placeholder for Phase 4.
  - 62 tests pass. Three behaviors were built test-first, each through an approved RED → GREEN cycle: a new application starts in Applied with exactly one StageChange, the rules refuse a duplicate pair even without the form, and the search and filters work alone and combined. Ordinary tests cover the DB constraint, the closed-opening refusal, the pickers, both redirects, tampered POSTs, the detail pages, the table columns, badge colors, history and time in stage, the close confirmation count, and login on the new pages.
  - Ruff check and format are clean, there are no missing migrations, and the CSS build contains every badge color. The user confirmed manual verification in the browser.
- **Deviations:**
  - The user asked for the new TDD test to be added to the plan's acceptance criteria. Claude pointed out that all three behaviors were already marked "(test)" in the plan, so instead it added "(even when the form is bypassed)" to the duplicate-pair criterion, the one detail the plan didn't state.
  - Claude made a few choices without asking: the badge color for each stage, cascading deletes on the application's foreign keys (so superusers can still delete records from admin), no "Record application" button on closed openings, a 404 when the record page is opened without a candidate or opening, and limiting the hidden fixed field to the one record from the URL.
  - Search still matches first or last name separately (not "Ann Lee" as a full name), consistent with the user's Phase 1 choice.
  - The user's own uncommitted edit to `CLAUDE.md`, made before the session, was again left out of the phase commit.
- **Sideways:**
  - Nothing failed. All three RED runs failed on assertions. For behaviors 1 and 2, Claude first wrote small stubs (a `create_application` that saved only the application, and an `application_refusal_reason` that always returned `None`) so the tests could fail on assertions instead of import or database errors.
  - Claude first set the stages in the filter test with a hard-to-read `.__class__.objects` chain and replaced it with an `apply_at_stage` helper before running the test. It also moved two inline imports in the rules tests to the top of the file.
  - Claude first used `PROTECT` on the application's foreign keys and switched to `CASCADE` before making the migration, because PROTECT would have blocked superusers from deleting candidates in admin.
  - Ruff reformatted one file. The tests were re-run afterwards and still passed.

## 2026-11-02 — Phase 2: job openings and skills

### Prompts
1. `/implement @prd/applicant-tracking-system.md  @plans/applicant-tracking-system.md  implement Phase 2`
2. `where did you get the close and reopen work repeatedly and only accept POST tdd from?`
3. `keep both, approved, go ahead, but add the new TDD test to the plan`
4. `approved, go ahead`
5. `continue`
6. `approved, go ahead`
7. `continue`
8. `manual verification passed, go ahead`

### Summary
- **Outcome:** Phase 2 was built on top of Phase 1:
  - `Skill` model with a database constraint that keeps names unique ignoring case. `JobOpening` model (title, department, location, description, open/closed status defaulting to open, skills, timestamps). Migration `0002`.
  - Opening list, detail, create and edit pages using generic class-based views, plus an "Openings" link in the navbar. A shared `partials/opening_status_badge.html` shows Open/Closed badges.
  - The opening form has a checkbox list of existing skills and an "Add a new skill" field. `rules.get_or_create_skill` reuses a skill whose name matches ignoring case and trims spaces.
  - POST-only close and reopen views (`@require_POST`) that redirect back to the opening, with matching buttons on the detail page.
  - Openings and skills are registered in admin. Skills have a "Merge selected skills into the oldest one" admin action for story 35.
  - 38 tests pass. Two behaviors were built test-first, each through an approved RED → GREEN cycle: reusing a skill that differs only in case, and close/reopen working repeatedly and only on POST. Ordinary tests cover the skill constraint, opening create/edit/view/list, the badges and buttons, more skill cases, the merge action, and login on the new pages and POST actions.
  - Ruff check and format are clean. The user confirmed manual verification in the browser.
- **Deviations:**
  - The user asked where the close/reopen TDD candidate came from. Claude pointed to the plan's Phase 2 criterion and admitted the plan didn't mark it "(test)". The user kept both behaviors and had "(test)" added to that criterion in the plan.
  - The close/reopen test checks that a GET leaves the status unchanged instead of demanding a 405, because the plan has `/close/` show a confirmation page on GET in Phase 3.
  - Claude made a few choices without asking: description is required, the skill-merge admin action was added, and editing an opening never changes its status.
  - The user's own uncommitted edit to `CLAUDE.md`, made before the session, was left out of the Phase 2 commit.
- **Sideways:**
  - Nothing failed. Both RED runs failed on assertions as intended, and the full suite, Ruff, the migration check and the CSS build all passed the first time.

## 2026-11-02 — Phase 1: skeleton, login and candidates

### Prompts
1. `/implement @prd/applicant-tracking-system.md  @plans/applicant-tracking-system.md  implement Phase 1`
2. `approved, go ahead`
3. `approved, go ahead`
4. `continue`
5. `approved, go ahead`
6. `continue`
7. `approved, go ahead`
8. `continue`
9. `manual verification passed, go ahead`

### Summary
- **Outcome:** Phase 1 was built from an empty repo:
  - A uv project (Django 6.1, django-tailwind-cli, pytest, pytest-django, ruff), a `config` project and a single `hiring` app.
  - Tailwind + DaisyUI 5 through django-tailwind-cli (source CSS in `tailwind/source.css`), and HTMX 2.0.4 from unpkg with a checked SRI hash, on a shared `templates/base.html`.
  - Login and logout use Django's auth views. Every page requires login through Django's `LoginRequiredMiddleware`. Login lands on a placeholder All Applications page, and `/` redirects there.
  - `/admin/` is limited to superusers by overriding `admin.site.has_permission` in `config/urls.py`. Candidate is registered in admin.
  - The `Candidate` model has a database constraint that keeps email unique ignoring case. Candidate list (search by name/email), detail, create and edit pages use generic class-based views.
  - `hiring/rules.py` holds the first business rule, `find_candidate_by_email`. `CandidateForm.clean_email` uses it to show a "candidate already exists" error that links to the existing record.
  - 22 tests pass. Three behaviors were built test-first, each through an approved RED → GREEN cycle: the database constraint, the linked duplicate-email error and candidate search. The other tests cover login on every page, the login and logout redirects, admin access and candidate create/edit/view.
  - Ruff check and format are clean, and the README has setup instructions. The user confirmed manual verification in the browser.
- **Deviations:**
  - The user approved every TDD selection and test without changes.
  - Claude pointed out that search matches each field separately, so a full name like "Ann Lee" won't match, and offered to add it. The user didn't ask for it, so it was left out.
  - The built CSS and the downloaded Tailwind binary are git-ignored, so a fresh clone needs one `tailwind build` (documented in the README). Claude made this choice without asking.
- **Sideways:**
  - `uv add` first failed with a TLS "invalid peer certificate: UnknownIssuer" error. It worked with `--system-certs`.
  - A `cd` into the installed tailwind package briefly changed the working directory. Claude noticed and changed back.
  - The first source CSS location (`assets/css/source.css`) triggered a django-tailwind-cli warning because it was inside the static folder. It was moved to `tailwind/source.css` before the first test went green.
  - The first `tailwind build` failed with "Access is denied" while running the just-downloaded CLI (probably Windows Defender scanning it). A retry worked.
  - The build used DaisyUI 5, which dropped `input-bordered`, `select-bordered`, `textarea-bordered`, `form-control`, `label-text` and the row `hover` class. Claude found this by checking the built CSS and replaced the classes before manual verification.
  - Smaller slips: a diagnostic command run against the not-yet-migrated dev database failed, and the PowerShell smoke test's redirect checks raised PowerShell 5 errors. Neither affected the code, and tests cover the redirects.

## 2026-11-02 — Phased implementation plan from the PRD

### Prompts
1. `/prd-to-plan @prd/applicant-tracking-system.md`
2. `merge the phases proposed, list any additional potential merges you'd reccomend, one app is okay`
3. `merge phases 1 + 2, 4+5, and unmerge 6 then write the plan`
4. `Write this session log to PROMPTS.md according to its instructions.`

### Summary
- **Outcome:** The PRD was broken into a six-phase tracer-bullet plan, written to `plans/applicant-tracking-system.md`:
  1. Skeleton, login and candidates.
  2. Job openings and skills.
  3. Record applications and the All Applications table.
  4. Moving applicants with HTMX.
  5. Progress tracker and reopen.
  6. Archive, unarchive and delete candidates.

  The plan header fixes the decisions that apply to every phase:
  - One `hiring` app in a `config` project.
  - A namespaced URL list using pks, not slugs.
  - The five models and their constraints.
  - A single rules module.
  - Login-required views, with admin for superusers only.
  - Shared table partials and test fixtures.

  Each phase has checkbox acceptance criteria. No application code was written, and nothing was committed.
- **Deviations:**
  - Claude first proposed nine phases. In prompt 2 the user merged the two pairs Claude had suggested (openings + skills, moves + tracker) and asked for more merge ideas.
  - Claude suggested merging skeleton + candidates (recommended) and record applications + table (reasonable). It also mentioned splitting the merged moves/tracker phase back up if it grew too big, and advised keeping archive/delete separate.
  - In prompt 3 the user took both merges and the split.
  - The user accepted Claude's single-app recommendation in prompt 2.
- **Sideways:**
  - Nothing failed.
  - One rules gap is noted in the plan: the "no archived candidates" check on new applications is deferred to the archive phase (Phase 6), because archiving doesn't exist before then.
  - Story 14 is split across Phases 1 and 3.

## 2026-11-01 — Design interview, two prototypes, and PRD for the Applicant Tracking System

### Prompts
1. `/grill-me @project-idea.md create an Applicant Tracking System fulfilling these requirements, allowing staff to check the process of each applicant and what jobs they apply to.`
2. `3`
3. `1`
4. `1 attached to candidate, not application`
5. `/prototype can you prototype the hiring stage transition rules from the latest question in our grill?`
6. `Flexible, option 2, block archiving with active apps`
7. `2`
8. `option 2`
9. `Option 2, skills on openings only`
10. `is this a UI question for the browser?`
11. `/prototype the applicant pipeline screen layouts`
12. `can we use option C but with option D's named action buttons as a dropdown for a selected candidate?`
13. `returning to the previous prototyping, can the action buttons have the same visual formatting as they do in option D`
14. `I meant the labeling of each process phase 1-6 and the line between them located in option D, include that for option E as a dropdown to show a visualization of where the employee is at in the process` (correction of prompt 13)
15. `Option E is great let's move on to question 9 with Option 3, keeping candidate creation separate`
16. `option 1 is good`
17. `pytest with pytest-django, keep the list as is`
18. `/to-prd`
19. `Write this session log to PROMPTS.md according to its instructions.`

### Summary
- **Outcome:** An 11-question design interview settled the full design:
  - Equal staff users, with only a superuser using Django admin.
  - Candidate email unique ignoring case.
  - Source dropdown stored on the candidate.
  - Archive any time; delete only candidates with no applications; archiving blocked while an application is active.
  - "Flexible" stage-transition rules.
  - Closing an opening stops new applications only; openings can be reopened freely.
  - Skills on openings only.
  - Pipeline screen "variant E".
  - One shared application form.
  - A StageChange history table.
  - pytest + pytest-django.

  Two throwaway prototypes were built: `prototypes/stage-rules.html` (logic) and `prototypes/pipeline-ui.html` (five layout variants A–E; E chosen). The PRD was written to `prd/applicant-tracking-system.md`. No application code exists yet.
- **Deviations:**
  - Question 8 (pipeline screen): Claude recommended a per-opening board (variant A). The user asked whether it was a UI question, had it prototyped, and chose their own combination instead: variant C's table plus variant D's progress tracker and action buttons, inside a per-row dropdown (variant E).
  - Prompt 4 explicitly confirmed source belongs on the candidate rather than the application.
  - Claude made no recommendation for the stage-rule set, so the user chose Flexible from the prototype.
  - Every other answer matched Claude's recommendation.
  - Follow-up questions: prompt 10 (whether Question 8 was a UI question) and prompts 12–14 (refining variant E).
  - The PRD includes three small assumptions the user never explicitly confirmed: land on All Applications after login, candidate search with a "Show archived" toggle, and a basic openings list.
- **Sideways:**
  - Prompt 5 asked for "the hiring stage transition rules from the latest question", but the latest question was about the candidate archive/delete lifecycle, and stage-transition rules hadn't been asked about yet. Claude built the prototype to cover both instead of asking which was meant.
  - Claude misread prompt 13 as being about button styling and restyled the dropdown buttons. The user corrected this in prompt 14: they meant D's numbered 1–6 progress tracker. Claude added the tracker and kept the restyled buttons.
  - While adding the tracker, Claude noticed Hired rows had no dropdown (so no tracker) and fixed it.
  - The first prototype had a stray duplicate `</main>` tag, caught and removed right after writing.
  - Node isn't installed, so the prototypes' JavaScript was never syntax-checked, and neither prototype was opened in a browser by Claude. The Tailwind/DaisyUI CDN versions (4.0.0 / 5.0.0) were also not verified to load.