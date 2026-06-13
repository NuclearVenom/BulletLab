"""Tests for bulletlab.telemetry."""

import time
import pytest
from bulletlab.telemetry import TelemetryManager, TelemetryChannel


class TestTelemetryChannel:
    def test_channel_creation(self):
        ch = TelemetryChannel("Speed", lambda: 5.0)
        assert ch.name == "Speed"
        assert ch.latest is None

    def test_poll_returns_value(self):
        ch = TelemetryChannel("x", lambda: 42.0)
        val = ch.poll(t=0.0)
        assert val == pytest.approx(42.0)

    def test_poll_updates_latest(self):
        value = [0.0]
        ch = TelemetryChannel("y", lambda: value[0])
        value[0] = 3.14
        ch.poll()
        assert ch.latest == pytest.approx(3.14)

    def test_history_accumulates(self):
        counter = [0]
        def source():
            counter[0] += 1
            return float(counter[0])

        ch = TelemetryChannel("count", source, history_len=100)
        for t in range(5):
            ch.poll(t=float(t))
        assert len(ch.history) == 5

    def test_history_maxlen(self):
        ch = TelemetryChannel("x", lambda: 1.0, history_len=3)
        for i in range(10):
            ch.poll(t=float(i))
        assert len(ch.history) == 3

    def test_history_timestamps(self):
        ch = TelemetryChannel("x", lambda: 1.0)
        ch.poll(t=0.5)
        ch.poll(t=1.0)
        ts = ch.timestamps
        assert ts[0] == pytest.approx(0.5)
        assert ts[1] == pytest.approx(1.0)

    def test_values_list(self):
        counter = [0]
        ch = TelemetryChannel("v", lambda: float(counter[0]))
        for i in range(3):
            counter[0] = i
            ch.poll(t=float(i))
        assert ch.values == [0.0, 1.0, 2.0]

    def test_clear(self):
        ch = TelemetryChannel("x", lambda: 1.0)
        ch.poll()
        ch.clear()
        assert len(ch.history) == 0
        assert ch.latest is None

    def test_unit_stored(self):
        ch = TelemetryChannel("speed", lambda: 0.0, unit="m/s")
        assert ch.unit == "m/s"

    def test_exception_in_source_returns_nan(self):
        def bad_source():
            raise ValueError("oops")

        ch = TelemetryChannel("bad", bad_source)
        val = ch.poll()
        import math
        assert math.isnan(val)


class TestTelemetryManager:
    def test_watch_creates_channel(self):
        tm = TelemetryManager()
        ch = tm.watch("Speed", lambda: 5.0)
        assert isinstance(ch, TelemetryChannel)
        assert "Speed" in tm

    def test_update_returns_dict(self):
        tm = TelemetryManager()
        tm.watch("x", lambda: 1.0)
        result = tm.update(t=0.0)
        assert isinstance(result, dict)
        assert "x" in result

    def test_get_returns_latest(self):
        val = [10.0]
        tm = TelemetryManager()
        tm.watch("v", lambda: val[0])
        tm.update(t=0.0)
        assert tm.get("v") == pytest.approx(10.0)

    def test_get_missing_returns_default(self):
        tm = TelemetryManager()
        assert tm.get("nonexistent", default=-99) == -99

    def test_snapshot(self):
        tm = TelemetryManager()
        tm.watch("a", lambda: 1.0)
        tm.watch("b", lambda: 2.0)
        tm.update()
        snap = tm.snapshot()
        assert "a" in snap
        assert "b" in snap
        assert snap["a"] == pytest.approx(1.0)
        assert snap["b"] == pytest.approx(2.0)

    def test_history(self):
        tm = TelemetryManager()
        tm.watch("x", lambda: 5.0)
        for i in range(3):
            tm.update(t=float(i))
        hist = tm.history("x")
        assert len(hist) == 3

    def test_values_array(self):
        tm = TelemetryManager()
        tm.watch("z", lambda: 3.0)
        tm.update()
        tm.update()
        vals = tm.values_array("z")
        assert vals == [3.0, 3.0]

    def test_unwatch(self):
        tm = TelemetryManager()
        tm.watch("x", lambda: 1.0)
        tm.unwatch("x")
        assert "x" not in tm

    def test_len(self):
        tm = TelemetryManager()
        tm.watch("a", lambda: 1.0)
        tm.watch("b", lambda: 2.0)
        assert len(tm) == 2

    def test_channel_names(self):
        tm = TelemetryManager()
        tm.watch("alpha", lambda: 0.0)
        tm.watch("beta", lambda: 0.0)
        assert "alpha" in tm.channel_names
        assert "beta" in tm.channel_names

    def test_clear_history(self):
        tm = TelemetryManager()
        tm.watch("x", lambda: 1.0)
        for _ in range(5):
            tm.update()
        tm.clear_history()
        assert tm.values_array("x") == []

    def test_clear_all(self):
        tm = TelemetryManager()
        tm.watch("x", lambda: 1.0)
        tm.clear_all()
        assert len(tm) == 0

    def test_multiple_updates_accumulate(self):
        tm = TelemetryManager()
        counter = [0]
        tm.watch("n", lambda: float(counter[0]))
        for i in range(10):
            counter[0] = i
            tm.update(t=float(i))
        assert len(tm.history("n")) == 10
