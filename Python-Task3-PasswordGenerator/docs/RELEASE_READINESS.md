# NOMOLI FORGE — Password Forge: Task 05 release readiness

**Review date:** 31 October 2026. **State:** source release candidate reviewed; the user subsequently approved commit and push.

## Scope and baseline

Reviewed the current public repository snapshot at commit `4ee00f48c828cd47123ce9d10a356c61dc3267e5`, plus the local Task 05 changes. The implementation is standard Tk/Pillow, not the CustomTkinter prototype described in the task context. No architecture migration or major feature was added. All pre-task work was preserved; a separate baseline copy was retained for comparison.

Reviewed application source, UI, CLI, bundled estimator and license, runtime/dev requirements, tests, root/project READMEs, ignore rules, documentation, launcher and artwork. Upstream estimator code/dictionaries were retained with attribution; unused upstream imports were not edited solely for style. No TODO/NotImplemented application placeholders were found. History and Settings are dashboard shortcuts, not separate screens; README now says so explicitly.

## Findings and changes

| Finding | Resolution | Evidence / limit |
| --- | --- | --- |
| Default 1280×800 client height can exceed a 768-pixel laptop screen | Initial dimensions now account for screen size and reserve space for window/taskbar chrome | Actual entry point launched on 1366×768 virtual display; desktop regression added |
| Resize callback identifier could be lost during a manual redraw | Cancel any pending resize before drawing | Existing resize and new close/lifecycle desktop checks pass |
| Copy actions can retain temporary history strings while the application object survives close | Clear canvas action callbacks during close | Desktop test asserts input, history/current state and callbacks are cleared before destruction |
| Test collection from the repository parent lacked an application import path | Add small pytest.ini with project-relative pythonpath/testpaths | Initial parent-directory attempt had 9 collection errors; final parent-directory run passes |
| Ignore rules missed alternate environments, private exports and temporary/editor files | Expand root and project .gitignore | Rules reviewed; release ZIP excludes generated caches, environments and scratch files |
| Requirements allowed untested version drift | Pin Pillow 12.3.0, pyperclip 1.11.0 and pytest 9.2.0 | Versions actually used here; runtime package metadata supports Python 3.10+ |
| README mixed prototype technology and historical setup instructions | Rewrite professional README with actual stack, correct Windows startup, security boundaries and limitations | Relative links checked; startup remains py -3 main.py |
| Screenshots directory/usage missing | Add four actual masked captures and provenance README | Generator, Lab, history and compact layout visually inspected |
| Clipboard double-failure/corrupt artwork/native typing had limited coverage | Add release failure-path and native-window regression checks | Executed in the final suite |
| Unused status kwargs and stale header-artwork wording | Remove unused parameter and correct module description | No public behavior change |

No existing project files were deleted or reset. Temporary caches already in scratch were left out of the package rather than deleting existing work. No source credentials were discovered that required removal or rotation.

## Security verification

| Requirement | Result |
| --- | --- |
| Cryptographically secure generation | Uses OS-backed secrets.choice; no random-based password generation |
| Selected categories and length | Validation plus rejection sampling enforce length 8–64 and every enabled category; regression forces rejection of an invalid candidate |
| Ambiguous exclusion | Filters 0/O/o/1/l/I; enabled/disabled cases and category combinations covered |
| Invalid input | Type/range/category errors handled; prior valid output survives invalid generation |
| Honest strength feedback | Generator uses an explicitly approximate upper bound; Lab uses local pattern scores; no guarantee or breach-history claims |
| Local Lab | Bundled zxcvbn 4.5.0; works in Python with site-packages disabled and network connections blocked |
| Manual input privacy | No logging/persistence/history; cancel pending work and clear on leave/About/close; exception messages and matched tokens are not surfaced |
| Clipboard failure | Both pyperclip and Tk failures return a safe result; no crash/input disclosure |
| Temporary history | Bounded per-session deque, clear and close behavior verified; clipboard persistence is separate |
| Repository credentials | Pattern scan and manual application/config review found no credential/token/private-key material; scope described below |

The application has no password storage or network-evaluation service. Test fixtures and the estimator's common-password dictionary intentionally contain sample/common strings; these are not user credentials. Python/Tk memory erasure is not guaranteed. System clipboard managers, OS monitoring, swap, screenshots and explicit CLI redirection remain outside the app's privacy guarantees.

### Credential-review scope

Scanned release-candidate text/config/source for recognizable GitHub, AWS, Slack and Google API token formats, private-key headers and credential-bearing connection URLs; manually reviewed application I/O and dependencies. No high-confidence match was found. Filenames were reviewed for environment/credential/key artifacts. No raw credential values were printed. This is a focused source audit, not a guarantee that every possible secret format, binary payload or historical Git object has been analyzed. Full Git history and live third-party vulnerability feeds were not audited. Dependency pinning is not a vulnerability certification.

## Executed test evidence

Environment: Linux cloud, Python **3.12.14**, Tk **9.0.4**, Pillow **12.3.0**, pyperclip **1.11.0**, pytest **9.2.0**; bundled zxcvbn **4.5.0**.

| Run | Passed | Failed | Skipped | Collection errors | Passing subchecks |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pre-change headless baseline | 72 | 0 | 2 | 0 | 77 |
| Final headless candidate | 84 | 0 | 3 | 0 | 77 |
| Final full candidate, desktop enabled | 87 | 0 | 0 | 0 | 77 |

Subchecks are reported separately and are not added to the pytest test-item count. Desktop tests are opt-in and need an actual/virtual graphical session. The portable unittest suite separately passes all 7 tests. Exact commands and latest results are recorded in VALIDATION.md.

Coverage includes generator lengths/categories/exclusion, rejection sampling, invalid types including NaN/infinity, strength labels/limits, Lab weak/common/sequence/Unicode/oversized cases, offline operation, sanitized errors, policy separation, replacement isolation, per-session history, clipboard failure/success adapters, valid/corrupt/missing artwork, actual native typing/debounce, navigation/close cleanup and resizing.

## UI and entry-point evidence

The actual main.main entry point was launched under a 1366×768 virtual display; its default 1280×680 client fit with room for chrome. Generator controls, six generations/five-entry masked history, dashboard shortcuts, Lab evaluation, settings focus and cleanup were exercised. Actual screenshots at 1280×680 and minimum 1000×680 were visually inspected for branding, background, type, spacing, visible controls and feedback. These are Linux captures; they are not Windows screenshots. No UI redesign was introduced.

## Outstanding limitations / release decision

The **source candidate is ready for review and final Windows sign-off**. There are no known failing automated tests or unresolved high-confidence source-secret findings from this audit. Source publication was subsequently approved; no GitHub release or tag is created by that approval.

Remaining work:

1. Recheck this candidate on the actual Windows laptop: normal/high-DPI scaling, fonts, keyboard focus, scrolling and OS clipboard. Prior Windows manual use is user-reported, not an independent Task 05 certification.
2. Complete the final submission checklist and record the internship demonstration using disposable data. The video has not been produced here.
3. Confirm artwork redistribution rights for any broader commercial distribution. The upstream estimator license is included; no new license for the author's own code/artwork has been assigned.
4. An installer/signed binary is outside this source release. Screens below 1000×680 logical pixels are not supported. Language-dependent strength estimates remain approximate and do not check breach databases.
5. Commit/push approval was subsequently given for the reviewed source candidate. Tags, merges and GitHub releases remain outside this publication step.

The full changed-file list is supplied as CHANGES_TASK05.md in the project folder.
