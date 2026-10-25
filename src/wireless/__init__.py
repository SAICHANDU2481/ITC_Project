"""
Wireless Communication System Package.
Contains frame protocol, socket networking, continuous transmission,
and wireless channel simulation modules.
"""

from .frame_protocol import (
    WirelessFrame,
    FrameType,
    StatusCode,
    InvalidFrameError,
    ChecksumMismatchError
)
from .network_transceiver import WirelessSender, WirelessReceiver
from .continuous_streamer import ContinuousSourceStreamer
from .channel_sim import WirelessPhysicalChannel, WirelessSimulationPipeline

__all__ = [
    "WirelessFrame",
    "FrameType",
    "StatusCode",
    "InvalidFrameError",
    "ChecksumMismatchError",
    "WirelessSender",
    "WirelessReceiver",
    "ContinuousSourceStreamer",
    "WirelessPhysicalChannel",
    "WirelessSimulationPipeline"
]
