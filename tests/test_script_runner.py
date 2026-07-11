"""Tests for bulletlab.ui.script_runner.ScriptRunner."""

from __future__ import annotations

import time
import pytest
from bulletlab.ui.script_runner import ScriptRunner


def _make_runner(namespace=None, sim=None):
    """Helper: create a runner with capture lists."""
    outputs = []
    errors = []
    echoes = []
    dones = [0]

    def on_output(line):
        outputs.append(line)

    def on_error(line):
        errors.append(line)

    def on_echo(line):
        echoes.append(line)

    def on_done():
        dones[0] += 1

    runner = ScriptRunner(
        namespace=namespace if namespace is not None else {},
        sim=sim,
        on_output=on_output,
        on_error=on_error,
        on_echo=on_echo,
        on_done=on_done,
    )
    return runner, outputs, errors, echoes, dones


def _tick_until_done(runner, timeout=2.0):
    """Wait for the runner to complete, calling tick() periodically."""
    start = time.monotonic()
    while runner.is_active:
        runner.tick()
        if time.monotonic() - start > timeout:
            raise TimeoutError("Runner did not complete in time")
        time.sleep(0.01)
    runner.tick() # final drain


class TestScriptRunnerBasics:
    def test_not_active_initially(self):
        runner, *_ = _make_runner()
        assert not runner.is_active

    def test_load_empty_returns_false(self):
        runner, *_ = _make_runner()
        result = runner.load("")
        assert result is False
        assert not runner.is_active

    def test_load_valid_activates(self):
        runner, *_ = _make_runner()
        result = runner.load("x = 1")
        assert result is True
        assert runner.is_active
        runner.cancel()

    def test_syntax_error_not_active(self):
        runner, outputs, errors, echoes, dones = _make_runner()
        result = runner.load("def (: broken")
        assert result is False
        assert not runner.is_active
        assert any("SyntaxError" in e for e in errors)

    def test_cancel_deactivates(self):
        runner, *_ = _make_runner()
        runner.load("while True: pass")  # infinite loop
        assert runner.is_active
        runner.cancel()
        assert not runner.is_active


class TestScriptRunnerExecution:
    def test_script_execution_changes_namespace(self):
        ns = {}
        runner, *_ = _make_runner(namespace=ns)
        runner.load("x = 99")
        _tick_until_done(runner)
        assert ns.get("x") == 99

    def test_echo_fires_on_start(self):
        runner, outputs, errors, echoes, dones = _make_runner()
        runner.load("a = 1\nb = 2")
        _tick_until_done(runner)
        assert len(echoes) == 1
        assert "a = 1" in echoes[0]
        assert "..." in echoes[0]

    def test_print_output_captured(self):
        runner, outputs, errors, echoes, dones = _make_runner()
        runner.load("print('hello')")
        _tick_until_done(runner)
        assert any("hello" in o for o in outputs)

    def test_error_aborts_script(self):
        ns = {}
        runner, outputs, errors, echoes, dones = _make_runner(namespace=ns)
        runner.load("x = 1\nraise ValueError('oops')\ny = 99")
        _tick_until_done(runner)
        assert any("ValueError" in e for e in errors)
        assert "y" not in ns  # Third statement never ran

    def test_reload_cancels_previous(self):
        ns = {}
        runner, *_ = _make_runner(namespace=ns)
        # Load a script that takes a long time
        runner.load("import time; time.sleep(0.5); x = 1")
        # Immediately load another
        runner.load("z = 99")
        _tick_until_done(runner)
        assert ns.get("z") == 99
        assert "x" not in ns


class TestScriptRunnerWaitAndStep:
    def test_wait_pauses_execution(self):
        ns = {}
        runner, outputs, errors, echoes, dones = _make_runner(namespace=ns)
        ns.update(runner.make_builtins())
        
        start = time.time()
        runner.load("wait(100)\nx = 1")
        _tick_until_done(runner)
        duration = time.time() - start
        
        assert ns.get("x") == 1
        assert duration >= 0.1

    def test_step_calls_sim(self):
        class FakeSim:
            def __init__(self):
                self.steps = 0
            def step(self):
                self.steps += 1

        fake_sim = FakeSim()
        ns = {}
        runner, *_ = _make_runner(namespace=ns, sim=fake_sim)
        ns.update(runner.make_builtins())
        
        runner.load("step(5)")
        _tick_until_done(runner)
        
        assert fake_sim.steps == 5

    def test_step_without_sim_does_not_crash(self):
        ns = {}
        runner, *_ = _make_runner(namespace=ns, sim=None)
        ns.update(runner.make_builtins())
        runner.load("step(10)")
        _tick_until_done(runner)


class TestConsolePanelSequential:
    """Integration: ConsolePanel sequential execution via tick()."""

    def test_single_statement_executes_immediately(self):
        from bulletlab.ui.panels.console import ConsolePanel
        ns = {}
        panel = ConsolePanel(namespace=ns)
        panel.execute("x = 42")
        assert ns.get("x") == 42
        assert not panel._script_running

    def test_multi_statement_uses_runner(self):
        from bulletlab.ui.panels.console import ConsolePanel
        ns = {}
        panel = ConsolePanel(namespace=ns)
        panel.execute("x = 1\ny = 2")
        # After execute, runner should be active
        assert panel._script_running
        _tick_until_done(panel._runner)
        assert ns.get("x") == 1
        assert ns.get("y") == 2
        assert not panel._script_running

    def test_cancel_script_aborts_runner(self):
        from bulletlab.ui.panels.console import ConsolePanel
        ns = {}
        panel = ConsolePanel(namespace=ns)
        panel.execute("while True: pass")
        assert panel._script_running
        panel.cancel_script()
        assert not panel._script_running
        _tick_until_done(panel._runner)
        assert "x" not in ns

    def test_wait_builtin_available(self):
        from bulletlab.ui.panels.console import ConsolePanel
        ns = {}
        panel = ConsolePanel(namespace=ns)
        assert "wait" in panel._namespace

    def test_step_builtin_available(self):
        from bulletlab.ui.panels.console import ConsolePanel
        ns = {}
        panel = ConsolePanel(namespace=ns)
        assert "step" in panel._namespace

    def test_execute_cancels_previous_script(self):
        from bulletlab.ui.panels.console import ConsolePanel
        ns = {}
        panel = ConsolePanel(namespace=ns)
        panel.execute("import time; time.sleep(0.5); x = 1")
        # Cancel by submitting a new script
        panel.execute("z = 99\nw = 88")
        _tick_until_done(panel._runner)
        assert ns.get("z") == 99
        assert ns.get("w") == 88
        assert "x" not in ns  # old script cancelled

    def test_tick_is_noop_when_idle(self):
        from bulletlab.ui.panels.console import ConsolePanel
        panel = ConsolePanel()
        panel.tick()  # should not raise or do anything
