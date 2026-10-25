"""
Integration tests for WirelessSender and WirelessReceiver.
Includes the required end-to-end integration test:
"Hello, this is my wireless ITC project!"
Verifies encoding, LDPC framing, socket transmission, exact reconstruction,
sequence number preservation, checksum verification, and ACK loop.
"""

import pytest
import time
from src.wireless.network_transceiver import WirelessSender, WirelessReceiver
from src.wireless.frame_protocol import StatusCode


def test_required_integration_test_hello_wireless():
    """
    REQUIRED INTEGRATION TEST:
    Original message: "Hello, this is my wireless ITC project!"
    Verify:
    1. Message is encoded.
    2. LDPC encoding succeeds.
    3. Complete frame is created.
    4. Receiver obtains the frame over socket.
    5. Receiver decodes it.
    6. Original text is reconstructed exactly.
    7. Sequence number is preserved.
    8. Checksum passes.
    9. Receiver acknowledges the correct sequence number.
    """
    test_port = 8555
    receiver = WirelessReceiver(host="127.0.0.1", port=test_port)
    assert receiver.start() is True

    try:
        sender = WirelessSender()
        test_message = "Hello, this is my wireless ITC project!"

        # Transmit with Arithmetic coding + LDPC FEC
        report = sender.send_message(
            message=test_message,
            host="127.0.0.1",
            port=test_port,
            use_source_coding=True,
            source_codec="arithmetic",
            use_ldpc=True,
            timeout=3.0
        )

        # 1. Sender report checks
        assert report['orig_text'] == test_message
        assert report['orig_size_bytes'] == len(test_message.encode('utf-8'))
        assert report['ldpc_applied'] is True
        assert report['seq_num'] == 1
        assert report['ack_received'] is True
        assert report['ack_status'] == StatusCode.OK.name
        assert "Delivered" in report['status']
        assert report['error_message'] is None

        # Give receiver event loop a brief moment to finish updating history
        time.sleep(0.1)

        # 2. Receiver history checks
        history = receiver.get_history()
        assert len(history) == 1
        rx_item = history[0]

        assert rx_item['seq_num'] == 1
        assert rx_item['checksum_verified'] is True
        assert rx_item['status_code'] == StatusCode.OK.name
        assert rx_item['reconstructed_text'] == test_message  # Exact reconstruction!
        assert rx_item['orig_size'] == len(test_message.encode('utf-8'))

    finally:
        receiver.stop()


def test_sender_receiver_lzw_and_unicode():
    test_port = 8556
    receiver = WirelessReceiver(host="127.0.0.1", port=test_port)
    receiver.start()

    try:
        sender = WirelessSender()
        msg = "WIRELESS_NODE_PACKET: TEMP=32.4C, VOLT=3.3V, STATUS=OK 📡"
        
        # Test with LZW + LDPC
        rep = sender.send_message(
            message=msg,
            host="127.0.0.1",
            port=test_port,
            use_source_coding=True,
            source_codec="lzw",
            use_ldpc=True,
            timeout=3.0
        )
        assert rep['ack_received'] is True
        assert rep['ack_status'] == StatusCode.OK.name

        time.sleep(0.1)
        history = receiver.get_history()
        assert len(history) == 1
        assert history[0]['reconstructed_text'] == msg

    finally:
        receiver.stop()


def test_multiple_messages_sequence_numbers():
    test_port = 8557
    receiver = WirelessReceiver(host="127.0.0.1", port=test_port)
    receiver.start()

    try:
        sender = WirelessSender()
        messages = [
            "Packet 1: Initialization",
            "Packet 2: Telemetry Stream Payload",
            "Packet 3: Final Acknowledgement"
        ]

        for i, m in enumerate(messages):
            rep = sender.send_message(m, host="127.0.0.1", port=test_port, use_ldpc=True)
            assert rep['seq_num'] == i + 1
            assert rep['ack_received'] is True

        time.sleep(0.1)
        history = receiver.get_history()
        assert len(history) == 3
        for i, m in enumerate(messages):
            assert history[i]['seq_num'] == i + 1
            assert history[i]['reconstructed_text'] == m

    finally:
        receiver.stop()


def test_sender_connection_refused_error_handling():
    sender = WirelessSender()
    # Try sending to an unallocated port where no receiver is listening
    rep = sender.send_message(
        message="Will fail gracefully",
        host="127.0.0.1",
        port=9999,
        timeout=1.0
    )
    assert rep['ack_received'] is False
    assert "Refused" in rep['status'] or "Failed" in rep['status'] or "Timeout" in rep['status']
    assert rep['error_message'] is not None
