"""User-triggered, local-only speech. An isolated process owns the engine and COM."""

import multiprocessing as mp
import sys
import time
from queue import Empty
from zoneinfo import ZoneInfo
from app.ui.presentation import temperature, location_label


def speech_text(bundle, unit="°C", cached=False):
    if bundle is None:
        return ""
    c = bundle.current
    suffix = "degrees Fahrenheit" if unit == "°F" else "degrees Celsius"

    def degrees(value):
        return (
            "unavailable"
            if value is None
            else temperature(value, unit).replace(unit, " " + suffix)
        )

    stamp = bundle.retrieved_at.astimezone(ZoneInfo(bundle.timezone)).strftime(
        "%d %B at %H:%M %Z"
    )
    intro = (
        f"Last retrieved conditions for {location_label(bundle.location)}, downloaded {stamp}."
        if cached
        else f"Weather for {location_label(bundle.location)}."
    )
    parts = [
        intro,
        f"The condition is {c.description}.",
        f"Temperature is {degrees(c.temperature_c)}.",
    ]
    if c.feels_like_c is not None:
        parts.append(f"It feels like {degrees(c.feels_like_c)}.")
    if c.humidity_percent is not None:
        parts.append(f"Humidity is {c.humidity_percent:g} percent.")
    if c.wind_speed_kmh is not None:
        parts.append(f"Wind speed is {c.wind_speed_kmh:g} kilometres per hour.")
    return " ".join(parts)


def run_engine(text, stop, results, factory, clock=time.monotonic, sleep=time.sleep):
    engine = None
    loop = False
    try:
        try:
            engine = factory()
        except Exception:
            results.put("Unavailable")
            return
        done = []
        errors = []
        engine.connect("finished-utterance", lambda name, completed: done.append(True))
        engine.connect("error", lambda name, exception: errors.append(True))
        if stop.is_set():
            return
        engine.say(text)
        engine.startLoop(False)
        loop = True
        results.put("Speaking")
        started = clock()
        while not stop.is_set() and not done and not errors:
            engine.iterate()  # SAPI5 implementation pumps COM messages on this owner thread.
            if clock() - started > 120:
                raise RuntimeError("Speech timeout")
            sleep(0.02)
        if errors:
            raise RuntimeError("Speech engine failure")
        results.put("Listen")
    except Exception:
        results.put("Error")
    finally:
        if engine:
            try:
                engine.stop()
            except Exception:
                pass
            if loop:
                try:
                    engine.endLoop()
                except RuntimeError:
                    pass


def _speech_process(text, stop, results):
    # Spawned child main thread: no Tk imports/objects, no shared engine or COM object.
    try:
        import pythoncom

        pythoncom.CoInitialize()
        try:
            import pyttsx3

            run_engine(text, stop, results, lambda: pyttsx3.init("sapi5"))
        finally:
            pythoncom.CoUninitialize()
    except Exception:
        results.put("Unavailable")


class VoiceService:
    def __init__(
        self, *, context=None, supported=None, clock=time.monotonic, worker=None
    ):
        self.context = context or mp.get_context("spawn")
        self.worker = worker or _speech_process
        self.supported = sys.platform == "win32" if supported is None else supported
        self.clock = clock
        self.process = None
        self.events = None
        self.stop_event = None
        self.status = "Listen" if self.supported else "Unavailable"
        self.stopping_at = None
        self.started_at = None
        self.closed = False

    @property
    def active(self):
        return self.process is not None

    def start(self, text):
        if self.closed or not text or self.active:
            return False
        if not self.supported:
            self.status = "Unavailable"
            return False
        try:
            self.events = self.context.Queue()
            self.stop_event = self.context.Event()
            self.process = self.context.Process(
                target=self.worker,
                args=(text, self.stop_event, self.events),
                daemon=True,
            )
            self.process.start()
            self.status = "Starting"
            self.started_at = self.clock()
            return True
        except Exception:
            self._release()
            self.status = "Error"
            return False

    def stop(self):
        if self.process and self.stopping_at is None:
            self.stop_event.set()
            self.stopping_at = self.clock()
            self.status = "Stopping"

    def poll(self):
        before = self.status
        if not self.process:
            return False
        while True:
            try:
                status = self.events.get_nowait()
                if self.stopping_at is None:
                    self.status = status
            except Empty:
                break
        if (
            self.stopping_at is not None
            and self.process.is_alive()
            and self.clock() - self.stopping_at > 0.5
        ):
            self.process.terminate()
        if self.started_at is not None and self.clock() - self.started_at > 130:
            self.process.terminate()
            self.status = "Error"
        if not self.process.is_alive():
            # Drain final child notifications after its feeder has finished.
            try:
                while True:
                    status = self.events.get(timeout=0.01)
                    if self.stopping_at is None:
                        self.status = status
            except Empty:
                pass
            if self.stopping_at is not None or self.status not in (
                "Error",
                "Unavailable",
            ):
                self.status = (
                    "Listen"
                    if self.stopping_at is not None or self.process.exitcode == 0
                    else "Error"
                )
            self.process.join(timeout=0)
            self._release()
        return before != self.status

    def _release(self):
        if self.events:
            self.events.close()
            self.events.cancel_join_thread()
        self.process = None
        self.events = None
        self.stop_event = None
        self.stopping_at = None
        self.started_at = None

    def close(self):
        self.closed = True
        if self.process:
            self.stop()
            self.process.join(timeout=0.25)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=0.2)
            if self.process.is_alive():
                self.process.kill()
                self.process.join(timeout=0.1)
            self._release()
