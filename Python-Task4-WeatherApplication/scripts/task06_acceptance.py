"""Explicit live Linux GUI acceptance; temporary data, no speech/IP request.

Run from a desktop: python scripts/task06_acceptance.py --output <directory>
Makes two city searches, one postal search and at most three weather fetches.
"""
import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PIL import ImageGrab
from app.ui.controller import Controller, Backend
from app.ui.window import SkyCastWindow
from app.storage.local import LocalStore
from app.core.exceptions import WeatherNetworkError, WeatherTimeoutError
from app.core.forecast_processor import next_six_hours, seven_days


def run(output):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    results=[]
    with tempfile.TemporaryDirectory() as tmp:
        store=LocalStore(Path(tmp)/'acceptance.sqlite3')
        backend=Backend()
        app=SkyCastWindow(Controller(backend,store=store),store=store,remote_icons=False)
        errors=[]
        app.report_callback_exception=lambda *args:errors.append(str(args))
        def settle(seconds=.4):
            end=time.monotonic()+seconds
            while time.monotonic()<end:
                app.update();time.sleep(.02)
        def finish():
            deadline=time.monotonic()+45
            while app.controller.state.loading and time.monotonic()<deadline:
                settle(.05)
            settle()
            assert not app.controller.state.loading,'Request did not finish'
        def capture(name):
            settle()
            ImageGrab.grab(bbox=(app.winfo_rootx(),app.winfo_rooty(),
                app.winfo_rootx()+app.winfo_width(),app.winfo_rooty()+app.winfo_height())).save(output/f'{name}.png')
        def search(query,expected_id):
            app.entry.delete(0,'end');app.entry.insert(0,query);app.search();finish()
            state=app.controller.state
            if state.candidates:
                chosen=next(x for x in state.candidates if x.provider_id==expected_id)
                app.choose(chosen);finish()
            assert state.bundle and state.bundle.location.provider_id==expected_id,(query,state.status)
            b=state.bundle;now=datetime.now(timezone.utc)
            hours=next_six_hours(b,now);days=seven_days(b,now)
            assert hours.complete and sum(x is not None for x in days.entries)>=5
            results.append({'query':query,'location':b.location.name,'country':b.location.country,
                'timezone':b.timezone,'retrieved_at':b.retrieved_at.isoformat(),
                'upcoming_hour_count':len(hours.entries),'daily_count':len(b.daily_forecasts),
                'weather_code':b.current.weather_code})
            return b
        try:
            app.geometry('1440x900+0+0');settle()
            london=search('London, United Kingdom',2643743)
            app.add_city();app.enhancements.save_favorite()
            freetown=search('Freetown, Sierra Leone',2409306)
            app.add_city();app.enhancements.save_favorite()
            app.choose(london.location);finish()
            assert app.controller.state.cache_source=='recent cache'
            capture('SkyCast_Task06_Dashboard')
            app.unit_changed('°F');app.tab_changed('Tomorrow');capture('SkyCast_Task06_Tomorrow_Fahrenheit')
            app.tab_changed('Next 7 Days');app.select_day(app.controller.state.selected_date+timedelta(days=1));capture('SkyCast_Task06_Seven_Days')
            app.tab_changed('Today');app.unit_changed('°C')
            app.toggle_details();settle();app.page._parent_canvas.yview_moveto(1);capture('SkyCast_Task06_Details')
            app.enhancements.show_favorites();settle();app.page._parent_canvas.yview_moveto(1);capture('SkyCast_Task06_Favorites')
            app.enhancements.favorite_list.pack_forget();app.enhancements.request_location();settle();capture('SkyCast_Task06_Location_Consent')
            app.enhancements.consent_panel.pack_forget()
            class Offline:
                def weather(self,location):raise WeatherNetworkError('Simulated connection loss')
            app.controller.backend=Offline();app.refresh();finish()
            assert app.controller.state.offline
            app.toggle_details();app.page._parent_canvas.yview_moveto(0);capture('SkyCast_Task06_Offline')
            app.refresh_city(london.location);settle(1);assert app.controller.state.cities[london.location].error
            capture('SkyCast_Task06_Cached_City')
            app.controller.backend=backend;app.refresh();finish()
            assert not app.controller.state.offline and app.controller.state.cache_source=='network'
            for w,h in [(1366,768),(1024,700)]:
                app.geometry(f'{w}x{h}+0+0');settle();capture(f'SkyCast_Task06_{w}x{h}')
            app.controller.search('');app.render_status();assert app.controller.state.failed
            class Timeout:
                def search(self,query):raise WeatherTimeoutError('Simulated timeout. Please retry.')
            app.controller.backend=Timeout();app.controller.search('Test timeout');finish()
            assert app.controller.state.failed and not app.controller.state.loading
            postal=backend.search('10115')
            assert postal
            results.append({'postal_query':'10115','matches':len(postal),'first_country':postal[0].country,'first_city':postal[0].name})
            assert not errors,errors
        finally:app.close()
        store=LocalStore(Path(tmp)/'acceptance.sqlite3')
        assert len(store.favorites()[0])==2
        app=SkyCastWindow(Controller(backend,store=store),store=store,remote_icons=False)
        try:
            app.geometry('1440x900+0+0');app.choose(store.favorites()[0][0]);finish()
            assert app.controller.state.bundle and app.controller.state.cache_source=='recent cache'
        finally:app.close()
    result={'captured_at':datetime.now(timezone.utc).isoformat(),'platform':'Linux / Python 3.12 / Tk 8.6',
        'live_results':results,'workflow':'search, selection, C/F, tabs, day selection, map/city rendering, favorite save/reopen, cache reuse, simulated offline and timeout, live recovery, restart',
        'not_executed':['Windows speech/audio','real public-IP lookup','native Windows DPI/accessibility'],
        'icons':'Original fallback icons; no hosted-icon requests in this acceptance run',
        'callback_errors':errors}
    (output/'acceptance.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);run(parser.parse_args().output)
