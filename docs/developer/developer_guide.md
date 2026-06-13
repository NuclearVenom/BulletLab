# Developer Guide

## Setting Up a Development Environment

```bash
git clone https://github.com/bulletlab/bulletlab
cd bulletlab
pip install -e ".[dev]"
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=bulletlab --cov-report=term-missing

# Run a specific test file
pytest tests/test_simulation.py -v

# Run a specific test
pytest tests/test_robot.py::TestRobotLoad::test_load_kuka -v
```

## Building Documentation

```bash
mkdocs serve       # live preview at http://localhost:8000
mkdocs build       # build static site in site/
```

## Project Structure

```
BulletLab/
├── bulletlab/          # Main library package
│   ├── core/           # Simulation, World
│   ├── robot/          # Robot, Joint, Link
│   ├── telemetry/      # TelemetryManager, TelemetryChannel
│   ├── logging/        # DataLogger, CsvWriter, JsonWriter
│   ├── plotting/       # LivePlot
│   ├── ui/             # BulletLabUI, panels, widgets
│   └── utils/          # math_utils, urdf_utils, timer
├── examples/           # 5 working examples
├── tests/              # pytest test suite
├── docs/               # MkDocs documentation
├── pyproject.toml      # Build configuration
└── README.md
```

## Adding a New Panel

1. Create `bulletlab/ui/panels/my_panel.py` with a class:

```python
class MyPanel:
    def __init__(self, ...):
        ...

    def render(self) -> None:
        if not _HAS_IMGUI:
            return
        import imgui
        imgui.text("My Panel")
```

2. Export from `bulletlab/ui/panels/__init__.py`
3. Register in `BulletLabUI._build_panels()` or let users register via `app.register_panel()`

## Adding a New Utility

1. Create or extend `bulletlab/utils/my_utils.py`
2. Export from `bulletlab/utils/__init__.py`
3. Write tests in `tests/test_utils.py`

## Code Style

- Type hints on all public functions
- Google-style docstrings with `Args:`, `Returns:`, `Example::`
- No bare `except:` — always catch specific exceptions
- Graceful degradation for optional dependencies (check `_HAS_X` before using)

## Contribution Checklist

- [ ] Type hints on all public API
- [ ] Docstring with example
- [ ] Tests added/updated
- [ ] `pytest tests/` passes
- [ ] `pip install -e .` succeeds cleanly
