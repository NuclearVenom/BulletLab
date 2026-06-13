"""Tests for bulletlab.logging (DataLogger, CsvWriter, JsonWriter)."""

import csv
import json
import math
import os
import pytest
from pathlib import Path

from bulletlab.logging import DataLogger
from bulletlab.logging.csv_writer import CsvWriter
from bulletlab.logging.json_writer import JsonWriter


class TestCsvWriter:
    def test_creates_file(self, tmp_path):
        path = tmp_path / "test.csv"
        w = CsvWriter(path, ["a", "b"])
        w.close()
        assert path.exists()

    def test_writes_header(self, tmp_path):
        path = tmp_path / "test.csv"
        w = CsvWriter(path, ["x", "y"])
        w.close()
        with open(path) as f:
            header = f.readline().strip()
        assert header == "x,y"

    def test_writes_row(self, tmp_path):
        path = tmp_path / "test.csv"
        w = CsvWriter(path, ["a", "b"])
        w.write_row({"a": 1.0, "b": 2.0})
        w.close()
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert float(rows[0]["a"]) == pytest.approx(1.0)

    def test_flush_does_not_raise(self, tmp_path):
        path = tmp_path / "test.csv"
        w = CsvWriter(path, ["x"])
        w.flush()
        w.close()


class TestJsonWriter:
    def test_creates_file(self, tmp_path):
        path = tmp_path / "test.json"
        w = JsonWriter(path)
        w.close()
        assert path.exists()

    def test_writes_ndjson_line(self, tmp_path):
        path = tmp_path / "test.json"
        w = JsonWriter(path)
        w.write_row({"t": 0.0, "val": 42.0})
        w.close()
        with open(path) as f:
            line = f.readline().strip()
        obj = json.loads(line)
        assert obj["val"] == pytest.approx(42.0)

    def test_multiple_rows(self, tmp_path):
        path = tmp_path / "test.json"
        w = JsonWriter(path)
        for i in range(5):
            w.write_row({"i": i})
        w.close()
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 5


class TestDataLogger:
    def test_watch_and_start_csv(self, tmp_path):
        path = tmp_path / "log.csv"
        logger = DataLogger()
        logger.watch("x", lambda: 1.0)
        logger.start(str(path))
        assert logger.is_running
        logger.stop()
        assert path.exists()

    def test_watch_and_start_json(self, tmp_path):
        path = tmp_path / "log.json"
        logger = DataLogger()
        logger.watch("x", lambda: 1.0)
        logger.start(str(path))
        logger.stop()
        assert path.exists()

    def test_step_records_data(self, tmp_path):
        path = tmp_path / "log.csv"
        counter = [0]
        logger = DataLogger()
        logger.watch("count", lambda: float(counter[0]))
        logger.start(str(path))
        for i in range(5):
            counter[0] = i
            logger.step()
        logger.stop()
        with open(path) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 5
        assert float(rows[4]["count"]) == pytest.approx(4.0)

    def test_step_count(self, tmp_path):
        path = tmp_path / "log.csv"
        logger = DataLogger()
        logger.watch("x", lambda: 1.0)
        logger.start(str(path))
        for _ in range(10):
            logger.step()
        logger.stop()
        assert logger.step_count == 10

    def test_step_not_running_is_noop(self):
        logger = DataLogger()
        logger.watch("x", lambda: 1.0)
        result = logger.step()  # not started
        assert result == {}

    def test_context_manager(self, tmp_path):
        path = tmp_path / "log.csv"
        with DataLogger() as logger:
            logger.watch("x", lambda: 1.0)
            logger.start(str(path))
            logger.step()
        assert not logger.is_running

    def test_double_start_raises(self, tmp_path):
        path = tmp_path / "log.csv"
        logger = DataLogger()
        logger.watch("x", lambda: 1.0)
        logger.start(str(path))
        with pytest.raises(RuntimeError):
            logger.start(str(tmp_path / "other.csv"))
        logger.stop()

    def test_unwatch(self, tmp_path):
        path = tmp_path / "log.csv"
        logger = DataLogger()
        logger.watch("x", lambda: 1.0)
        logger.watch("y", lambda: 2.0)
        logger.unwatch("y")
        assert "y" not in logger.channel_names
        assert "x" in logger.channel_names

    def test_timestamp_column_present(self, tmp_path):
        path = tmp_path / "log.csv"
        logger = DataLogger(include_timestamp=True)
        logger.watch("x", lambda: 1.0)
        logger.start(str(path))
        logger.step()
        logger.stop()
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert "t" in rows[0]

    def test_step_column_present(self, tmp_path):
        path = tmp_path / "log.csv"
        logger = DataLogger(include_step=True)
        logger.watch("x", lambda: 1.0)
        logger.start(str(path))
        logger.step()
        logger.stop()
        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert "step" in rows[0]
        assert int(rows[0]["step"]) == 0

    def test_chained_watch(self, tmp_path):
        path = tmp_path / "log.csv"
        logger = DataLogger()
        result = logger.watch("a", lambda: 1.0).watch("b", lambda: 2.0)
        assert result is logger

    def test_json_output_correct(self, tmp_path):
        path = tmp_path / "log.json"
        logger = DataLogger()
        logger.watch("val", lambda: 99.0)
        logger.start(str(path))
        logger.step(t=1.5)
        logger.stop()
        with open(path) as f:
            obj = json.loads(f.readline())
        assert obj["val"] == pytest.approx(99.0)
        assert obj["t"] == pytest.approx(1.5)

    def test_nan_on_source_exception(self, tmp_path):
        path = tmp_path / "log.csv"
        def bad():
            raise RuntimeError("bad")

        logger = DataLogger()
        logger.watch("bad", bad)
        logger.start(str(path))
        row = logger.step()
        logger.stop()
        assert math.isnan(row["bad"])

    def test_flush_does_not_raise(self, tmp_path):
        path = tmp_path / "log.csv"
        logger = DataLogger()
        logger.watch("x", lambda: 1.0)
        logger.start(str(path))
        logger.flush()
        logger.stop()
