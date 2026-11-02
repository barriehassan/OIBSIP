from queue import Queue
from threading import Event
from types import SimpleNamespace
from dataclasses import replace
import json
import requests
import pytest
from app.services.voice_service import VoiceService, run_engine
from app.services.ip_location_service import (
    IpLocationService,
    normalize,
    FIELDS,
    CONSENT,
)
from app.core.exceptions import (
    LocationValidationError,
    WeatherProviderError,
    WeatherNetworkError,
)
from app.ui.controller import Controller
from test_ui_controller import Workers, Backend


class Events(Queue):
    def close(self):
        pass

    def cancel_join_thread(self):
        pass


class Process:
    def __init__(self, **kwargs):
        self.alive = False
        self.exitcode = 0
        self.kwargs = kwargs

    def start(self):
        self.alive = True

    def is_alive(self):
        return self.alive

    def terminate(self):
        self.alive = False
        self.exitcode = -15

    def kill(self):
        self.alive = False

    def join(self, timeout):
        pass


class Context:
    Queue = Events
    Event = Event
    Process = Process


def test_voice_start_stop_no_overlap_cleanup():
    clock = [0]
    service = VoiceService(context=Context(), supported=True, clock=lambda: clock[0])
    assert not service.active
    assert service.start("actual weather")
    process = service.process
    assert not service.start("second") and service.process is process
    service.events.put("Speaking")
    service.poll()
    assert service.status == "Speaking"
    service.stop()
    assert service.stop_event.is_set()
    clock[0] = 1
    service.poll()
    assert not service.active and service.status == "Listen"
    service.start("third")
    process = service.process
    service.close()
    assert (
        not process.is_alive()
        and not service.active
        and not service.start("after close")
    )


@pytest.mark.parametrize("status", ["Unavailable", "Error"])
def test_voice_process_failures(status):
    service = VoiceService(context=Context(), supported=True)
    service.start("weather")
    service.events.put(status)
    service.process.alive = False
    service.poll()
    assert service.status == status and not service.active


def test_unsupported_and_empty_do_not_start():
    service = VoiceService(context=Context(), supported=False)
    assert not service.start("weather") and service.status == "Unavailable"
    assert not service.start("") and not service.active


class Engine:
    def __init__(self, stop=None):
        self.callbacks = {}
        self.stopped = False
        self.ended = False
        self.stop_event = stop
        self.text = ""
        self.loop = None

    def connect(self, name, cb):
        self.callbacks[name] = cb

    def say(self, text):
        self.text = text

    def startLoop(self, internal):
        self.loop = internal

    def iterate(self):
        if self.stop_event:
            self.stop_event.set()
        else:
            self.callbacks["finished-utterance"]("weather", True)

    def stop(self):
        self.stopped = True

    def endLoop(self):
        self.ended = True


@pytest.mark.parametrize("cancel", [False, True])
def test_engine_owner_loop_stop_cleanup(cancel):
    stop = Event()
    events = Queue()
    engine = Engine(stop if cancel else None)
    run_engine("weather text", stop, events, lambda: engine, sleep=lambda _: None)
    assert engine.text == "weather text" and engine.loop is False
    assert engine.stopped and engine.ended
    assert events.get() == "Speaking" and events.get() == "Listen"


def test_engine_initialization_failure():
    events = Queue()

    def fail():
        raise RuntimeError()

    run_engine("weather", Event(), events, fail)
    assert events.get() == "Unavailable"


def test_engine_runtime_failure_cleans_up():
    events = Queue()
    engine = Engine()

    def fail():
        raise RuntimeError()

    engine.iterate = fail
    run_engine("weather", Event(), events, lambda: engine)
    assert events.get() == "Speaking" and events.get() == "Error"
    assert engine.stopped and engine.ended


VALID = {
    "success": True,
    "city": "Freetown",
    "region": "Western Area",
    "country": "Sierra Leone",
    "country_code": "SL",
    "latitude": 8.48,
    "longitude": -13.23,
    "timezone": {"id": "Africa/Freetown"},
}


def test_ip_normalization_discards_ip_and_stable_identity():
    loc = normalize({**VALID, "ip": "192.0.2.1", "connection": {"private": "unused"}})
    assert loc.name == "Freetown" and loc.provider_id < 0 and not hasattr(loc, "ip")
    assert normalize(VALID) == loc


@pytest.mark.parametrize(
    "changes",
    [
        {"city": ""},
        {"city": None},
        {"latitude": 91},
        {"longitude": -181},
        {"latitude": True},
        {"latitude": float("nan")},
        {"timezone": {"id": "wrong/zone"}},
        {"success": False},
        {"country_code": "XYZ"},
    ],
)
def test_invalid_ip_results(changes):
    with pytest.raises(LocationValidationError):
        normalize({**VALID, **changes})


def test_country_only_and_ambiguous_results():
    with pytest.raises(LocationValidationError):
        normalize({"success": True, "country": "Sierra Leone"})
    with pytest.raises(LocationValidationError):
        normalize([VALID, VALID])


class Response:
    def __init__(self, payload=VALID, status=200):
        self.payload = payload
        self.status_code = status
        self.headers = {}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def iter_content(self, size):
        yield json.dumps(self.payload).encode()


class Session:
    def __init__(self, response=None, error=None):
        self.response = response or Response()
        self.error = error
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def get(self, url, **kw):
        self.calls.append((url, kw))
        if self.error:
            raise self.error
        return self.response


def test_consent_and_bounded_https():
    session = Session()
    service = IpLocationService(lambda: session)
    assert not session.calls
    with pytest.raises(LocationValidationError):
        service.detect()
    assert not session.calls
    assert service.detect(consent=True).name == "Freetown"
    url, args = session.calls[0]
    assert url.startswith("https://") and args["allow_redirects"] is False
    assert args["timeout"] == (3, 6) and "ip" not in args["params"]["fields"].split(",")
    with pytest.raises(WeatherProviderError):
        service.detect(consent=True)
    assert len(session.calls) == 1
    assert "VPNs" in CONSENT and "manual" in CONSENT


@pytest.mark.parametrize("error", [requests.Timeout(), requests.ConnectionError()])
def test_ip_timeout_and_failure(error):
    service = IpLocationService(lambda: Session(error=error))
    with pytest.raises(WeatherNetworkError):
        service.detect(consent=True)


@pytest.mark.parametrize("status", [301, 403, 429, 500])
def test_ip_http_failures(status):
    service = IpLocationService(lambda: Session(Response(status=status)))
    with pytest.raises(WeatherProviderError):
        service.detect(consent=True)


def test_controller_detection_requires_confirm_and_obsolete_results_discarded(location):
    workers = Workers()
    service = SimpleNamespace(detect=lambda **kw: location)
    c = Controller(Backend(), workers, ip_service=service)
    assert not workers.pending and not c.detect_location()
    c.detect_location(consent=True)
    assert len(workers.pending) == 1
    workers.finish("main", location)
    c.drain()
    assert (
        c.state.approximate == location
        and c.state.bundle is None
        and not workers.pending
    )
    c.detect_location(consent=True)
    old = workers.pending["main"][0]
    c.search("Paris")
    workers.results.put(("main", old, location, None))
    c.drain()
    assert c.state.approximate is None and c.state.query == "Paris"


def silent_process(text, stop, events):
    events.put("Speaking")
    stop.wait(3)
    events.put("Listen")


def test_real_spawn_lifecycle_without_audio():
    import time

    service = VoiceService(supported=True, worker=silent_process)
    assert service.start("mock text; no audio engine")
    process = service.process
    deadline = time.monotonic() + 3
    while service.status == "Starting" and time.monotonic() < deadline:
        time.sleep(0.02)
        service.poll()
    assert service.status == "Speaking"
    service.close()
    assert not process.is_alive() and not service.active
