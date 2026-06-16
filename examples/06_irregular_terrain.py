"""
Example 06 — Husky Rover on Irregular Terrain
Driven via the ImGui control panel.
"""

import math
import numpy as np
import pybullet as p

from bulletlab import Simulation, Robot
from bulletlab.core.world import World
from bulletlab.telemetry import TelemetryManager
from bulletlab.ui import BulletLabUI
from bulletlab.ui import widgets as ui

# ─────────────────────────────────────────────────────────────────────────────
# 1. Simulation
# ─────────────────────────────────────────────────────────────────────────────
sim = Simulation(mode="gui", gravity=(0, 0, -9.81), timestep=1/240).start()
cid = sim.client_id

# ─────────────────────────────────────────────────────────────────────────────
# 2. Irregular terrain via PyBullet heightfield
# ─────────────────────────────────────────────────────────────────────────────
TERRAIN_SIZE = 256
np.random.seed(42)

# Multi-octave noise for natural-looking hills
def make_heightfield(n):
    h = np.zeros((n, n))
    for octave, amp, freq in [(1, 0.6, 0.05), (2, 0.3, 0.12), (4, 0.1, 0.3)]:
        for i in range(n):
            for j in range(n):
                h[i, j] += amp * math.sin(freq * i) * math.cos(freq * j)
    h += np.random.uniform(-0.15, 0.15, (n, n))  # fine grain noise
    # Flatten a 6×6 square at the origin so the rover spawns cleanly
    cx, cy = n // 2, n // 2
    h[cx-8:cx+8, cy-8:cy+8] = 0.0
    return h.flatten().tolist()

heights = make_heightfield(TERRAIN_SIZE)
scale   = 0.25   # height scale

terrain_shape = p.createCollisionShape(
    p.GEOM_HEIGHTFIELD,
    meshScale       = [0.1, 0.1, scale],
    heightfieldData = heights,
    numHeightfieldRows    = TERRAIN_SIZE,
    numHeightfieldColumns = TERRAIN_SIZE,
    physicsClientId = cid,
)
terrain_body = p.createMultiBody(
    baseCollisionShapeIndex = terrain_shape,
    basePosition            = (0, 0, 0),
    physicsClientId         = cid,
)
p.changeVisualShape(
    terrain_body, -1,
    rgbaColor = (0.55, 0.45, 0.35, 1.0),   # dirt colour
    physicsClientId = cid,
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Scatter some rocks / ramps for extra obstacles
# ─────────────────────────────────────────────────────────────────────────────
rng = np.random.default_rng(7)
for _ in range(30):
    x, y  = rng.uniform(-10, 8, 2)
    sz    = rng.uniform(0.2, 0.6, 3).tolist()
    shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=sz, physicsClientId=cid)
    vis   = p.createVisualShape(
        p.GEOM_BOX, halfExtents=sz,
        rgbaColor=(0.4, 0.4, 0.4, 1.0),
        physicsClientId=cid,
    )
    p.createMultiBody(
        baseMass                = 0,
        baseCollisionShapeIndex = shape,
        baseVisualShapeIndex    = vis,
        basePosition            = [x, y, sz[2]],
        physicsClientId         = cid,
    )

# ─────────────────────────────────────────────────────────────────────────────
# 4. Load Husky rover
# ─────────────────────────────────────────────────────────────────────────────
robot = Robot.load(
    "husky/husky.urdf",
    sim      = sim,
    position = (0, 0, 0.4),
    name     = "Husky",
)

sim.set_camera(distance=5.0, yaw=50, pitch=-30, target=(0, 0, 0.2))

# Wheel joint names in Husky URDF
WHEEL_JOINTS = [
    "front_left_wheel",
    "front_right_wheel",
    "rear_left_wheel",
    "rear_right_wheel",
]

def get_wheel(name):
    """Return joint by name, gracefully."""
    return robot.joints.get(name)

wheels = {n: get_wheel(n) for n in WHEEL_JOINTS}
wheels = {k: v for k, v in wheels.items() if v is not None}
print("Wheel joints found:", list(wheels.keys()))

# ─────────────────────────────────────────────────────────────────────────────
# 5. Drive state (controlled by UI sliders)
# ─────────────────────────────────────────────────────────────────────────────
drive = {
    "throttle": 0.0,   # -1 → 1  (backward → forward)
    "steer":    0.0,   # -1 → 1  (left → right)
    "max_vel":  15.0,  # rad/s cap
    "stopped":  False,
}

def apply_drive():
    if drive["stopped"]:
        for w in wheels.values():
            w.velocity = 0.0
        return
    cap   = drive["max_vel"]
    fwd   = drive["throttle"] * cap
    turn  = drive["steer"]    * cap * 0.5
    left_vel  = fwd - turn
    right_vel = fwd + turn
    for name, joint in wheels.items():
        if "left" in name:
            joint.velocity = left_vel
        else:
            joint.velocity = right_vel

# ─────────────────────────────────────────────────────────────────────────────
# 6. Telemetry
# ─────────────────────────────────────────────────────────────────────────────
telemetry = TelemetryManager()
telemetry.watch("Speed",  lambda: robot.speed,                 unit="m/s")
telemetry.watch("Height", lambda: robot.base_position[2],      unit="m")
telemetry.watch("Roll",   lambda: math.degrees(robot.roll),    unit="°")
telemetry.watch("Pitch",  lambda: math.degrees(robot.pitch),   unit="°")

# ─────────────────────────────────────────────────────────────────────────────
# 7. UI
# ─────────────────────────────────────────────────────────────────────────────
app = BulletLabUI(
    sim=sim, robots=[robot], telemetry=telemetry,
    title="BulletLab — Husky on Terrain",
    width=480, height=820,
)

@app.custom_panel("Drive Controls")
def drive_panel():
    pos = robot.base_position
    ui.text("Speed",  f"{robot.speed:.2f} m/s")
    ui.text("Height", f"{pos[2]:.3f} m")
    ui.text("Roll",   f"{math.degrees(robot.roll):.1f} °")
    ui.text("Pitch",  f"{math.degrees(robot.pitch):.1f} °")

    ui.separator("Controls")

    drive["throttle"] = ui.slider(
        "Throttle ↑↓",
        lambda: drive["throttle"],
        -1.0, 1.0,
        setter=lambda v: drive.__setitem__("throttle", v),
        fmt="%.2f",
    )
    drive["steer"] = ui.slider(
        "Steer  ←→",
        lambda: drive["steer"],
        -1.0, 1.0,
        setter=lambda v: drive.__setitem__("steer", v),
        fmt="%.2f",
    )
    drive["max_vel"] = ui.slider(
        "Max Speed",
        lambda: drive["max_vel"],
        1.0, 40.0,
        setter=lambda v: drive.__setitem__("max_vel", v),
        fmt="%.1f rad/s",
    )

    ui.separator("Actions")
    if ui.button("  ⏹  STOP  "):
        drive["throttle"] = 0.0
        drive["steer"]    = 0.0
    ui.same_line()
    if ui.button("  Reset Rover  "):
        robot.reset()
        drive["throttle"] = 0.0
        drive["steer"]    = 0.0

app.start()

# ─────────────────────────────────────────────────────────────────────────────
# 8. Main loop
# ─────────────────────────────────────────────────────────────────────────────
step = 0
while not app.should_close:
    apply_drive()
    sim.step()
    step += 1
    if step % 10 == 0:
        telemetry.update(t=sim.elapsed_time)
    app.step()

app.stop()
sim.stop()
