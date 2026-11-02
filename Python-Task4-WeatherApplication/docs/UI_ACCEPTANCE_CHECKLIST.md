# SkyCast — UI acceptance checklist

**Task 02 design review. Unchecked boxes below are future implementation checks, not completed tests.**

## Validation performed for this specification

The exact 1024 × 768 reference was visually inspected. Representative flat colors were sampled. Layout equations were checked at the 1440 logical-pixel target. The static SVG was rendered to PNG for visual inspection. No CustomTkinter interface, Windows rendering, live API request or speech playback was tested in Task 02.

Calculated sRGB contrast, using relative luminance and `(Llighter + .05)/(Ldarker + .05)`:

| Pair | Foreground | Background | Ratio |
|---|---|---|---|
| Primary / shell | #F5F5F7 | #111015 | 17.39:1 |
| Secondary / panel | #B0AFBA | #1B1B1D | 7.93:1 |
| Selected text / blue | #14151B | #BBD7EC | 12.18:1 |
| Selected secondary / blue | #353B45 | #BBD7EC | 7.54:1 |
| Error / panel | #FFB4AB | #1B1B1D | 10.13:1 |
| Focus / dark | #BBD7EC | #111015 | 12.67:1 |

These pairs exceed the project target of 4.5:1 for ordinary text. Decorative separators do not substitute for high-contrast focus boundaries. Calculations do not establish overall accessibility, screen-reader support or contrast for arbitrary future images.

## Visual fidelity — compare actual captures with approved reference

- [ ] Near-black rounded shell, compact top bar, centered search and right utilities.
- [ ] Understated Today / Tomorrow / Next 7 Days tabs; no sidebar or scenic hero substitution.
- [ ] Horizontal seven-date strip with wide light-blue selected card and narrow dark neighbors.
- [ ] Selected-card large temperature and compact details maintain the source's hierarchy.
- [ ] Rain panel stays upper-right and balanced with forecast row.
- [ ] Main-to-right column ratio remains close to the specified ratio at default size.
- [ ] Large lower-left map retains landscape proportions and dark geography.
- [ ] Lower-right city stack aligns with map top and bottom.
- [ ] Compact additional metrics and six-hour strip do not replace/shrink the map excessively.
- [ ] Typography, spacing and image sizes match documented tokens and remain readable.
- [ ] Official icon appearance difference is reviewed honestly; no false pixel-perfect claim.
- [ ] Screenshot sample geography/temperatures are absent from runtime values.

## Mandatory internship UI traceability

| Requirement | UI evidence required |
|---|---|
| FR-01 / FR-12 | City/postal search, empty-input error and candidate disambiguation |
| FR-02 / FR-13 | Real normalized bundle; graceful provider/network failure |
| FR-03 / FR-11 | Current primary/equivalent °C/°F and consistent shared toggle |
| FR-04 / FR-06 | Humidity and wind values with % and km/h |
| FR-05 / FR-08 | Meaningful text and official OpenWeatherMap icon URLs, including fallback |
| FR-07 / FR-14 | Get Weather, results panel and inline errors |
| FR-09 | Six consecutive upcoming hourly instants, correctly dated |
| FR-10 | Tomorrow through at least day +5, correct high/low labels |

- [ ] All above evidence recorded on Windows; missing mandatory data is not treated as a passed requirement.
- [ ] Current estimates, forecasts, valid times and retrieval times are distinguishable.
- [ ] Probability is %, amount is mm, and chart/stat time periods are explicit.

## Interaction, data and lifecycle

- [ ] Enter and Get Weather behave identically; ambiguous city choice is explicit.
- [ ] Selecting a date updates blue card, hourly context, rain chart and metric caption consistently.
- [ ] Tab/selection changes reuse current bundle without unnecessary network requests.
- [ ] Unit switching changes all temperatures and chart labels without cumulative rounding.
- [ ] Slow search A cannot overwrite later search B; secondary-city failures stay local.
- [ ] Missing/zero probabilities render differently; no fake loading values.
- [ ] Map pins correspond to real coordinates; weather badge requires matching fetched data.
- [ ] View wide uses existing data and restores focus after closing.
- [ ] Resize updates existing chart/images without duplicate cards, figures or timers.
- [ ] Closing during network/speech work does not crash or hang the app.
- [ ] Optional actions are absent before implementation; no decorative dead controls.

## State coverage

- [ ] First launch/no location/searching/multiple candidates/weather loading.
- [ ] Complete/partial success and Today/Tomorrow/seven-day/card selection.
- [ ] Unit change/timeout/invalid location/provider outage/rate limitation.
- [ ] Cached/stale/no-cache and empty secondary-city data.
- [ ] Missing icon, speech ready/playing/stopped/error and resizing.

Compare against all 20 rows in INTERACTION_FLOWS.md. Test keyboard and pointer recovery, not just appearance.

## Desktop and accessibility

- [ ] Actual client geometry fits available work area; distinguish screen size from client size.
- [ ] 1440 × 900 client where supported; 1366 × 768 screen; 1024 × 700 client checked.
- [ ] Windows 100%, 125%, 150% scaling; logical-work-area fallback checked.
- [ ] Forecast/hourly strips scroll horizontally, page vertically; wheel focus behaves predictably.
- [ ] Minimum text 12 logical px, useful 40 px targets, no overlap/clipped action.
- [ ] Visible focus on dark surfaces and selected blue card; selection not conveyed only by color.
- [ ] Tab/arrows/Enter/Space/Escape paths complete; focused item scrolls into view.
- [ ] Chart values and map locations have text/list alternatives.
- [ ] Icons have meaningful labels; errors have message and recovery action.
- [ ] Test actual screen-reader behavior before making support claims.

## Seven enhancement placements and behavior

- [ ] EN-01: Listen/Stop near detail, never autoplay; location/unit change stops old speech.
- [ ] EN-02: Star and favorites popup, persistent success/failure feedback.
- [ ] EN-03: Four compact metric tiles, measurement period clear.
- [ ] EN-04: Expandable trend below hourly strip; map retained and resources cleaned.
- [ ] EN-05: Cache badge, last retrieval, stale warning, Refresh and expired-interval handling.
- [ ] EN-06: Sunrise/sunset selected-day local times or honest unavailable state.
- [ ] EN-07: Consent before any IP lookup; confirm/correct approximation; no raw IP persistence.

## Windows evidence template

Record OS, Python, Tk, CustomTkinter, screen/client dimensions, scaling, app revision and data source. Capture Today, Tomorrow, seven-day selection, a narrow layout and an error/partial state. For Phase 2 capture cache/voice/favorites behavior. Include a pass/fail/blocked result and defect notes for each group. Use real screenshots and real execution evidence; the static Task 02 wireframe is not acceptance evidence for the app.
