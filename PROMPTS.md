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