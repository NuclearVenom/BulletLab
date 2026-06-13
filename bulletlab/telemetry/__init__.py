"""
BulletLab telemetry subpackage.

Provides TelemetryManager and TelemetryChannel for monitoring live robot state.
"""

from bulletlab.telemetry.manager import TelemetryManager
from bulletlab.telemetry.channel import TelemetryChannel

__all__ = ["TelemetryManager", "TelemetryChannel"]
