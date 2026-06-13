"""Tests for bulletlab.plotting.LivePlot (headless/mocked)."""

import pytest


class TestLivePlotConstruction:
    def test_construct_without_error(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot(title="Test", max_points=100)
        assert plot is not None

    def test_watch_registers_series(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        plot.watch("Speed", lambda: 5.0, color="#00ff00")
        assert "Speed" in plot.series_names

    def test_watch_returns_self(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        result = plot.watch("x", lambda: 1.0)
        assert result is plot

    def test_not_running_before_start(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        assert not plot.is_running

    def test_not_paused_by_default(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        assert not plot.is_paused

    def test_series_names_empty_initially(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        assert plot.series_names == []

    def test_multiple_series(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        plot.watch("a", lambda: 1.0)
        plot.watch("b", lambda: 2.0)
        plot.watch("c", lambda: 3.0)
        assert len(plot.series_names) == 3


class TestLivePlotHeadlessUpdate:
    def test_update_when_not_running_does_not_raise(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        plot.watch("x", lambda: 1.0)
        plot.update()  # not started — should be no-op

    def test_pause_resume_state(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        plot.pause()
        assert plot.is_paused
        plot.resume()
        assert not plot.is_paused

    def test_clear_does_not_raise(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        plot.watch("x", lambda: 1.0)
        plot.clear()  # should not raise even before start

    def test_stop_when_not_running_does_not_raise(self):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        plot.stop()  # should not raise

    def test_export_when_not_started_does_not_raise(self, tmp_path):
        from bulletlab.plotting import LivePlot
        plot = LivePlot()
        plot.export(str(tmp_path / "plot.png"))  # should print warning, not raise
