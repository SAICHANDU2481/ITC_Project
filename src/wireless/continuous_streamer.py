"""
Continuous Wireless Source Streamer Module (Mode B).
Generates successive information frames and transmits them continuously over Wi-Fi/TCP,
with bounded memory queues, backpressure handling, throughput tracking,
and thread-safe graceful cancellation.
"""

from typing import Dict, Any, List, Optional
import threading
import queue
import time
from collections import deque
import numpy as np

from .frame_protocol import WirelessFrame, FrameType, StatusCode
from .network_transceiver import WirelessSender
from src.source_coding.saturated_source import SaturatedSource


class ContinuousSourceStreamer:
    """
    Continuous stream generator and wireless transmitter.
    Runs on a dedicated background thread with rate limiting and bounded queues.
    """

    def __init__(self, sender: Optional[WirelessSender] = None):
        self.sender = sender if sender is not None else WirelessSender()
        self.source = SaturatedSource(seed=42)

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Bounded frame queue to prevent memory explosion under network backpressure
        self.frame_queue: queue.Queue = queue.Queue(maxsize=50)

        # Metrics and counters
        self.frames_generated = 0
        self.frames_transmitted = 0
        self.frames_acknowledged = 0
        self.frames_failed = 0
        self.frames_dropped_backpressure = 0
        self.bytes_transmitted = 0
        self.start_time: Optional[float] = None
        self.recent_frames: deque = deque(maxlen=20)

    def start(
        self,
        dest_host: str = "127.0.0.1",
        dest_port: int = 8550,
        source_type: str = "telemetry",
        frame_size: int = 128,
        interval_sec: float = 0.5,
        use_source_coding: bool = True,
        source_codec: str = "arithmetic",
        use_ldpc: bool = True
    ) -> bool:
        """Start continuous transmission on background thread."""
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False  # Already streaming

            self._stop_event.clear()
            self.start_time = time.time()
            self._thread = threading.Thread(
                target=self._stream_loop,
                args=(
                    dest_host,
                    dest_port,
                    source_type,
                    frame_size,
                    interval_sec,
                    use_source_coding,
                    source_codec,
                    use_ldpc
                ),
                daemon=True
            )
            self._thread.start()
            return True

    def stop(self):
        """Signal streamer to stop and join thread."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _stream_loop(
        self,
        dest_host: str,
        dest_port: int,
        source_type: str,
        frame_size: int,
        interval_sec: float,
        use_source_coding: bool,
        source_codec: str,
        use_ldpc: bool
    ):
        pkt_index = 0
        while not self._stop_event.is_set():
            t_cycle_start = time.perf_counter()
            pkt_index += 1

            # 1. Generate payload
            if source_type == "telemetry":
                # Saturated telemetry string
                raw_text = self.source.generate_text_stream(num_packets=1)
                # Adjust to approximate frame_size
                if len(raw_text) > frame_size:
                    raw_text = raw_text[:frame_size]
                elif len(raw_text) < frame_size:
                    raw_text = raw_text + ("_" * (frame_size - len(raw_text)))
            else:
                # Random bits converted to hex string
                rand_bytes = self.source.rng.integers(0, 256, size=max(16, frame_size // 2), dtype=np.uint8).tobytes()
                raw_text = rand_bytes.hex()[:frame_size]

            # 2. Check queue backpressure
            with self._lock:
                self.frames_generated += 1
                if self.frame_queue.full():
                    self.frames_dropped_backpressure += 1
                    # Skip transmission for this cycle to handle backpressure
                    self._stop_event.wait(max(0.01, interval_sec))
                    continue

            # 3. Transmit frame via sender
            rep = self.sender.send_message(
                message=raw_text,
                host=dest_host,
                port=dest_port,
                use_source_coding=use_source_coding,
                source_codec=source_codec,
                use_ldpc=use_ldpc,
                timeout=max(1.0, interval_sec * 2.0)
            )

            with self._lock:
                self.frames_transmitted += 1
                self.bytes_transmitted += rep.get('coded_size_bytes', len(raw_text))

                if rep.get('ack_received', False) and rep.get('ack_status') == StatusCode.OK.name:
                    self.frames_acknowledged += 1
                else:
                    self.frames_failed += 1

                self.recent_frames.append({
                    'seq': rep['seq_num'],
                    'time': time.strftime("%H:%M:%S"),
                    'size': rep.get('orig_size_bytes', 0),
                    'coded_size': rep.get('coded_size_bytes', 0),
                    'status': rep.get('status', 'Unknown'),
                    'ack': rep.get('ack_status', 'FAIL'),
                    'rtt_ms': rep.get('round_trip_ms', 0.0)
                })

            # 4. Precise rate control
            elapsed = time.perf_counter() - t_cycle_start
            sleep_duration = max(0.01, interval_sec - elapsed)
            self._stop_event.wait(sleep_duration)

    def get_metrics(self) -> Dict[str, Any]:
        """Return snapshot of real-time stream metrics."""
        with self._lock:
            elapsed_sec = (time.time() - self.start_time) if self.start_time else 0.0
            throughput_bps = (self.bytes_transmitted * 8.0 / elapsed_sec) if elapsed_sec > 0 else 0.0
            throughput_fps = (self.frames_transmitted / elapsed_sec) if elapsed_sec > 0 else 0.0

            return {
                'is_running': self.is_running(),
                'elapsed_sec': elapsed_sec,
                'frames_generated': self.frames_generated,
                'frames_transmitted': self.frames_transmitted,
                'frames_acknowledged': self.frames_acknowledged,
                'frames_failed': self.frames_failed,
                'frames_dropped_backpressure': self.frames_dropped_backpressure,
                'bytes_transmitted': self.bytes_transmitted,
                'throughput_bps': throughput_bps,
                'throughput_fps': throughput_fps,
                'recent_frames': list(self.recent_frames)
            }

    def reset_counters(self):
        with self._lock:
            self.frames_generated = 0
            self.frames_transmitted = 0
            self.frames_acknowledged = 0
            self.frames_failed = 0
            self.frames_dropped_backpressure = 0
            self.bytes_transmitted = 0
            self.recent_frames.clear()
