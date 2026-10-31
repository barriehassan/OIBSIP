# Final manual QA and internship submission checklist

Use disposable demonstration values. Never display real account credentials. This checklist records work still to perform on the target laptop; check items only after observing them.

## Windows release confirmation

- [ ] Extract the Task 05 review package to a separate directory, preserving existing work.
- [ ] Check `py -3 --version` and `py -3 -m tkinter`.
- [ ] Install the pinned dependencies with the same Python interpreter.
- [ ] Run `py -3 main.py`; confirm branding, background and full-window fit.
- [ ] Check 1366×768 or the laptop's normal resolution and chosen DPI scaling.
- [ ] Confirm fonts, contrast and spacing; resize down to 1000×680 if the desktop allows it.
- [ ] Generate at lengths 8, 18 and 64; inspect each selected category and lookalike exclusion.
- [ ] Enter invalid lengths and select fewer than two categories; confirm useful feedback and preserved prior output.
- [ ] Verify slider/numeric synchronization and Show/Hide.
- [ ] Test current/history copy with a disposable value, confirm the complete value, then remove it from the clipboard/editor.
- [ ] Enable auto-copy, verify it, then disable it.
- [ ] Generate six values; confirm only the latest five remain, masked by default.
- [ ] Clear history; confirm the current generated output is intentionally retained.
- [ ] Verify Generate, History and Settings dashboard shortcuts and About.
- [ ] Enter `password` in Lab; expect Very weak after a brief pause. Check now must also update.
- [ ] Check a fresh replacement, Show/Hide/Clear, oversized input and scrollable findings.
- [ ] Switch away while typing; verify Lab clears and never enters history or auto-copy.
- [ ] Check Tab, Enter/Space, Ctrl+G and Esc in both modes.
- [ ] Close/reopen; confirm no previous history or manual input remains.
- [ ] Run the ordinary and desktop-enabled test commands in the README and record actual results.

Windows launch and manual use were reported by the author before Task 05; the refinements in this candidate still need this final target-laptop confirmation. Cloud automated evidence is Linux/Tk 9, not Windows certification.

## Submission preparation

- [ ] Confirm the assigned task number, required features, AI/attribution policy, submission dates and video/link format from the internship brief.
- [ ] Review source modules and explain secure randomness, rejection sampling, ephemeral history and strength-estimation limits.
- [ ] Capture authentic Windows screenshots using disposable masked data if needed.
- [ ] Record a short demo: generation/settings, invalid input, masking/copy, history, Lab weak input, replacement and cleanup.
- [ ] Explain that Lab is local and not a breach-database check.
- [ ] Check the repository contains no private files, credentials, environment folders or real password exports.
- [x] Task 05 diff approved by the author for commit/push after review. No release/tag/merge is included.
- [ ] Attach the repository and demonstration links required by the internship.

Video recording can be done after the chosen projects are finished, provided the internship's actual deadline and submission instructions allow it. No video or internship acceptance is claimed here.
