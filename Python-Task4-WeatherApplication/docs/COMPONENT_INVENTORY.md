# SkyCast — Component inventory

**Task 02 · Contracts only; no widgets implemented**

Every component receives immutable display data plus callbacks. None knows HTTP endpoints, SQL queries or speech-engine internals. Tokens come from one theme definition during Task 04. Names below describe responsibilities, not required module names.

| Component | Inputs | States | Events / responsibility | Rendering dependencies |
|---|---|---|---|---|
| SkyCastWindow | DisplayState, theme, work-area size | Ready, closing, compact | Own layout, scroll, dialogs; close callback | CTk window/grid; controller |
| TopNavigation | Location label, current status, enabled utilities | No location, loading, ready | App menu/About, search, unit/optional utility placement | CTk frame, buttons, labels |
| LocationSearch | Query, candidates, request status | Idle, invalid, searching, candidates, failed | Submit Enter/button, select candidate, cancel; preserve Unicode/postal strings | CTk entry, button, popup list |
| ForecastTabs | Active tab, availability | Default, active, hover, focused, unavailable | Emit tab selection; preserve exact three labels | CTk buttons styled as text tabs |
| SelectedDayCard | Date, current or daily summary, icon descriptor, unit | Current, forecast, partial, loading | Selected focal card; display labeled temperature basis | CTk frame, text, Pillow/CTkImage |
| DailyForecastCard | Date, high/low, condition, selected flag | Default, hover, focused, selected, missing | Emit date selection; descriptive keyboard name | CTk button/frame composition |
| DailyForecastStrip | Seven date models, selected date | Loaded, partial, narrow | Manage chronological positions and horizontal scrolling; expand selected slot | CTk/Canvas horizontal scroll container |
| HourlyForecastStrip | Six hourly slots, date/window, unit | Loading, complete, gap, future window | Show exact instants; select hour; previous/next window only for future-date mode | CTk cell frames; horizontal scrolling |
| ChanceOfRainChart | Same six slots as hourly strip | Loading, empty, partial, zero, ready | Draw percentage scale; focusable textual values; no decorative dummy bars | Tk Canvas; text detail popup |
| GlobalWeatherMap | Map asset, resolved markers, selected ID | Empty, selected, partial weather, asset failure | Select genuine pin, expose status; optional View wide dialog | Canvas, Pillow map; projection helper |
| OtherCitiesPanel | Up to three city card models | Empty, loading, partial, ready | Coordinate card layout; optional chooser | CTk frames; controller requests |
| OtherCityCard | Location, current bundle summary, unit | Loading, ready, unavailable, cached | Select main location or Retry specific card | CTk card, image and labels |
| WeatherStatCard | Label, value?, unit, valid time/basis | Ready, unavailable, loading | Present one measurement without inventing fallback | CTk frame/labels |
| UnitToggle | Celsius/Fahrenheit enum | Active, focused | Set shared display unit; never mutate canonical measurements | CTk segmented buttons |
| WeatherStatusIndicator | Source, valid/retrieved times, cache state | Fresh download, cached, stale, updating | Describe provenance and Refresh action | CTk labels/button |
| LoadingIndicator | Request kind and active flag | Visible/hidden | Non-blocking progress; no duplicate timers | CTk progress or timed indicator |
| ErrorMessage | Safe message, scope, retry availability | Search/main/icon/city/optional-service | Explain error and offer relevant recovery; text + icon | CTk label/action; no raw exception text |
| VoiceControls, Phase 2 | Availability, playback state | Ready, speaking, stopped, unavailable, error | Listen current weather / Stop; never autoplay | CTk buttons; speech service callbacks |
| FavoritesPopup, Phase 2 | Resolved favorites, current identity | Empty, loaded, persistence failure | Select/remove; star toggles current favorite | CTk popup/list; repository service |
| TemperatureTrend, Phase 2 | Hourly series, unit, expanded flag | Collapsed, ready, gaps, unavailable | Expand/collapse; resize and label axes | Matplotlib figure owned by component |
| ApproximateLocationDialog, Phase 2 | Provider explanation, status/result | Consent, locating, confirm/correct, error | Accept/cancel before request; confirm approximate result | CTk dialog; location service |
| AttributionView | Source/license/change notices | Closed/open | Open allowlisted provider/license links via user's browser | CTk dialog and link buttons |

## Shared presentation contracts

`DisplayState` retains selected location/date/tab, unit, request generation and status. WeatherBundle supplies provider-independent domain models. Presentation-only views derive formatted strings, exact timestamps, icon descriptors, availability reasons and measurement basis; components never infer missing values from another city/date.

`HourlySlot` contains an expected instant and optional data. A missing slot therefore remains a visible gap. `DailyCardModel` distinguishes current temperature from forecast high/low. `MapMarkerModel` requires coordinates and identity, with optional weather/status fields; absent weather is not zero degrees. `CityCardModel` owns its own source/retrieval/error state.

The selected card uses the same data source as its small-card counterpart; selection must not create a second weather fetch or duplicate widget hierarchy. Resizing/repainting changes dimensions, not location/date/unit state.

## Threading, resource ownership and stale results

The application controller owns a bounded worker executor, a result queue, a monotonically increasing main-request generation and per-city request generations. Geocoding/weather/icon requests occur off the Tk thread; workers return plain data or decoded non-Tk image data. A Tk `after` queue poll applies only matching generations. The main thread creates Tk/CTk image wrappers, widgets and Matplotlib canvas updates. No worker accesses widgets.

Keep separate main-location and secondary-city request tokens. A main search does not cancel all city cards; a city Retry does not replace main-location status. Coalesce identical requests. A new query invalidates older candidates, including candidates arriving after Escape or selection.

Retain image references for the lifetime of their widget; cache bounded variants keyed by icon family and scaled display size. Reuse chart objects and update data; destroy canvases/close Matplotlib figures on component disposal. Debounce map/chart resizing by a proposed 100 ms; verify final sizes after resizing stops. Do not create a new figure or HTTP call on every configure event.

On close: set closed flag, cancel scheduled Tk polls/redraws, reject future results, stop speech through its owning worker and cancel queued work. Running network tasks obey Task 01 timeout/deadline policy. A bounded shutdown must not call Tk from a worker or hang indefinitely.

## Layout and accessibility responsibility

SkyCastWindow owns vertical scrolling; strips own horizontal scrolling. Child cards do not create their own vertical scroll zones. Tab/arrow navigation scrolls the focused item into view. Dialogs return focus to the invoking control. Each icon control has a visible or accessible label and tooltip; descriptions remain available if icons are missing. Screen-reader compatibility is a validation goal, not an assumed property of custom drawing.
