"""
BulletLab Interactive Demo
==========================

Loads a robot model and lets you control every joint via the UI window.

Two windows open:
  • PyBullet window  — 3D physics simulation
  • BulletLab window — sliders, telemetry, console, live plots

Usage:
    python examples/demo_ui_control.py              # auto-picks best model
    python examples/demo_ui_control.py r2d2         # R2D2 (velocity wheels)
    python examples/demo_ui_control.py kuka         # Kuka iiwa arm (position)
    python examples/demo_ui_control.py husky        # Husky rover (velocity)
"""

from __future__ import annotations

import math
import sys
import time

import pybullet_data

from bulletlab import Robot, Simulation
from bulletlab.telemetry import TelemetryManager
from bulletlab.ui import BulletLabUI
from bulletlab.ui import widgets as ui


# ──────────────────────────────────────────────────────────────────────────────
# 1.  Model catalogue
# ──────────────────────────────────────────────────────────────────────────────

MODELS = {
    "kuka": {
        "urdf":       "kuka_iiwa/model.urdf",
        "name":       "Kuka iiwa 14",
        "position":   (0, 0, 0),
        "fixed_base": True,
        "mode":       "position",      # joint control mode
        "description": "7-DOF robotic arm — drag sliders to pose each joint",
    },
    "r2d2": {
        "urdf":       "r2d2.urdf",
        "name":       "R2D2",
        "position":   (0, 0, 0.3),
        "fixed_base": False,
        "mode":       "velocity",
        "description": "Wheeled robot — set wheel velocities to drive around",
    },
    "husky": {
        "urdf":       "husky/husky.urdf",
        "name":       "Husky Rover",
        "position":   (0, 0, 0.2),
        "fixed_base": False,
        "mode":       "velocity",
        "description": "4-wheel-drive rover — set wheel velocities to steer",
    },
    "ant": {
        "urdf":       "ant.urdf",
        "name":       "Ant Robot",
        "position":   (0, 0, 0.5),
        "fixed_base": False,
        "mode":       "torque",
        "description": "Multi-legged ant — apply torques to each leg joint",
    },
}

# Default preference order
DEFAULT_ORDER = ["kuka", "r2d2", "husky", "ant"]


def pick_model(arg: str | None) -> dict:
    """Return model config; fall back gracefully if URDF not found."""
    import os
    data = pybullet_data.getDataPath()

    if arg and arg.lower() in MODELS:
        cfg = MODELS[arg.lower()]
        if os.path.exists(os.path.join(data, cfg["urdf"])):
            return cfg
        print(f"[demo] '{arg}' URDF not found, trying defaults…")

    for key in DEFAULT_ORDER:
        cfg = MODELS[key]
        if os.path.exists(os.path.join(data, cfg["urdf"])):
            return cfg

    raise RuntimeError("No bundled URDF found. Check pybullet_data installation.")


# ──────────────────────────────────────────────────────────────────────────────
# 2.  Per-joint slider helpers
# ──────────────────────────────────────────────────────────────────────────────

class JointState:
    """Holds the current target value for one joint (position, velocity, or torque)."""
    def __init__(self, default: float = 0.0):
        self.target: float = default

# We store targets in a dict so the UI closures can capture live references.
_joint_targets: dict[str, JointState] = {}


def build_joint_panel(robot: Robot, mode: str):
    """Return an ImGui render function that draws sliders for each joint."""

    controllable = robot.controllable_joints
    for j in controllable:
        _joint_targets[j.name] = JointState(0.0)

    def render():
        ui.text("Model",  robot.name)
        ui.text("Mode",   mode.capitalize() + " control")
        ui.text("Joints", str(len(controllable)))
        ui.separator()

        for j in controllable:
            state = _joint_targets[j.name]
            lo, hi = j.limits if j.limits != (0.0, 0.0) else (-3.14, 3.14)

            if mode == "velocity":
                lo, hi = -20.0, 20.0   # rad/s

            elif mode == "torque":
                lo, hi = -50.0, 50.0   # N·m

            # Slider — short label so it fits
            label = j.name[:22] if len(j.name) > 22 else j.name
            state.target = ui.slider(
                label,
                lambda s=state: s.target,
                lo, hi,
                setter=lambda v, s=state: setattr(s, "target", v),
            )

        ui.separator()
        if ui.button("  Zero All  "):
            for s in _joint_targets.values():
                s.target = 0.0

        if mode == "position":
            ui.same_line()
            if ui.button("  Wave  "):
                # Animate a sine wave across all joints
                t = time.monotonic()
                for i, j in enumerate(controllable):
                    _joint_targets[j.name].target = math.sin(t + i * 0.5) * 1.0

    return render


def apply_targets(robot: Robot, mode: str):
    """Send the current slider targets to PyBullet."""
    for joint in robot.controllable_joints:
        target = _joint_targets.get(joint.name)
        if target is None:
            continue

        if mode == "position":
            joint.set_position(target.target)

        elif mode == "velocity":
            joint.velocity = target.target

        elif mode == "torque":
            joint.torque = target.target


# ──────────────────────────────────────────────────────────────────────────────
# 3.  Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    model_cfg = pick_model(arg)

    print(f"\n{'─'*60}")
    print(f"  BulletLab Demo  —  {model_cfg['name']}")
    print(f"  {model_cfg['description']}")
    print(f"{'─'*60}\n")

    # ── Simulation ───────────────────────────────────────────────────────────
    sim = Simulation(mode="gui", gravity=(0, 0, -9.81), timestep=1/240).start()

    # Ground plane
    from bulletlab.core.world import World
    world = World(sim=sim)
    world.load_plane()

    # Load robot
    robot = Robot.load(
        model_cfg["urdf"],
        sim=sim,
        position=model_cfg["position"],
        fixed_base=model_cfg["fixed_base"],
        name=model_cfg["name"],
    )

    print(f"  Joints  : {list(robot.joints.keys())}")
    print(f"  Links   : {list(robot.links.keys())}")
    print(f"  Controllable joints: {robot.num_controllable_joints}\n")

    mode = model_cfg["mode"]

    # ── Telemetry ─────────────────────────────────────────────────────────────
    telemetry = TelemetryManager()
    telemetry.watch("Speed",    lambda: robot.speed,               unit="m/s")
    telemetry.watch("Height",   lambda: robot.base_position[2],    unit="m")
    telemetry.watch("Roll",     lambda: math.degrees(robot.roll),  unit="°")
    telemetry.watch("Pitch",    lambda: math.degrees(robot.pitch), unit="°")
    telemetry.watch("SimStep",  lambda: sim.step_count)

    for j in robot.controllable_joints[:4]:
        telemetry.watch(
            f"j:{j.name[:12]}",
            (lambda jj: lambda: jj.position)(j),
            unit="rad",
        )

    # ── UI ────────────────────────────────────────────────────────────────────
    app = BulletLabUI(
        sim=sim,
        robots=[robot],
        telemetry=telemetry,
        title=f"BulletLab — {model_cfg['name']}",
        width=660,
        height=900,
    )

    # Joint control panel (custom)
    joint_render_fn = build_joint_panel(robot, mode)
    app.register_panel("🎮  Joint Control", joint_render_fn)

    # Info panel
    def info_panel():
        ui.text("Model",   robot.name)
        ui.text("Mode",    mode.capitalize())
        ui.text("Joints",  str(robot.num_controllable_joints))
        ui.text("Links",   str(len(robot.links)))
        ui.separator("Base State")
        pos = robot.base_position
        ui.text("X",  f"{pos[0]:.3f} m")
        ui.text("Y",  f"{pos[1]:.3f} m")
        ui.text("Z",  f"{pos[2]:.3f} m")
        ui.text("Speed",  f"{robot.speed:.3f} m/s")
        ui.text("Roll",   f"{math.degrees(robot.roll):.1f} °")
        ui.text("Pitch",  f"{math.degrees(robot.pitch):.1f} °")
        ui.text("Yaw",    f"{math.degrees(robot.yaw):.1f} °")
        ui.separator("Actions")
        if ui.button("Reset Robot"):
            robot.reset()
            for s in _joint_targets.values():
                s.target = 0.0

    app.register_panel("📊  Info", info_panel)
    app.start()

    # ── Simulation loop ───────────────────────────────────────────────────────
    print("  Simulation running. Close the BulletLab window to exit.\n")

    step = 0
    while sim.is_connected and not app.should_close:
        apply_targets(robot, mode)
        sim.step()

        step += 1
        if step % 10 == 0:
            telemetry.update(t=sim.elapsed_time)

        app.step()

    app.stop()
    sim.stop()
    print("\n  Demo finished. Goodbye!\n")


if __name__ == "__main__":
    main()
