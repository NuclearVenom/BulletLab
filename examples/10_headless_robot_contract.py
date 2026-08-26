"""
Example 10: Headless Robot Contract
===================================
Load any URDF without a display and print its action, observation, joint, and
link contract as JSON.

Usage::

    python examples/10_headless_robot_contract.py
    python examples/10_headless_robot_contract.py r2d2.urdf
    python examples/10_headless_robot_contract.py kuka_iiwa/model.urdf --output robot.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from bulletlab import Robot, Simulation, robot_contract
from bulletlab.utils.urdf_utils import find_urdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urdf", nargs="?", default="kuka_iiwa/model.urdf")
    parser.add_argument("--output", type=Path, help="write JSON to this path instead of stdout")
    args = parser.parse_args()

    sim = Simulation(mode="direct")
    sim.start()
    try:
        urdf_path = find_urdf(args.urdf)
        robot = Robot.load(str(urdf_path), sim=sim, fixed_base=True)
        payload = json.dumps(robot_contract(robot), indent=2)
        if args.output is None:
            print(payload)
        else:
            args.output.write_text(f"{payload}\n", encoding="utf-8")
            print(f"Wrote robot contract to {args.output}")
    finally:
        sim.stop()


if __name__ == "__main__":
    main()
