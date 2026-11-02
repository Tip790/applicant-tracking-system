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

## 2026-11-02 — Phase 6: archive, unarchive and delete candidates

### Prompts
1. `/implement @prd/applicant-tracking-system.md  @plans/applicant-tracking-system.md  implement Phase 6`
2. `approved, go ahead`
3. `approved, go ahead`
4. `continue`
5. `approved, go ahead`
6. `continue`
7. `contine`
8. `continue!`
9. `manual verification passes, finish the process`

### Summary
- **Outcome:** Phase 6 was built on top of Phase 5:
  - `hiring/rules.py` gained:
    - `archived_reason`, the one "archived = read-only" message.
    - `archive_refusal_reason` / `archive_candidate`: archiving is refused while any application is active, and the message lists them as "Opening (Stage)".
    - `unarchive_candidate`.
    - `delete_refusal_reason` / `delete_candidate`: deleting is refused once the candidate has any application, and the message suggests archiving.
  - `move_refusal_reason` now refuses every move on an archived candidate's applications. `application_refusal_reason` refuses archived candidates. `candidates_who_can_apply_to` excludes them. `move_options` returns `None` when no button would be offered.
  - POST-only `candidate_archive`, `candidate_unarchive` and `candidate_delete` views. A refusal shows as an error message on the candidate page, and a successful delete goes to the candidate list. The edit page and the "record application" page (started from the candidate) redirect an archived candidate back to their page with the read-only message.
  - Templates:
    - A new `archived_badge.html` partial on the candidate list, the candidate page and the table rows.
    - The candidate page shows Unarchive, or Edit and Archive, plus Delete only when the candidate has no applications. Delete asks first through `hx-boost` + `hx-confirm`. An archived candidate's page has a read-only alert and no "Record application" button.
    - The Actions dropdown shows an "is archived" note instead of move buttons.
    - The candidate list has a "Show archived" checkbox.
  - 163 tests pass. Three behaviors were built test-first, each through an approved RED → GREEN cycle:
    - Archiving is refused while an application is active, and the reason lists the blocking applications.
    - A tampered move on an archived candidate's application returns the 422 alert and changes nothing.
    - Deleting a candidate with any application is refused with an archive suggestion, while one with no applications is deleted.
  - Ordinary tests cover:
    - The archive/unarchive/delete views and their messages.
    - Refusing edits, refusing applications (in the rules and through a tampered form POST), and the record-page redirect.
    - The picker exclusion, the candidate page buttons and the dropdown note.
    - The "Show archived" toggle, alone and with search.
    - Login on the new POST actions, plus a new test that every POST action refuses GET.
  - Ruff check and format are clean, there are no missing migrations, and the CSS build contains the new badge, checkbox and outline-button styles. The user confirmed manual verification in the browser.
- **Deviations:**
  - The user approved all three TDD behaviors and all three tests without changes. Prompt 7 ("contine") was a typo; Claude took it as approval of the third test and said so.
  - Claude made a few choices without asking:
    - The wording of every refusal and archived message.
    - Showing Delete only for candidates with no applications.
    - A browser confirm on Delete (through `hx-boost` + `hx-confirm`, since HTMX is the only JavaScript) but none on Archive, because unarchiving undoes it.
    - An Archived badge in the applications table rows too.
    - Checking "archived" before every other move rule.
- **Sideways:**
  - All three RED runs failed on assertions. For behaviors 1 and 3, Claude first wrote stubs (an `archive_candidate` and a `delete_candidate` that skipped the check). Behavior 2 needed no stub.
  - Behavior 2's first GREEN run still failed because Django HTML-escapes the apostrophe in "can't". Claude made a mechanical repair (unescape the response before checking the text) and noted it in one line. The assertion itself didn't change.
  - Claude's first draft of the archive view tests had inline `JobOpening` imports and an unused `opening` fixture. Both were cleaned up before the first run.
  - Claude never opened the pages in a browser, so the Delete confirm dialog was only checked during the user's manual verification.

## 2026-11-02 — Phase 5: progress tracker and reopen

### Prompts
1. `/implement @prd/applicant-tracking-system.md  @plans/applicant-tracking-system.md  implement Phase 5`
2. `only do the first 2 as TDD, remove the third one focused on the color of the tracker`
3. `approved, go ahead`
4. `continue`
5. `approved, go ahead`
6. `continue!`
7. `when displaying what stage an applicant is on, the final stage badge doesn't fit within it's border, fix if possibke`
8. `if you believe that anything needs to be added to CLAUDE.md add it, then continue with the implement skill`

### Summary
- **Outcome:** Phase 5 was built on top of Phase 4:
  - `hiring/rules.py` gained `previous_stage` (the from-stage of the StageChange that moved the application into its current stage, or `None` if the history doesn't show it) and `progress_steps` (the six pipeline steps, each marked reached; Rejected/Withdrawn count up to the stage they left from). `move_refusal_reason` now lets Rejected or Withdrawn move only back to that previous stage, and refuses every other target with "Rejected applications can only be reopened to Interview." (names filled in). `move_options` returns only a `reopen` option for them. `Application` got matching `previous_stage()` and `progress_steps()` methods for the templates.
  - A new `progress_tracker.html` partial: DaisyUI steps with reached steps in blue, red for Rejected (with "Rejected after [stage]") and yellow for Withdrawn (with "Withdrawn from [stage]"). Hired shows all six steps. The Actions dropdown shows it under the name and badge, followed by a divider and a warning-style "Reopen to [stage]" button for Rejected/Withdrawn.
  - Stage badges got `whitespace-nowrap` so "Final Review" stays inside its border.
  - 144 tests pass. Two behaviors were built test-first, each through an approved RED → GREEN cycle: a reopen to the previous stage succeeds and records exactly one StageChange with the right from/to/user (for both Rejected and Withdrawn), and every other move out of Rejected/Withdrawn is refused with a reason naming the reopen stage and changes nothing. Ordinary tests cover the reopen option, the tracker's reached steps for every pipeline stage and for Rejected/Withdrawn, the dropdown's colored steps, notes and single Reopen button, the Hired full tracker, the re-rendered row after a reopen, and a tampered wrong-stage reopen returning the 422 alert.
  - Ruff check and format are clean, there are no missing migrations, and the CSS build contains the step, divider, warning-button and nowrap styles.
  - `CLAUDE.md` gained three lines: use the stage badge and tracker partials, write Tailwind class names out in full, and reopen reads the history (so tests must reach Rejected/Withdrawn through `rules.move_application`).
- **Deviations:**
  - Claude proposed three TDD behaviors. The user dropped the third (the rejected tracker's red steps and note), so it was built and tested normally instead.
  - Claude said it would lay the tracker out vertically, then switched to horizontal and widened the dropdown from 18rem to 24rem because six vertical steps made the dropdown very tall. It told the user when presenting the manual check.
  - Claude made a few choices without asking: yellow steps for Withdrawn (matching its badge), the wording of the refusal reason and of the "Withdrawn from" note, the history-based definition of the previous stage, and offering no moves when the history doesn't show one.
  - The user reported a badge problem during manual verification (prompt 7) and then asked Claude to continue with the skill (prompt 8) without separately saying that verification passed. Claude took prompt 8 as approval to finish the phase.
- **Sideways:**
  - Both RED runs failed on assertions without needing stubs. Behavior 1's test first asks `move_refusal_reason` whether the reopen is allowed, which failed on the old "can't be moved" answer.
  - Two Phase 4 tests no longer matched the rules: `test_rejected_and_withdrawn_cannot_move_yet` was deleted when behavior 1's test was written (Claude said so at the RED step), and `test_final_stages_offer_no_moves_yet` was renamed and narrowed to Hired and to Rejected/Withdrawn with no history.
  - Claude left an unused `staff_user` fixture in one test and removed it. Ruff flagged one line over 100 characters, which `ruff format` fixed. The tests were re-run afterwards and still passed.
  - The user found that the "Final Review" badge spilled outside its border in the browser. Claude hadn't caught it because it never opened the page; the tests only check the HTML. Five test assertions that matched the exact badge HTML were updated for the new class.

## 2026-11-02 — Phase 4: moving applicants with HTMX

### Prompts
1. `/implement @prd/applicant-tracking-system.md  @plans/applicant-tracking-system.md  implement Phase 4`
2. `those design choices are fine, continue`
3. `approved, go ahead`
4. `continue`
5. `approved, go ahead`
6. `continue`
7. `approved, go ahead`
8. `continue`
9. `manual verification passed, go ahead, before commit update CLAUDE.md with only the most important lines, like the HTMX conventions`
10. `remove the firefox mention from PROMPTS.md then continue` (correction, after interrupting Claude's edit and commit)
11. `keep the dropdown browser part, include these messages in the PROMPTS.MD as well, then continue` (correction, after interrupting Claude's edit)
12. `that can stay, continue` (after interrupting Claude's attempt to reword its own description of prompt 10 in the log)

### Summary
- **Outcome:** Phase 4 was built on top of Phase 3:
  - `hiring/rules.py` gained `move_refusal_reason` (the Flexible rules: active → any other active stage, Rejected or Withdrawn; Hired only from Offer; Hired final; nothing out of Rejected/Withdrawn until Phase 5's reopen; no move to the current or an unknown stage), `move_application` (checks the rule, then saves the stage and a StageChange in one transaction) and `move_options` (the buttons the dropdown offers, each checked with `move_refusal_reason`). `Application.move_options()` hands this to the templates.
  - A POST-only `application_move` view at `/applications/<pk>/move/`. Success returns only the re-rendered row plus an out-of-band empty `#move-alert` that clears old errors. A refusal returns 422 with a DaisyUI error alert and `HX-Retarget: #move-alert`. An `htmx-config` meta tag in `base.html` makes HTMX swap 422 responses.
  - An `application_actions.html` partial: a DaisyUI popover dropdown (so the scrolling table card doesn't clip it) with the candidate's name, a stage badge and buttons for only the legal moves — Advance (primary), Back (ghost), Jump to (small ghost), Reject (outlined error), Mark withdrawn (ghost). Hired shows "Hired is final." The All Applications page and the opening page share it through the row partial.
  - 116 tests pass. Three behaviors were built test-first, each through an approved RED → GREEN cycle: a legal move records exactly one StageChange with the right from/to/user, illegal Hired moves are refused with a reason and change nothing, and a tampered illegal POST returns a 422 alert with the stage unchanged. Ordinary tests cover every allowed Flexible move, Rejected/Withdrawn and same/unknown-stage refusals, the transaction rollback, the button options, the row-only success fragment, POST-only, 404, login, closed openings, the dropdown labels and styles, the Hired note and the opening page.
  - Ruff check and format are clean, there are no missing migrations, and the CSS build contains the new button, alert and popover styles. The user confirmed manual verification in the browser.
  - `CLAUDE.md` gained three lines: stage moves go through the rules module, the HTMX row-action conventions, and the popover dropdown. At the user's request it was committed with this phase, including the user's own earlier uncommitted edits to it.
- **Deviations:**
  - Claude proposed two design choices before starting (422 + `HX-Retarget` + an `htmx-config` meta tag for the alert, and DaisyUI's popover dropdown). The user accepted both.
  - Claude made a few choices without asking: the exact wording of the refusal reasons, refusing all moves out of Rejected/Withdrawn until Phase 5, refusing a move to the current stage, clearing the old alert out-of-band after a successful move, and showing "No moves available." for Rejected/Withdrawn rows.
  - The dropdown header shows the name and stage badge now; the 1–6 tracker is left for Phase 5.
- **Sideways:**
  - Nothing failed. All three RED runs failed on assertions. For behaviors 1 and 3, Claude first wrote stubs (a `move_application` that changed nothing, and a move view that swallowed refusals and returned the row) so the tests could fail on assertions.
  - Claude left an unused `popover_id` variable in the dropdown template's `with` tag and removed it right away. A first draft of the Hired-dropdown test sliced the HTML wrongly (it assumed the toggle button was inside the slice) and was fixed before the first run.
  - Ruff reformatted one file. The tests were re-run afterwards and still passed.
  - The dropdown uses CSS anchor positioning, a newer browser feature. It worked in the user's browser during manual verification.
  - Claude's first draft of this log said the dropdown was "confirmed working" in Firefox, which Claude didn't know. Claude tried to reword it and commit in the same step. The user stopped both and asked for the Firefox mention to be removed (prompt 10). When Claude's next edit would have dropped the whole bullet, the user stopped that too and asked to keep the dropdown browser note (prompt 11).

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