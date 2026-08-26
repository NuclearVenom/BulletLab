"""Tests for the machine-readable robot contract."""

import json

from bulletlab import robot_contract


def test_robot_contract_matches_action_and_state_interfaces(kuka_robot):
    contract = robot_contract(kuka_robot)

    assert contract["schema_version"] == 1
    assert contract["name"] == "TestKuka"
    assert contract["action"] == {
        "size": kuka_robot.num_controllable_joints,
        "joint_order": [joint.name for joint in kuka_robot.controllable_joints],
    }
    assert contract["observation"]["state_size"] == kuka_robot.get_state().size
    assert [joint["index"] for joint in contract["joints"]] == sorted(
        joint.index for joint in kuka_robot.joints.values()
    )
    assert [link["index"] for link in contract["links"]] == sorted(
        link.index for link in kuka_robot.links.values()
    )
    controllable_count = sum(joint["controllable"] for joint in contract["joints"])
    assert controllable_count == contract["action"]["size"]
    assert all(len(joint["limits"]) == 2 for joint in contract["joints"])

    json.dumps(contract, allow_nan=False)
