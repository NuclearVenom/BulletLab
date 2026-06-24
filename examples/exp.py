"""
BulletLab Universal URDF Loader & Controller
============================================
Usage:
    python universal_loader.py <path/to/model.urdf>
    python universal_loader.py <path/to/model.urdf> --fixed
    python universal_loader.py husky/husky.urdf           # from pybullet_data
"""

import sys
import math
import pybullet_data

from bulletlab import Simulation, Robot
from bulletlab.core.world import World
from bulletlab.ui import BulletLabUI
from bulletlab.ui import widgets as ui

# ─────────────────────────────────────────────────────────────────────────────
# Config — edit these or pass via command line
# ─────────────────────────────────────────────────────────────────────────────
URDF_PATH  = sys.argv[1] if len(sys.argv) > 1 else ""
FIXED_BASE = "--fixed" in sys.argv
SPAWN_POS  = (0, 0, 0.791)

# Control mode: "position" | "velocity" | "torque"
ctrl_mode = ["position"]

# ─────────────────────────────────────────────────────────────────────────────
# Simulation + ground
# ─────────────────────────────────────────────────────────────────────────────
sim = Simulation(mode="gui", gravity=(0, 0, -9.81), timestep=1/240).start()
World(sim=sim).load_plane()

robot = Robot.load(
    URDF_PATH,
    sim        = sim,
    position   = SPAWN_POS,
    fixed_base = FIXED_BASE,
    name       = URDF_PATH.split("/")[-1].replace(".urdf", ""),
)

sim.set_camera(distance=2.5, yaw=45, pitch=-25, target=(0, 0, 0.5))

joints = robot.controllable_joints
print(f"\nLoaded : {robot.name}")
print(f"Joints : {len(joints)}")
print(f"Links  : {len(robot.links)}")
for j in joints:
    print(f"  [{j.index}] {j.name}  limits={j.limits}")

# apply_targets reads the live target stored on each joint (j.target).
# Sliders write to j.target; console commands write via the property setters
# which also update j.target and sync the slider position.

def apply_targets():
    mode = ctrl_mode[0]
    for j in joints:
        try:
            if mode == "position":
                j.set_position(j.target)   # respects pin if joint.pin_position was set
            elif mode == "velocity":
                j.set_velocity(j.target)   # respects pin if joint.pin_velocity was set
            elif mode == "torque":
                j.set_torque(j.target)     # respects pin if joint.pin_torque was set
        except Exception:
            pass

# ─────────────────────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────────────────────
app = BulletLabUI(
    sim=sim, robots=[robot],
    title=f"BulletLab — {robot.name}",
    width=480, height=900,
)

@app.custom_panel(f"🔧  {robot.name}")
def control_panel():

    # ── Info ─────────────────────────────────────────────────────────────────
    pos = robot.base_position
    ui.text("Model",   robot.name)
    ui.text("Joints",  str(len(joints)))
    ui.text("Links",   str(len(robot.links)))
    ui.text("Pos",     f"({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
    ui.text("Speed",   f"{robot.speed:.3f} m/s")

    ui.separator("Control Mode")

    # Mode buttons
    for m in ("position", "velocity", "torque"):
        label = f"[{'X' if ctrl_mode[0]==m else ' '}] {m.capitalize()}"
        if ui.button(label):
            ctrl_mode[0] = m
            # Reset all targets and release all pins when switching mode
            for jj in joints:
                jj.target = 0.0
                jj.unpin()
        ui.same_line()
    ui.text("")   # newline after same_line chain

    ui.separator("Joint Sliders")

    mode = ctrl_mode[0]
    for j in joints:
        # Choose slider range per mode
        if mode == "position":
            lo, hi = j.limits if j.limits != (0.0, 0.0) else (-3.14, 3.14)
        elif mode == "velocity":
            lo, hi = -20.0, 20.0
        else:   # torque
            lo, hi = -50.0, 50.0

        # Color the slider knob red when the joint is pinned
        ui.slider(
            j.name[-20:],
            lambda jj=j: jj.target,
            lo, hi,
            setter=lambda v, jj=j: setattr(jj, "target", v),
            fmt="%.3f",
            highlight=j.is_pinned,
        )

    ui.separator("Actions")

    if ui.button("  Zero All  "):
        for jj in joints:
            jj.target = 0.0
            jj.unpin()

    ui.same_line()

    if ui.button("  Reset Robot  "):
        robot.reset()
        for jj in joints:
            jj.target = 0.0
            jj.unpin()

    ui.same_line()

    if ui.button("  Pause Sim  "):
        sim.pause() if not sim.is_paused else sim.resume()

app.start()

# ── Console help messages ──────────────────────────────────────────────────────
# robot, sim are always in the console namespace.
# Use property setters to pin joints — they override the slider loop:
#   robot.joints['left_knee_joint'].position = 1.0   # pin to position
#   robot.joints['left_knee_joint'].velocity = 5.0   # pin to velocity
#   robot.joints['left_knee_joint'].unpin()           # release back to sliders
#   [j.name for j in robot.controllable_joints]       # list all joint names
app._console.log("Console ready  —  robot and sim are available.")
app._console.log("  Move & free  →  robot.joints['left_knee_joint'].position = 1.0")
app._console.log("  Move & lock  →  robot.joints['left_knee_joint'].pin_position = 1.0")
app._console.log("  Release pin  →  robot.joints['left_knee_joint'].unpin()")
app._console.log("  Unpin all    →  [j.unpin() for j in robot.controllable_joints]")
app._console.log("  List joints  →  [j.name for j in robot.controllable_joints]")

# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────
while not app.should_close:
    apply_targets()
    sim.step()
    app.step()

app.stop()
sim.stop()
