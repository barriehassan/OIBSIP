# SkyCast — Detailed UI/UX design specification

**Task 02 · 2 November 2026 · Implementation-ready design, no application code**

## Authority and baseline

The supplied `image(20261102-081659).png` (1024 × 768) is the exact approved reference and has now been visually inspected. It supersedes the missing-image caveat in the historical Task 01 report. Task 01 was published to `barriehassan/OIBSIP`, `main`, commit `4db40b7a64092b25d24a6d2b42afce8e4afdd05f`. Its requirements and architecture remain the functional basis.

This specification translates the reference into editable CustomTkinter components. It is not an alternative mockup. Approximate source measurements below describe the image; implementation dimensions are deliberate proposals in logical pixels. They are not claims of pixel-perfect reproduction.

## Reference anatomy

| Element | Approximate source rectangle (x, y, width, height) | Design significance |
|---|---|---|
| Rounded app container | 41, 61, 922, 657 | Near-black central surface; outer grey is presentation framing |
| Top navigation | 66, 82, 872, 36 | Compact icons/location, centered search, right utilities |
| Tab row | 66, 142, 648, 29 | Understated labels; no sidebar |
| Daily cards | 66, 189, 648, 163 | One 164-wide featured card, six roughly 68-wide cards, 13–14 gaps |
| Rain region | 739, 151, 198, 200 | Narrow chart aligned to upper content |
| Map panel | 66, 419, 649, 273 | Large landscape map, rounded edges, subtle land shapes |
| Other cities | 741, 419, 196, 274 | Three stacked compact cards |

Preserve the approximate 3.3:1 main-to-right-column ratio and the selected-card-to-small-card width ratio of 2.4:1. Scale space before text; do not enlarge the screenshot into an unresponsive background.

The screenshot contains inconsistent example geography (such as “Seattle, Australia”) and qualitative rain-axis words. These are not data rules. Show actual resolved location names and a percentage axis. Keep their visual positions. The screenshot's air-quality tab, avatar, theme controls, map promotion and zoom controls are not authorized features; replace their roles only with useful approved actions or omit them as detailed below.

## Visual tokens

Flat-area mode sampling with Pillow produced the sampled colors below. Compression/antialiasing and the selected card's subtle variations mean a sample is representative, not a universal pixel value. Production tokens use flat fills and minimal borders.

| Token | Value | Origin / use |
|---|---|---|
| `surface.app` | `#111015` | Sampled shell |
| `surface.panel` | `#1B1B1D` | Sampled map/card flat regions |
| `surface.search` | `#1E1E1E` | Sampled search background |
| `surface.hover` | `#28282D` | Proposed interaction state |
| `surface.selected` | `#BBD7EC` | Sampled selected-card patch |
| `text.primary` | `#F5F5F7` | Proposed accessible near-white |
| `text.secondary` | `#B0AFBA` | Proposed readable grey; brighter than tiny source labels |
| `text.on_selected` | `#14151B` | Proposed dark selected-card text |
| `text.on_selected_secondary` | `#353B45` | Proposed darker supporting text |
| `border.subtle` | `#34343C` | Decorative separators, not sole focus indicator |
| `accent.blue` | `#92C6EE` | Bars/focus accents |
| `accent.lavender` | `#C6B6EA` | Optional restrained utility accent |
| `status.error` | `#FFB4AB` | Text + icon + explanatory label |
| `status.warning` | `#F4D28B` | Cached/stale warning text |
| `focus.on_dark` | `#BBD7EC` | 2 px visible focus ring |
| `focus.on_selected` | `#14151B` | Dark ring on blue card |

Do not use low-opacity secondary text for meaningful labels. Selected card and primary action use dark text over light blue. Error is not conveyed by red alone. Contrast results are recorded in UI_ACCEPTANCE_CHECKLIST.md; runtime text rendering remains a manual check.

### Typography

Primary family: Segoe UI; fall back to Arial, then TkDefaultFont if unavailable. Use weight, size and spacing for hierarchy; do not depend on an unidentified font from the source image. Sizes below are logical pixel targets, not typographic points. Task 04 must map them consistently to CustomTkinter font/scaling behavior; Canvas and Tk font settings must use the same scale conversion.

| Style | Size / weight | Use |
|---|---|---|
| Brand | 15 bold | SkyCast; NOMOLI FORGE in About/header tooltip |
| Section | 18 semibold/bold | Global Map, Other Large Cities, Chance of Rain |
| Navigation | 16 regular; active semibold | Three forecast tabs |
| Featured temperature | 48 bold | Selected-card headline |
| Daily temperature | 28 medium | Small daily cards |
| Stat value | 22 semibold | Compact statistics |
| Body | 14 regular | Location/city/condition |
| Label | 12 regular | Dates, units, timestamps, secondary value |
| Hourly temperature | 18 semibold | Six-hour strip |

Do not shrink meaningful text below 12 logical pixels. On source-matching compact cards, use fewer labeled lines or accessible detail rather than recreating unreadably small source text.

### Geometry and reusable states

Spacing scale: 4, 8, 12, 16, 24, 32. Shell radius 32; forecast radius 24; map 24; city cards 22; stats 16; search pill 24. Shell horizontal padding 32; column gap 32. Target controls 40 high minimum; search 48 high; small icon visuals 18–24 within at least 40 × 40 targets. Standard inner padding 16; small daily-card padding 10–12.

Hover changes surface only, without resizing. Active tabs gain weight and a 2 px underline. Keyboard focus adds a distinct 2 px ring with 2 px inset; selected cards also expose a Selected label/accessibility name. Disabled controls have an explanation and cannot invoke an action; do not make essential results unreadable. Scrollbars use a 10 px track, visible thumb and keyboard/trackpad access. Avoid animated gradients and looping decoration; loading indicators stop when work completes.

## Layout at 1440 × 900 client size

All measurements exclude native window chrome. Use the operating system title bar with “NOMOLI FORGE — SkyCast”; no frameless draggable-window implementation is required. A logical shell width of 1360 is centered with 40 px side gutters at this reference size. At widths above 1600, cap shell width at 1520 and center it. A header of 96 px remains visible; the content below it scrolls vertically.

| Region | Position / size in content canvas | Rule |
|---|---|---|
| Header A | x72, y24, w1296, h48 | Three-column grid: 290 / 1fr / 256; 24 gaps |
| Tabs B | x72, y112, w968, h40 | Today / Tomorrow / Next 7 Days; optional approved forecast-detail control at right |
| Daily cards C | x72, y168, w968, h220 | Selected 242, six cards 101, six gaps 20 |
| Rain D | x1072, y112, w296, h276 | Heading above plot; chart baseline aligns with card row |
| Stats G | x72, y404, w968, h72 | Four cards 230 wide with 16 gaps |
| Hourly detail H | x72, y492, w968, h104 | Six-hour cells: 148 each, five gaps 16; date/time and value labels |
| Lower headings | x72 and x1072, y620, h32 | Global Map / Other Large Cities |
| Map E | x72, y664, w968, h408 | Keep large map; overflow below viewport is intentional |
| Cities F | x1072, y664, w296, h408 | Three cards 128 high, 12 gaps |
| Attribution/footer | y1088, h40 | Provider links and retrieval/cache status |

These are document-canvas coordinates. The 900-high window shows the header, forecasts, statistics, hourly strip and upper map; scroll reaches the complete map. Do not shrink the map to cram additional mandatory information into the screenshot's original height. The right-hand area between rain and cities remains breathing room rather than another feature panel.

With Phase 1 only, humidity and wind are the two populated statistics tiles. The two later tiles are omitted and that pair is centered/aligned within the same row; do not show inactive pretend values. The full Phase 2 row holds humidity, wind, feels-like and rain probability. Core values may also appear in the selected current card as compact metadata.

### Top bar

Left: 40 px application/menu button (opens About and provider notices), small SkyCast wordmark and location icon/name; tooltip or expandable detail exposes full region/country when truncated. No notification bell without a notification feature.

Center: search field and visible Get Weather button within the search group. At default width the group is roughly 702 px. Right: shared °C/°F segmented control; Phase 2 star/favorites and Use my approximate location actions. If width is constrained, move optional utilities into a labeled More menu. No authentication/avatar or fake light-theme switch. Favorites star status and opening the favorites list are separate affordances (toggle star; list in menu).

The candidate list is an anchored, keyboard-accessible popup at the search group's width, maximum height 260, row height at least 48; show city, region and country on two lines. Escape dismisses it and restores search focus. Do not steal focus when a late result arrives.

## Cards, tabs and data semantics

Default tab is **Today**, although the image shows Next 7 days active. Preserve labels **Today | Tomorrow | Next 7 Days**. The seven-day strip stays visible across tabs. Its dates are today through +6 according to Task 01; “seven upcoming” does not change this to tomorrow through +7. Tomorrow selects +1. Clicking another date activates Next 7 Days. The selected card expands in its chronological slot; keep order unchanged and scroll the selected slot into view when necessary.

Selected-card header: local day/date plus Now/time only for today; future cards say Forecast, not the current clock. Today shows current temperature with secondary equivalent unit, condition, humidity and wind; future selection shows labeled high/low and day condition instead. Show source valid time in detail/status; retrieval time remains distinct. Day/night imagery for current/hourly follows data; daily forecast imagery is a daytime summary.

Small cards contain day/date, graphical icon (48), high temperature (28 text) and a readable 12 px low label; all values carry unit context from the shared toggle and panel label. No arbitrary single temperature is unlabeled. The featured illustration is up to 88 × 88, positioned beside the headline rather than behind text.

Current conditions remain available even after a future day is selected: the fixed header status line identifies current temperature/condition for the selected location, and the Today tab returns to the full current detail. Never move the current reading under a future-date label.

### Six-hour strip and optional chart

Today always shows H, directly below G. Each cell has local date/time (12), icon (32), temperature (18), optional probability (12). Cells share one coherent time window with rain bars. Next six hours may cross midnight; show a date change. Missing points keep a slot labeled Unavailable; never substitute three-hour intervals.

Tomorrow and selected future dates reuse H as a six-hour window into that day's hourly data. Start at 06:00 local when that instant exists, otherwise the first available hour after it; Previous/Next window controls move six actual forecast instants and stop at the day boundary. Label the full date/window. A Today-specific next-six-hours mode is not represented as tomorrow's first six hours. Repeated DST times display offsets.

Phase 2 temperature trend is a collapsed detail expansion below H, height 160 plus 16 gap. Expanding it shifts map/cities down together; it never replaces the map. Plot real hourly data with gaps, current display unit and textual values. Voice controls (Listen to Weather / Stop) occupy an action line inside this detail region; they summarize Today/current conditions only. Future-date views label the action “Listen to current weather” to remove ambiguity.

### Rain and statistics

Chance of Rain has six slim light-blue bars on a 0–100% axis with three guides, not the screenshot's Rainy/Sunny/Heavy text. Plot matches H's time window. Hover/focus exposes exact percentage, date/time and context; include a text summary/list for non-pointer access. Zero probability has a baseline marker and “0%”; missing probability has a gap and “Unavailable.” Loading does not invent bars.

Statistic labels explicitly identify their basis: Today humidity/wind/feels-like are current values, Rain is next forecast hour probability; future views show selected-hour values from the detail cursor (initially its first available hour), with a shared “At HH:mm, date” caption. Do not mix current humidity and future wind under one unlabeled date. Daily maximum probability is shown only when labeled Daily maximum.

### Map and other cities

Retain E's dark landscape map and small circular weather pins. Use the equirectangular local-map decision in ASSET_PLAN.md. A pin is a location, not evidence of a live reading; weather badges require a fetched bundle. Selected pin has a ring plus location label. Caption: “Location overview · weather only for fetched places.” Functional controls are Select location (via search), center selected pin when a transform exists, and View wide; omit zoom/layers until implemented. View wide opens a resizable map-only dialog using existing map data, with Escape/Close and restored focus; it makes no new weather request.

Do not reproduce the white marketing card or its satellite image/Get started call-to-action: it is not a SkyCast feature and would obscure the map. On first launch, a small unobtrusive text hint can say “Search a city to place a marker.”

City cards: country/region (12), city (16), short condition (12), icon (48) and current temperature (24), plus retrieval/status text. Proposed suggestions Freetown, London and Beijing are search seeds only; resolve them before use and fetch values. Three visible cards maximum; Show all opens a secondary-city chooser/list only when implemented. A failed card has Retry without hiding successful cards. Clicking a loaded city selects it as the main location; maintain the global unit.

## Responsive rules

| Client width | Rule |
|---|---|
| ≥1280 | Two columns; 32 outer padding; 32 gap; right column 23% of content, minimum 264; left gets remainder |
| 1100–1279 | Two columns retained; 24 padding/gap; right 248; forecast row horizontally scrolls rather than shrinking typography |
| 1024–1099 | Minimum supported desktop: stacked header (search full width below identity/utilities); main content remains two columns with 232-right; horizontal forecast/hourly scrolling and vertical page scrolling |
| Below 1024 | Do not promise support; enforce a practical minimum client width where work area allows, otherwise single-column fallback with forecast/rain, stats/hourly, map/cities reading order |

Min target client height 700; default 1440 × 900 only when the available work area supports it. Clamp initial size to the usable screen excluding taskbar/chrome; never open controls off-screen. On a 1366 × 768 screen, the client will be smaller than screen dimensions. At high DPI the available logical width may require the fallback. This is still a desktop application, not a mobile redesign.

In narrow two-column layouts, keep selected card at least 220 and other cards at least 88 with 12 gaps. Stats become 2 × 2 at left-column width under 800, adding 88 px to document height and shifting lower content down. Hourly cells retain 140 minimum width. The whole page scrolls vertically; inner strips scroll horizontally only, avoiding nested vertical-scroll traps. Recalculate positions from grid constraints, not absolute widget placements.

## Accessibility and implementation boundaries

Tab order: app menu, search, Get Weather, candidate list when open, unit toggle, optional utilities, forecast tabs, daily strip, hourly strip, detail actions, map controls, city cards, attribution. Arrow keys move within tabs/cards; Enter/Space selects; Escape closes popups/dialogs. Focus is retained across refetch and resizing. Offer textual weather descriptions and exact chart values, label every icon button, and ensure errors include explanatory text/action.

Standard CustomTkinter: shell, text, fields, tabs, buttons, cards and scrollable page. Canvas: precise chart bars, map pins/hit targets and custom focus decoration as necessary. Pillow: decoded/resized licensed weather graphics and local map raster. Matplotlib is reserved for the optional temperature chart. No network/SQL/speech within widgets. Follow the controller/worker contracts in COMPONENT_INVENTORY.md and INTERACTION_FLOWS.md.

The original soft illustrations and unspecified typeface cannot be guaranteed with official icons and system fonts. Functional/readable differences are explicit; actual Windows captures must be inspected before any parity claim. No application is implemented by this document.
