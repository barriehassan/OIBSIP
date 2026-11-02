# SkyCast — Approved UI requirements

**Task 01 · composition constraints, not a new design**

> **Task 02 update — 2 November 2026:** The exact reference `image(20261102-081659).png` is now supplied and visually inspected. The absence noted below describes Task 01 at preparation time. See [UI_DESIGN_SPEC.md](UI_DESIGN_SPEC.md) for the measured anatomy and detailed translation.

## Authority

The exact user-approved dark weather dashboard image is the authoritative visual reference. It must not be replaced with another dashboard. The text specification describes the composition below; the actual selected image was not available or positively identified in this execution. No pixel measurements, visual comparison or screenshot fidelity is claimed. Attach that exact image before Task 02 layout signoff.

Clean Forecast Studio contributes only compact statistics cards. It is not a replacement layout. No scenic hero, sidebar-first redesign, light-themed calculator, authentication screen or unrelated weather concept is authorized.

## Composition and behavior

| Region | Preserve | Functional contract |
|---|---|---|
| Shell | Near-black/charcoal, large rounded container, restrained grey/blue/lavender accents | Native resizable Windows window; no heavy decorative gradients |
| Top left | Supporting/menu icon and selected location | Show location with country/region as needed; icons open real controls only |
| Top center | Prominent city search and search icon | Visible Get Weather action plus Enter; candidate chooser below search |
| Top right | Compact display controls | Unit toggle; no nonfunctional theme/avatar/notification controls |
| Forecast navigation | Today, Tomorrow, Next 7 days | Keyboard reachable; visible selected state |
| Upper left/center | Horizontal rounded daily cards | Day/date, condition icon, labeled high/low; active card light blue |
| Upper right | Chance of Rain vertical bars | Actual probability, 0–100% scale and interval labels; missing data not a zero-height measured bar |
| Lower left | Large dark Global Map | Dominant map area, real geocoded pins; truthful location-overview caption |
| Lower right | Other Large Cities compact cards | Resolved places with fetched current values and individual loading/error states |
| Secondary row | Compact Clean Forecast Studio statistics | Humidity, wind, later feels-like and probability; map/city panels remain visible |

Do not copy sample temperatures or cities from the image into runtime observations. Suggested city names may seed search choices, but their coordinates must be resolved and weather fetched. No weather value appears before data arrives.

## Mandatory data placement

Keep a compact current-conditions summary alongside the forecast information: condition text and icon, current primary temperature and secondary °C/°F equivalent, humidity, wind and valid time. Avoid an oversized hero. Place the six upcoming hours in a compact secondary horizontal strip beneath the daily cards; use horizontal scrolling when needed rather than shrinking card text. This strip is distinct from the daily row, so six hourly entries cannot be mistaken for six days.

The project requires current conditions even though the mockup emphasizes forecasts. The proposed placements preserve all named regions; Task 02 must resolve their exact sizes against the original image.

## Tab and selection state

- **Today:** select today's daily card; show current conditions and the next six hourly entries. Label tomorrow's hours when the strip crosses midnight.
- **Tomorrow:** select the next location-local date; show forecast summary and that date's hourly detail. Do not describe tomorrow's temperature as current.
- **Next 7 days:** show today through +6; select a card to update daily details and rain series for that date. The current summary remains explicitly separate.
- Card selection updates supporting details and charts, while each other-city card remains clearly labeled as current weather for its own location. Selecting an other-city card initiates a new main-location request.
- Loading a new city updates the location label only with coherent result state. Any preserved old city result retains its old city label; never show city A values under city B.

Rain bars show the next six hourly probabilities in Today and a labeled six-hour window of the selected day in future-date views. If scrolling changes the window, chart and hourly labels move together. Enhanced daily probability cards use the daily maximum and say so; they are not the probability at “now.”

## Feedback and accessibility

| State | Required presentation |
|---|---|
| Initial | Search invitation and empty data regions; no made-up weather |
| Loading | Spinner/status, available cancel or new search; no frozen window |
| Ambiguous | Name/region/country choices with keyboard selection |
| No match | Inline explanation and editable search |
| Network/provider failure | Inline cause and Retry; clear whether previous results remain |
| Partial | Unavailable fields, gap markers and incomplete-forecast explanation |
| Fresh cache, Phase 2 | Cached indicator plus retrieval time |
| Stale cache, Phase 2 | Prominent age/warning; Refresh action; expired intervals not called future forecasts |
| No cache, Phase 2 | No offline data message with manual retry |

Use text labels for units, icons and status. Selection needs a focus/selected indicator beyond color. Maintain keyboard search, candidate choice, tabs, cards and unit toggle. Chart values should also be readable through labels/text detail. Tooltips are supplementary. Do not claim screen-reader support until tested.

## Responsive desktop requirements

Task 02 should validate a candidate minimum client size of 1000 × 700 logical pixels rather than treating it as an image measurement. Check 1366 × 768 and 1920 × 1080 displays, including Windows 100%, 125% and 150% scaling. At constrained sizes, retain readable controls and use vertical page scrolling/horizontal card scrolling. Keep the map before the other-cities region in reading order when stacking is necessary. Do not hide the map, remove the city cards or shrink text excessively to make everything fit without scrolling.

Theme values, precise spacing, corner radii and typography are Task 02 measurements/proposals. No invented hex color is declared an exact match in Task 01.

## Phase 2 controls

Add Listen to Weather / Stop controls in the compact action area, a working favorites menu, Refresh with cache status, and approximate-location action with an explicit consent dialog. Add feels-like/rain tiles to the secondary statistics row. Place the temperature trend in an expandable forecast-detail area without displacing the map. Sunrise/sunset belongs in selected-day detail. No microphone or account UI.

## Visual acceptance

Compare actual Windows captures against the exact approved image: shell, relative panel prominence, top-bar alignment, tab row, card proportions, blue active card, rain chart, large map and right-side city stack. Review additions separately for obstruction or loss of balance. User approval of a generic description is not evidence that the implemented GUI matches the image.
