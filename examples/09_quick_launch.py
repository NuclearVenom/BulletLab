"""
Example 09: Instant Robot Deployment with quickLaunch()
======================================================
Demonstrates BulletLab's signature one-liner deployment feature.

Pass any model path (built-in URDF, local file, or Arsenal package URI)
and quickLaunch immediately spins up:
  - Physics world with ground plane and realistic gravity
  - Auto-generated Joint Control UI with Position / Velocity / Torque modes
  - Dynamic Camera Tracking with smooth follow mode and capsule toggle switch
  - Live Telemetry tracking base pose, speed, roll/pitch/yaw, and joint angles
  - Interactive Python Console for live scripting

Run with default (R2D2):
    python examples/09_quick_launch.py

Run with an Arsenal package:
    python examples/09_quick_launch.py arsenal:reference_bot

Run with a local/built-in URDF:
    python examples/09_quick_launch.py kuka_iiwa/model.urdf
"""

import sys
from pathlib import Path

# Allow importing bulletlab from source checkout
sys.path.insert(0, str(Path(__file__).parent.parent))

import bulletlab


def main() -> None:
    # Accept model path from command-line argument, or default to Arsenal model
    model_path = sys.argv[1] if len(sys.argv) > 1 else "arsenal:reference_bot"

    print("=" * 60)
    print("  BulletLab — Signature One-Line Deployment")
    print(f"  Target Model: {model_path}")
    print("=" * 60)

    # ⚡ ONE LINE AND YOUR MODEL IS DEPLOYED!
    bulletlab.quickLaunch(model_path)


if __name__ == "__main__":
    main()
