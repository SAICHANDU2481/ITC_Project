"""
Wireless Network Transceiver Module.
Implements WirelessSender and WirelessReceiver classes using standard Python sockets
over local Wi-Fi or loopback interfaces.
Integrates the complete Information Theory pipeline:
UTF-8 conversion -> Source Coding -> LDPC Channel Coding -> Framing -> Socket Transport
-> Channel Decoding -> Source Decoding -> Integrity Verification -> Exact Reconstruction.
"""

from typing import Dict, Any, List, Optional, Tuple
import socket
import threading
import time
import struct
import numpy as np

from .frame_protocol import WirelessFrame, FrameType, StatusCode, InvalidFrameError, ChecksumMismatchError
from src.source_coding.arithmetic_codec import ArithmeticCodec
from src.source_coding.lzw_codec import LZWCodec
from src.channel_coding.ldpc_codec import LDPCCodec


class WirelessSender:
    """
    Client-side wireless transmitter for Mode A (Live Message Transmission).
    Encodes text using Arithmetic/LZW source coding and LDPC FEC,
    serializes into CRC32-protected frames, transmits over TCP/IP,
    and awaits receiver acknowledgment with sequence number confirmation.
    """

    def __init__(self):
        self.seq_num = 1
        self.history: List[Dict[str, Any]] = []
        self.arithmetic_codec = ArithmeticCodec()
        self.lzw_codec = LZWCodec(bit_depth=12)
        self.ldpc_codec = LDPCCodec(n=64, k=32, max_iter=25, seed=42)
        self._lock = threading.Lock()

    def send_message(
        self,
        message: str,
        host: str = "127.0.0.1",
        port: int = 8550,
        use_source_coding: bool = True,
        source_codec: str = "arithmetic",
        use_ldpc: bool = True,
        timeout: float = 4.0
    ) -> Dict[str, Any]:
        """
        Transmit message through the complete wireless communication pipeline.
        
        Returns:
            Dict containing transmission metrics, sequence number, sizes,
            durations, and receiver acknowledgment details.
        """
        with self._lock:
            current_seq = self.seq_num
            self.seq_num += 1

        t0 = time.perf_counter()
        raw_bytes = message.encode("utf-8")
        orig_size = len(raw_bytes)

        flags = 0
        src_duration_ms = 0.0

        # Step 1: Source Coding
        if use_source_coding:
            t_src = time.perf_counter()
            if source_codec.lower() == "arithmetic":
                compressed_bytes, src_stats = self.arithmetic_codec.encode(message)
                flags |= WirelessFrame.FLAG_SOURCE_CODED | WirelessFrame.FLAG_ARITHMETIC
            else:
                # LZW
                comp_bits, src_stats = self.lzw_codec.encode(message)
                compressed_bytes = np.packbits(comp_bits).tobytes()
                flags |= WirelessFrame.FLAG_SOURCE_CODED | WirelessFrame.FLAG_LZW
            src_duration_ms = (time.perf_counter() - t_src) * 1000.0
            src_size = len(compressed_bytes)
        else:
            compressed_bytes = raw_bytes
            src_size = orig_size

        # Step 2: Channel Coding (LDPC)
        fec_duration_ms = 0.0
        if use_ldpc:
            t_fec = time.perf_counter()
            # Unpack compressed bytes into bit array for LDPC block segmentation
            comp_bits = np.unpackbits(np.frombuffer(compressed_bytes, dtype=np.uint8))
            tx_bits, pad_len = self.ldpc_codec.encode(comp_bits)
            # Store padding length in first 2 bytes of payload
            packed_fec = np.packbits(tx_bits).tobytes()
            payload = struct.pack(">H", pad_len) + packed_fec
            flags |= WirelessFrame.FLAG_LDPC_CODED
            fec_duration_ms = (time.perf_counter() - t_fec) * 1000.0
        else:
            payload = compressed_bytes

        coded_size = len(payload)

        # Step 3: Frame Construction
        frame = WirelessFrame(
            frame_type=FrameType.DATA,
            seq_num=current_seq,
            payload=payload,
            orig_size=orig_size,
            src_size=src_size,
            flags=flags
        )

        record: Dict[str, Any] = {
            'seq_num': current_seq,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'orig_text': message,
            'orig_size_bytes': orig_size,
            'src_size_bytes': src_size,
            'coded_size_bytes': coded_size,
            'compression_ratio': float(orig_size / max(src_size, 1)),
            'source_codec': source_codec if use_source_coding else "None",
            'ldpc_applied': use_ldpc,
            'src_duration_ms': src_duration_ms,
            'fec_duration_ms': fec_duration_ms,
            'destination': f"{host}:{port}",
            'status': "Sending...",
            'ack_received': False,
            'ack_status': "PENDING",
            'round_trip_ms': 0.0,
            'error_message': None
        }

        # Step 4: Network Transmission & Acknowledgment Loop
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            t_send = time.perf_counter()
            frame.send_to_socket(sock)

            # Await receiver acknowledgment
            ack_frame = WirelessFrame.read_from_socket(sock, timeout=timeout)
            rtt_ms = (time.perf_counter() - t_send) * 1000.0

            if ack_frame.frame_type != FrameType.ACK:
                raise ValueError(f"Expected ACK frame, got frame type {ack_frame.frame_type.name}")

            if ack_frame.seq_num != current_seq:
                raise ValueError(
                    f"Sequence number mismatch in ACK: expected #{current_seq}, got #{ack_frame.seq_num}"
                )

            record['ack_received'] = True
            record['ack_status'] = ack_frame.status.name
            record['round_trip_ms'] = rtt_ms

            if ack_frame.status == StatusCode.OK:
                record['status'] = "Delivered & Reconstructed (ACK OK)"
            else:
                record['status'] = f"Delivered with Receiver Error ({ack_frame.status.name})"

        except socket.timeout:
            record['status'] = "Connection Timeout"
            record['error_message'] = f"Timeout ({timeout}s) waiting for receiver at {host}:{port}"
        except ConnectionRefusedError:
            record['status'] = "Connection Refused"
            record['error_message'] = f"Receiver is not running or listening at {host}:{port}"
        except Exception as e:
            record['status'] = "Transmission Failed"
            record['error_message'] = str(e)
        finally:
            try:
                sock.close()
            except Exception:
                pass

        with self._lock:
            self.history.append(record)

        return record

    def clear_history(self):
        with self._lock:
            self.history.clear()


class WirelessReceiver:
    """
    Server-side wireless receiver for Mode A & Mode B.
    Runs on a background thread, accepts incoming connections, parses frames,
    performs checksum verification, runs LDPC and source decoding,
    reconstructs original messages, and sends acknowledgments.
    """
    _active_instance: Optional['WirelessReceiver'] = None

    def __init__(self, host: str = "0.0.0.0", port: int = 8550):
        self.host = host
        self.port = port
        self.history: List[Dict[str, Any]] = []
        self._server_sock: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running = False
        self._lock = threading.Lock()

        # Codecs for decoding
        self.arithmetic_codec = ArithmeticCodec()
        self.lzw_codec = LZWCodec(bit_depth=12)
        self.ldpc_codec = LDPCCodec(n=64, k=32, max_iter=25, seed=42)

        # Performance counters
        self.total_received = 0
        self.total_decoded_ok = 0
        self.total_errors = 0

    def start(self, host: Optional[str] = None, port: Optional[int] = None) -> bool:
        """Start the receiver background server."""
        if self._is_running:
            return True

        if host is not None:
            self.host = host
        if port is not None:
            self.port = port

        try:
            self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_sock.bind((self.host, self.port))
            self._server_sock.listen(10)
            self._server_sock.settimeout(0.5)  # Periodic wake-up to check _is_running
            self._is_running = True
            WirelessReceiver._active_instance = self

            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            return True
        except Exception as e:
            self._is_running = False
            if self._server_sock:
                try:
                    self._server_sock.close()
                except Exception:
                    pass
                self._server_sock = None
            raise e

    def stop(self):
        """Stop receiver server gracefully."""
        self._is_running = False
        if WirelessReceiver._active_instance is self:
            WirelessReceiver._active_instance = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.5)
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
            self._server_sock = None

    def is_running(self) -> bool:
        if self._is_running:
            return True
        active = WirelessReceiver._active_instance
        if active and active is not self:
            return active.is_running()
        return False

    def _listen_loop(self):
        """Background thread accepting client connections."""
        while self._is_running:
            try:
                client_sock, client_addr = self._server_sock.accept()
            except socket.timeout:
                continue
            except Exception:
                break

            # Handle each connection in separate worker or inline
            try:
                self._handle_client(client_sock, client_addr)
            except Exception:
                pass
            finally:
                try:
                    client_sock.close()
                except Exception:
                    pass

    def _handle_client(self, sock: socket.socket, addr: Tuple[str, int]):
        """Receive frame, decode, verify checksum, and reply with ACK."""
        t_proc_start = time.perf_counter()

        try:
            frame = WirelessFrame.read_from_socket(sock, timeout=4.0)
        except ChecksumMismatchError as e:
            # Send corrupted ACK
            with self._lock:
                self.total_received += 1
                self.total_errors += 1
                self.history.append({
                    'seq_num': -1,
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'sender': f"{addr[0]}:{addr[1]}",
                    'status': "Checksum Mismatch (Corrupt Frame)",
                    'status_code': StatusCode.CHECKSUM_ERROR.name,
                    'reconstructed_text': None,
                    'orig_size': 0,
                    'coded_size': 0,
                    'processing_duration_ms': (time.perf_counter() - t_proc_start) * 1000.0,
                    'checksum_verified': False
                })
            try:
                ack = WirelessFrame.create_ack(seq_num=0, status=StatusCode.CHECKSUM_ERROR)
                ack.send_to_socket(sock)
            except Exception:
                pass
            return
        except Exception as e:
            with self._lock:
                self.total_errors += 1
            return

        # Frame successfully received & CRC validated
        seq = frame.seq_num
        payload = frame.payload
        flags = frame.flags
        reconstructed_text = ""
        decode_status = StatusCode.OK
        status_msg = "Received & Decoded Successfully"

        try:
            # Step 1: LDPC Channel Decoding (if encoded)
            if flags & WirelessFrame.FLAG_LDPC_CODED:
                if len(payload) < 2:
                    raise ValueError("Malformed FEC payload: missing pad_len header.")
                pad_len = struct.unpack_from(">H", payload, 0)[0]
                fec_bits = np.unpackbits(np.frombuffer(payload[2:], dtype=np.uint8))
                
                # Slicer / hard decision decoding in noiseless socket environment
                dec_bits = self.ldpc_codec.decode(fec_bits, pad_len=pad_len, channel_type="lossless")
                comp_bytes = np.packbits(dec_bits).tobytes()
            else:
                comp_bytes = payload

            # Step 2: Source Decoding
            if flags & WirelessFrame.FLAG_SOURCE_CODED:
                if flags & WirelessFrame.FLAG_ARITHMETIC:
                    reconstructed_text = self.arithmetic_codec.decode(comp_bytes, return_as_string=True)
                elif flags & WirelessFrame.FLAG_LZW:
                    comp_bits = np.unpackbits(np.frombuffer(comp_bytes, dtype=np.uint8))
                    reconstructed_text = self.lzw_codec.decode(comp_bits, return_as_string=True)
                else:
                    reconstructed_text = comp_bytes.decode("utf-8", errors="replace")
            else:
                reconstructed_text = comp_bytes.decode("utf-8", errors="replace")

        except Exception as e:
            decode_status = StatusCode.DECODE_ERROR
            status_msg = f"Decoding Failed: {str(e)}"
            reconstructed_text = f"[DECODING_ERROR: {str(e)}]"

        duration_ms = (time.perf_counter() - t_proc_start) * 1000.0

        # Send ACK with status
        try:
            ack = WirelessFrame.create_ack(seq_num=seq, status=decode_status)
            ack.send_to_socket(sock)
        except Exception:
            pass

        # Record in history
        with self._lock:
            self.total_received += 1
            if decode_status == StatusCode.OK:
                self.total_decoded_ok += 1
            else:
                self.total_errors += 1

            self.history.append({
                'seq_num': seq,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'sender': f"{addr[0]}:{addr[1]}",
                'status': status_msg,
                'status_code': decode_status.name,
                'reconstructed_text': reconstructed_text,
                'orig_size': frame.orig_size,
                'coded_size': len(frame.payload),
                'processing_duration_ms': duration_ms,
                'checksum_verified': True
            })

    def get_history(self) -> List[Dict[str, Any]]:
        with self._lock:
            if not self.history and WirelessReceiver._active_instance and WirelessReceiver._active_instance is not self:
                return WirelessReceiver._active_instance.get_history()
            return list(self.history)

    def clear_history(self):
        with self._lock:
            self.history.clear()
            self.total_received = 0
            self.total_decoded_ok = 0
            self.total_errors = 0
        active = WirelessReceiver._active_instance
        if active and active is not self:
            active.clear_history()

    @property
    def display_total_received(self) -> int:
        if self.total_received > 0 or not WirelessReceiver._active_instance or WirelessReceiver._active_instance is self:
            return self.total_received
        return WirelessReceiver._active_instance.total_received

    @property
    def display_total_decoded_ok(self) -> int:
        if self.total_decoded_ok > 0 or not WirelessReceiver._active_instance or WirelessReceiver._active_instance is self:
            return self.total_decoded_ok
        return WirelessReceiver._active_instance.total_decoded_ok

    @property
    def display_total_errors(self) -> int:
        if self.total_errors > 0 or not WirelessReceiver._active_instance or WirelessReceiver._active_instance is self:
            return self.total_errors
        return WirelessReceiver._active_instance.total_errors
