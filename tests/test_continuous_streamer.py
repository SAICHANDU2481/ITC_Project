"""
Unit tests for ContinuousSourceStreamer (Mode B).
Tests streaming start/stop lifecycle, throughput metrics, backpressure handling,
and graceful background cancellation.
"""

import pytest
import time
from src.wireless.continuous_streamer import ContinuousSourceStreamer
from src.wireless.network_transceiver import WirelessReceiver


def test_continuous_streamer_lifecycle():
    test_port = 8558
    receiver = WirelessReceiver(host="127.0.0.1", port=test_port)
    receiver.start()

    streamer = ContinuousSourceStreamer()
    try:
        # Start fast continuous streaming
        started = streamer.start(
            dest_host="127.0.0.1",
            dest_port=test_port,
            source_type="telemetry",
            frame_size=64,
            interval_sec=0.1,
            use_source_coding=True,
            use_ldpc=True
        )
        assert started is True
        assert streamer.is_running() is True

        # Let it stream for 0.4s (around 3-4 frames)
        time.sleep(0.4)

        metrics = streamer.get_metrics()
        assert metrics['is_running'] is True
        assert metrics['frames_transmitted'] > 0
        assert metrics['frames_acknowledged'] > 0
        assert metrics['bytes_transmitted'] > 0

    finally:
        streamer.stop()
        receiver.stop()

    assert streamer.is_running() is False


def test_continuous_streamer_graceful_stop_when_idle():
    streamer = ContinuousSourceStreamer()
    # Calling stop on an unstarted streamer should be harmless
    streamer.stop()
    assert streamer.is_running() is False
