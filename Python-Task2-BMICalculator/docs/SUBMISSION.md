# Oasis Infobyte submission and demonstration guide

**Project:** NOMOLI FORGE — BMI Insight. **Internship assignment:** Task 2 — Advanced BMI Calculator. **Author:** Hassan Barrie (`barriehassan`).

## Before publication

1. Review the Task 08 release-readiness report and complete the Windows checklist where possible.
2. Confirm the intended source changes and test results. Do not claim Windows support was manually verified until it was.
3. Keep runtime databases, personal reports, virtual environments, secrets, logs and build output out of Git. Demo PNGs use synthetic records and are intentional documentation.
4. Obtain explicit approval before commit, push, release or executable packaging. Task 08 does not publish automatically.
5. Confirm the internship portal's current submission fields/deadline and whether it requires a video/post. This guide does not assert unprovided portal rules.

## Suggested 4–6 minute demonstration

- Introduce the internship Task 2 project, NOMOLI FORGE identity and local/offline architecture.
- Create a synthetic profile. Calculate 70 kg / 175 cm and explain BMI 22.86 / Normal. Show one invalid input and the controlled feedback.
- Save several synthetic measurements and open History; explain explicit saving and profile-specific storage.
- Open Trends: show both charts, period filtering, adult reference toggle, and no fabricated data.
- Open Dashboard: explain latest-versus-previous changes and filtered versus all-time counts without medical judgments.
- Switch to an empty second profile to demonstrate isolation and empty states.
- Export a PDF for the first profile; show title/date options, optional sections, background generation and the resulting table/charts/disclaimer.
- Delete one synthetic measurement with confirmation; show refresh, then close/reopen to demonstrate persistence.
- Finish with test results, educational BMI limitations, local unencrypted storage and any outstanding platform checks.

Use synthetic data throughout; do not show the user's real profile database, personal report destinations or unrelated files in a recording. Do not record passwords or credentials. Keep the application and PDF text readable at the recording resolution.

## Source package contents

The release candidate contains the BMI project code, requirements, tests, local assets, README, release/Windows/submission documentation and genuine Linux screenshots. It excludes runtime databases, generated PDFs, caches and environments. Password Forge remains unchanged in OIBSIP and is not duplicated into the BMI archive.

There is no required executable in this task. The verified source launch path is documented in the README. The author should be able to explain validation, unrounded classification, parameterized SQLite queries, service separation, chart lifecycle and process-based report generation. Acknowledge external libraries, the supplied mockup and development assistance as required by the internship rules.
