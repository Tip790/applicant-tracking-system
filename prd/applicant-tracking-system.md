# PRD: Applicant Tracking System

## Problem Statement

The company's hiring staff have no single place to track the people applying for jobs. Candidates arrive from the company website, job boards, referrals and other outside sources. Staff need to know who each candidate is, which job openings they have applied to, and where each application stands in the hiring process. Without a shared system, staff can't easily answer "where is everyone for this job?" or "what happened to this applicant?" Duplicate candidate records and duplicate applications creep in, and there is no reliable history of who moved an applicant, or when.

Staff also lack agreed rules for the awkward cases: what happens to a candidate's record over time (editing, archiving, deleting), what happens to in-progress applicants when a job opening closes, and whether a closed opening can be reopened.

## Solution

An internal, login-only web application for hiring staff. Candidates never log in. Staff can:

- Keep one record per candidate (identified by email), including where the candidate came from.
- Create and edit job openings, tag them with skills, and close or reopen them at any time.
- Record a candidate's application to an opening, either from the candidate's page or from the opening's page. The system prevents duplicate applications and applications to closed openings.
- See every application in one searchable, filterable table. Each row has an **Actions** dropdown that shows a numbered progress tracker (Applied → Screening → Interview → Final Review → Offer → Hired) and buttons for only the stage moves the rules allow. Moving an applicant updates just that row, with no full page reload.
- See a full history of every stage change, including who made it and when.
- Archive candidates who are no longer active, without losing their hiring history.

## User Stories

### Access

1. As a staff member, I want to log in with a username and password, so that only employees involved in hiring can see candidate data.
2. As a staff member, I want every page to require login, so that candidate information is never exposed to anonymous visitors.
3. As a staff member, I want to land on the All Applications page after logging in, so that I immediately see the state of the hiring pipeline.
4. As a staff member, I want all staff to have the same abilities in the app, so that I'm never blocked waiting for someone with more permissions during day-to-day work.
5. As a superuser, I want to use the Django admin site to repair data and permanently delete records, so that rare corrections and data-removal requests can be handled outside the normal staff screens.

### Candidates

6. As a staff member, I want to create a candidate with first name, last name, email, optional phone, source, source details and notes, so that I have their basic information on file.
7. As a staff member, I want to choose a candidate's source from Website, Job Board, Referral or Other, so that I can see where candidates come from.
8. As a staff member, I want a free-text source details field (e.g. "Indeed" or "referred by Maria in Sales"), so that I can capture specifics the dropdown doesn't cover.
9. As a staff member, I want the system to reject a new candidate whose email already exists, regardless of capitalization, so that the same person isn't entered twice.
10. As a staff member, I want the duplicate-email error to tell me that the candidate already exists and link to the existing record, so that I can go straight to it.
11. As a staff member, I want to edit a candidate's information at any time while they're not archived, so that I can keep their details current.
12. As a staff member, I want a candidate list with search, so that I can quickly find a person.
13. As a staff member, I want archived candidates hidden from the candidate list by default, with a "Show archived" toggle, so that the list shows people who are currently relevant.
14. As a staff member, I want to see a candidate's page listing all their applications and their current stages, so that I can see everything they've applied for in one place.
15. As a staff member, I want to archive a candidate, so that people who are no longer in consideration stop cluttering my lists while their history is kept.
16. As a staff member, I want the system to stop me archiving a candidate who still has an active application (Applied, Screening, Interview, Final Review or Offer), and tell me which applications are blocking it, so that nobody disappears from view mid-process.
17. As a staff member, I want archived candidates to be read-only, so that nobody accidentally edits or moves applications for someone who has been set aside.
18. As a staff member, I want to unarchive a candidate, so that I can bring them back if they become relevant again.
19. As a staff member, I want to delete a candidate who has no applications, so that I can clean up records created by mistake.
20. As a staff member, I want the system to stop me deleting a candidate who has any application and suggest archiving instead, so that hiring history is never destroyed from the app.
21. As a staff member, I want archived candidates excluded from the candidate picker when recording an application, so that I don't add applications for someone who is set aside.

### Job openings

22. As a staff member, I want to create a job opening with a title, department, location and description, so that I can track a position we're hiring for.
23. As a staff member, I want to edit a job opening, so that I can correct or update its details.
24. As a staff member, I want an openings list showing each opening's status, so that I can see what we're hiring for.
25. As a staff member, I want to close an opening, so that it stops accepting new applications once we have enough applicants.
26. As a staff member, I want a confirmation when closing an opening that tells me how many applications are still active, so that I understand that in-progress applicants will continue.
27. As a staff member, I want applications already in progress on a closed opening to keep moving through the stages normally, so that we can finish interviewing the shortlist after closing.
28. As a staff member, I want closed openings clearly marked wherever they appear (e.g. a "closed" badge), so that I don't mistake them for open roles.
29. As a staff member, I want to reopen a closed opening, so that I can undo a mistaken close or resume hiring for the same role.
30. As a staff member, I want an opening's page to show its applications in the same table and with the same actions as the All Applications page, pre-filtered to that opening, so that I can see where everyone stands for this one job.

### Skills

31. As a staff member, I want to attach skills to a job opening, so that the opening shows what it requires.
32. As a staff member, I want to choose from existing skills on the opening form, so that the same skill is shared across many openings.
33. As a staff member, I want to add a new skill from the opening form when it isn't in the list yet, so that I'm never blocked waiting for someone else to create it.
34. As a staff member, I want a new skill that matches an existing one except for capitalization (e.g. "python" vs "Python") to reuse the existing skill, so that the skill list stays free of duplicates.
35. As a superuser, I want to manage and merge skills in Django admin, so that near-duplicates like "JS" and "JavaScript" can be cleaned up.

### Applications

36. As a staff member, I want to record a new application from a candidate's page by picking an opening, so that I can log an application when a candidate contacts us.
37. As a staff member, I want to record a new application from an opening's page by picking a candidate, so that I can process a batch of applicants for one job.
38. As a staff member, I want the opening picker to show only open openings the candidate hasn't already applied to, so that I can't pick an invalid choice.
39. As a staff member, I want the candidate picker to show only non-archived candidates who haven't already applied to that opening, so that I can't pick an invalid choice.
40. As a staff member, I want the system to refuse a second application for the same candidate and opening, even if the form is bypassed, so that each person has at most one application per opening.
41. As a staff member, I want the system to refuse an application to a closed opening, so that closing an opening really stops intake.
42. As a staff member, I want a new application to start in the Applied stage, so that every application begins at the start of the process.
43. As a staff member, I want a candidate who was rejected earlier to "re-apply" to the same opening by reopening their old application, so that their history stays in one place without breaking the one-application rule.

### Pipeline: viewing

44. As a staff member, I want an All Applications table listing each application's candidate (name and email), opening, source, current stage, stage history and time in current stage, so that I can see where everyone is.
45. As a staff member, I want to search the table by candidate name, so that I can find one applicant quickly.
46. As a staff member, I want to filter the table by opening, so that I can focus on one job.
47. As a staff member, I want to filter the table by stage, including an "Active only" option, so that I can focus on applicants still in progress.
48. As a staff member, I want each stage shown as a colored badge (e.g. green for Hired, red for Rejected), so that I can scan statuses at a glance.
49. As a staff member, I want each row's Actions dropdown to show a numbered 1–6 progress tracker (Applied, Screening, Interview, Final Review, Offer, Hired) with the reached steps highlighted, so that I can see visually how far the applicant has progressed.
50. As a staff member, I want the progress tracker for a rejected applicant to show the reached steps in red with a note such as "Rejected after Interview", so that I can tell how far they got before being rejected.
51. As a staff member, I want the progress tracker for a withdrawn applicant to show the stage they withdrew from, so that I know where they left the process.

### Pipeline: moving applicants

52. As a staff member, I want the Actions dropdown to offer only the moves the rules allow, so that I can't make an illegal move by accident.
53. As a staff member, I want a highlighted "Advance to [next stage] →" button, so that the most common move is one click.
54. As a staff member, I want a "← Back to [previous stage]" button, so that I can correct a premature advance.
55. As a staff member, I want "Jump to" buttons for the other active stages, so that a strong applicant can skip a stage or be moved back further.
56. As a staff member, I want "Reject" and "Mark withdrawn" buttons available from any active stage, so that I can close out an application whenever it ends.
57. As a staff member, I want "Hired" to be available only from the Offer stage, so that nobody is hired without going through an offer.
58. As a staff member, I want Hired to be final, so that a completed hire can't be undone by a misclick.
59. As a staff member, I want a "Reopen to [previous stage]" button on Rejected or Withdrawn applications that returns them only to the stage they were in before, so that I can undo a mistaken rejection without letting someone jump ahead.
60. As a staff member, I want moving an applicant to update only that table row, without reloading the whole page, so that I keep my place, search and filters.
61. As a staff member, I want the server to refuse an illegal move even if the request is tampered with, and show me an error alert explaining why, so that the rules can't be bypassed.
62. As a staff member, I want moves on archived candidates' applications to be refused, so that archived records stay read-only.

### History

63. As a staff member, I want every stage change recorded with the from-stage, to-stage, the staff member who made it, and when, so that I can answer "who rejected this applicant, and when?"
64. As a staff member, I want the history to begin with the application's creation in Applied, so that it is complete from the start.
65. As a staff member, I want a stage move and its history record to be saved together or not at all, so that the current stage and history never disagree.

## Implementation Decisions

### Stack and tooling
- Python and Django, using SQLite as the database. Dependencies and commands are managed with uv.
- Styling uses Tailwind CSS with DaisyUI components, integrated through django-tailwind-cli. Interactivity uses HTMX only, with no additional JavaScript libraries (drag-and-drop was explicitly rejected so a library like SortableJS is never needed).
- Ruff for linting and formatting.

### Authentication and permissions
- Django's built-in authentication (login and logout views). Every app view requires a logged-in user.
- One kind of staff user, with no role-based permissions inside the app. The Django admin site is available only to superusers, and permanent deletion of candidates with history happens only there.
- After login, users are redirected to the All Applications page.

### Models
- **Candidate**
  - Fields: first name, last name, email, optional phone, source, source details (free text), notes, an archived flag, and created/updated timestamps.
  - Source is a fixed set of choices: Website, Job Board, Referral, Other.
  - Email is required and unique ignoring case. This is enforced at the database level (e.g. a unique constraint on the lowercased email) and surfaced as a friendly form error that links to the existing record.
  - Source belongs to the candidate, not to individual applications.
- **JobOpening**
  - Fields: title, department, location, description, status (`open` / `closed`), and created/updated timestamps.
  - Many-to-many relationship to Skill.
- **Skill**
  - A name, unique ignoring case. It is shared across many openings and is not related to candidates.
- **Application**
  - Foreign keys to Candidate and JobOpening, a current stage, and created/updated timestamps.
  - A database-level unique constraint on the (candidate, opening) pair.
  - The current stage is stored directly on the application so the table can be filtered quickly.
- **StageChange**
  - Foreign key to Application, plus from-stage (empty for the initial entry), to-stage, the user who made the change, and a timestamp.
  - One StageChange row is created for "Applied" when an application is created.
  - "Previous stage" (for reopening) and "time in current stage" are derived from these rows.
- **Stages**
  - A fixed, ordered set of choices: Applied, Screening, Interview, Final Review, Offer, Hired, Rejected, Withdrawn.
  - Active stages are Applied, Screening, Interview, Final Review and Offer. Final stages are Hired, Rejected and Withdrawn.

### Business rules (kept in one place, e.g. model methods or a small service module, so views and forms share them)
- **Stage transitions ("Flexible" rules)**
  - From any active stage, an application can move to any other active stage, or to Rejected or Withdrawn.
  - Hired is reachable only from Offer.
  - Hired is final; no moves out of it are allowed.
  - Rejected or Withdrawn can move only back to the stage the application was in immediately before. This is the "reopen" move.
  - Moves are refused when the candidate is archived.
- **Performing a move**
  - A move updates the application's stage and creates a StageChange inside one database transaction.
  - The function that performs a move first checks the rule and refuses illegal moves with a human-readable reason.
- **Archiving and deleting candidates**
  - Archiving is refused while the candidate has any application in an active stage. The error lists the blocking applications.
  - Archived candidates are read-only: no edits, no new applications, no stage moves. They can be unarchived.
  - Deleting is allowed only when the candidate has zero applications. Otherwise staff are told to archive.
- **Creating applications**
  - Refused when the opening is closed, the candidate is archived, or an application already exists for that pair.
  - The database constraint is the final safeguard behind the form validation.
- **Closing and reopening openings**
  - Closing only blocks new applications; existing applications are unaffected and can still be moved.
  - Openings can be closed and reopened any number of times.
- **Adding skills**
  - A new skill name that matches an existing skill, ignoring case, reuses the existing skill instead of creating a duplicate.

### Views, forms and URLs
- **Candidates**
  - Pages: list (with search and a "Show archived" toggle), detail (listing their applications), create, edit.
  - Actions: archive, unarchive, and delete (only when permitted).
- **Job openings**
  - Pages: list, detail, create, edit.
  - The edit form includes skill selection and a field for adding a new skill.
  - A close/reopen action, with a confirmation that shows how many applications are still active when closing.
- **Applications**
  - A single application-creation form and view that accepts a candidate and an opening.
  - It is reached from the candidate page (candidate pre-filled, choose an opening) or from the opening page (opening pre-filled, choose a candidate).
  - The pickers exclude invalid choices: closed openings, archived candidates, and pairs that already have an application.
- **All Applications page ("variant E", chosen through UI prototyping)**
  - A table with columns: candidate (name and email), opening (with a closed badge where relevant), source, stage badge, stage history, time in stage, and actions.
  - Filters: search by candidate name, opening, and stage (including "Active only").
- **Opening detail page**
  - Reuses the same table template, pre-filtered to that opening.
- **Actions dropdown (one per row)**
  - At the top: the candidate's name, a stage badge, and a numbered 1–6 progress tracker (DaisyUI steps with connecting lines).
  - Below that, styled action buttons offering only the legal moves:
    - "Advance to [next] →" (primary)
    - "← Back to [previous]" (ghost)
    - "Jump to" buttons for the other active stages (small ghost buttons)
    - "Reject" (outlined error)
    - "Mark withdrawn" (ghost)
    - "Reopen to [previous]" (warning), for Rejected or Withdrawn applications only
  - Hired applications show the full tracker and a "Hired is final" note instead of buttons.
- **Stage move endpoint**
  - A single view that accepts a POST with the target stage.
  - On success it returns only the re-rendered table row as an HTMX fragment.
  - On a refused move it returns an error response with a DaisyUI alert explaining the reason, and the stage is unchanged.
  - Both the All Applications page and the opening page use this same endpoint and row template.
- **Reusable partials**
  - The progress tracker, the table row and the Actions dropdown are each reusable template partials.
- **Django admin**
  - Models are registered in Django admin for superuser maintenance: data repair, permanent deletion, and merging skills.

### Testing
- pytest with pytest-django, run with `uv run pytest`. Shared fixtures provide a logged-in staff client, a candidate, an opening and an application.
- Required coverage:
  - Candidate email uniqueness ignores case.
  - Applying twice to the same opening is refused, as are applying to a closed opening and applying as an archived candidate.
  - Every Flexible stage rule: allowed moves succeed; illegal moves are refused (Hired only from Offer, Hired final, reopen only to the previous stage).
  - Each successful move creates exactly one StageChange recording the correct user.
  - Archiving is blocked while an application is active, and deleting is blocked once a candidate has applications.
  - The HTMX move view returns only the row fragment, and refuses an illegal move with an error.
  - Every page requires login.

## Out of Scope

- Candidate-facing features of any kind: candidate login, a public careers page, or self-service applications.
- Role-based permissions inside the app (e.g. separate recruiter and hiring-manager roles).
- Skills on candidates, and any candidate-to-opening skill matching.
- Drag-and-drop pipeline boards, and any JavaScript library beyond HTMX.
- Kanban/board-style pipeline layouts (prototyped as variants A and B and not chosen).
- Résumé or file uploads, LinkedIn URLs, salary ranges and employment types on openings (not requested; could be added later).
- Tracking source per application (source is per candidate only).
- Soft duplicate warnings based on matching names or phone numbers (only email uniqueness is enforced).
- Recording when openings were opened or closed (e.g. `closed_at`) and time-to-fill reporting.
- Limits on openings with multiple positions (e.g. preventing reopening after a hire).
- Creating a candidate and their application in a single combined form.
- Email notifications, interview scheduling, analytics dashboards and reports.

## Further Notes

- Two throwaway prototypes informed these decisions and are kept for reference only. They must not be promoted into production code.
  - The stage-rules prototype explored the stage-transition rule sets (Strict, Flexible, Free) and the candidate archive/delete options. **Flexible** was chosen, together with "delete only if no applications" and "block archiving while an application is active."
  - The pipeline-UI prototype explored five screen layouts. **Variant E** was chosen: variant C's table combined with variant D's progress tracker and styled action buttons, all inside a per-row dropdown.
- Under the chosen rules, a candidate rejected earlier "re-applies" to the same opening by having their old application reopened. A second application is never created for the same opening.
- The developer is a beginner, so the implementation should prefer standard Django patterns: model constraints, ModelForms, class-based or simple function views, and template partials. Avoid clever abstractions.
- This is a CIDM 3312 course project (Project #1). AI usage is logged in the repository's prompt log at the end of each session, and only when the developer asks for it.
