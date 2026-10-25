"""
Arithmetic Source Codec Module.
Implements a lossless Arithmetic / Range coder for arbitrary byte sequences and UTF-8 text.
Provides entropy-approaching lossless data compression with exact round-trip reconstruction,
arbitrary length support, explicit metadata tracking, and malformed stream detection.
"""

from typing import Tuple, Dict, Any, Union, Optional
import time
import struct
import numpy as np


class ArithmeticCodec:
    """
    Finite-precision integer-based Arithmetic / Range Codec.
    Uses 32-bit integer register arithmetic to guarantee reproducible, platform-independent,
    lossless compression without floating-point rounding errors.
    
    Model: Static byte frequency model with 1-byte frequency table header, or uniform fallback.
    Supports: UTF-8 strings, raw bytes, and numpy bit arrays.
    """

    # 32-bit register bounds
    PRECISION = 32
    WHOLE = 1 << PRECISION
    HALF = WHOLE >> 1
    QUARTER = HALF >> 1
    THREE_QUARTER = HALF + QUARTER
    MAX_CODE = WHOLE - 1

    def __init__(self):
        pass

    @staticmethod
    def _build_frequencies(data: bytes) -> Tuple[np.ndarray, np.ndarray, int]:
        """
        Compute byte frequencies and cumulative distribution.
        Uses Laplace smoothing (add-1) so every byte in [0, 255] has non-zero probability.
        """
        counts = np.ones(257, dtype=np.uint64)  # 256 byte values + 1 EOF symbol (index 256)
        if len(data) > 0:
            byte_counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
            counts[:256] += byte_counts.astype(np.uint64)
        
        # Cumulative frequencies
        cum_freq = np.zeros(258, dtype=np.uint64)
        np.cumsum(counts, out=cum_freq[1:])
        total = int(cum_freq[-1])
        return counts, cum_freq, total

    def encode(self, input_data: Union[str, bytes, bytearray, np.ndarray]) -> Tuple[bytes, Dict[str, Any]]:
        """
        Compress input data into an arithmetic-coded byte stream.
        
        Args:
            input_data: Text string, bytes, or binary bit array.
            
        Returns:
            compressed_bytes: Complete self-contained serialized compressed byte string.
            stats: Dictionary containing compression metrics, durations, and sizes.
        """
        t0 = time.perf_counter()

        # Convert to raw bytes
        if isinstance(input_data, str):
            raw_bytes = input_data.encode("utf-8")
        elif isinstance(input_data, (bytes, bytearray)):
            raw_bytes = bytes(input_data)
        elif isinstance(input_data, np.ndarray):
            raw_bits = np.asarray(input_data, dtype=np.uint8).flatten()
            raw_bytes = np.packbits(raw_bits).tobytes()
        else:
            raise TypeError(f"Unsupported input type for ArithmeticCodec: {type(input_data)}")

        raw_size = len(raw_bytes)

        # Handle empty payload
        if raw_size == 0:
            duration = time.perf_counter() - t0
            header = struct.pack(">4sII", b"ARTH", 0, 0)
            return header, {
                'raw_bytes': 0,
                'compressed_bytes': len(header),
                'compression_ratio': 0.0,
                'space_saving_pct': 0.0,
                'encoding_duration_ms': duration * 1000.0,
                'entropy_bits_per_symbol': 0.0,
                'metadata_overhead_bytes': len(header)
            }

        # Calculate empirical entropy
        counts_raw = np.bincount(np.frombuffer(raw_bytes, dtype=np.uint8), minlength=256)
        p = counts_raw[counts_raw > 0] / raw_size
        entropy = float(-np.sum(p * np.log2(p)))

        # Build frequency model with compact presence bitmap
        byte_counts = np.bincount(np.frombuffer(raw_bytes, dtype=np.uint8), minlength=256)
        active_symbols = np.where(byte_counts > 0)[0]

        counts = np.ones(257, dtype=np.uint64)
        for sym in active_symbols:
            counts[sym] = 1 + int(min(byte_counts[sym], 65535))

        cum_freq = np.zeros(258, dtype=np.uint64)
        np.cumsum(counts, out=cum_freq[1:])
        total = int(cum_freq[-1])

        # Serialize 32-byte presence bitmap + 2 bytes per active symbol
        presence_bitmap = bytearray(32)
        freq_table_bytes = bytearray()
        for sym in active_symbols:
            presence_bitmap[sym >> 3] |= (1 << (sym & 7))
            freq_table_bytes.extend(struct.pack(">H", int(counts[sym] - 1)))

        # Arithmetic encoding loop
        low = 0
        high = self.MAX_CODE
        underflow_bits = 0
        output_bit_buffer = []

        def output_bit(b: int):
            output_bit_buffer.append(b)

        # Encode symbols (including 256 as explicit EOF)
        symbols_to_encode = list(raw_bytes) + [256]

        for symbol in symbols_to_encode:
            sym_low = int(cum_freq[symbol])
            sym_high = int(cum_freq[symbol + 1])
            range_val = high - low + 1

            # Update interval
            high = low + (range_val * sym_high // total) - 1
            low = low + (range_val * sym_low // total)

            # Rescaling / Renormalization
            while True:
                if high < self.HALF:
                    output_bit(0)
                    for _ in range(underflow_bits):
                        output_bit(1)
                    underflow_bits = 0
                    low = low << 1
                    high = (high << 1) | 1
                elif low >= self.HALF:
                    output_bit(1)
                    for _ in range(underflow_bits):
                        output_bit(0)
                    underflow_bits = 0
                    low = (low - self.HALF) << 1
                    high = ((high - self.HALF) << 1) | 1
                elif low >= self.QUARTER and high < self.THREE_QUARTER:
                    underflow_bits += 1
                    low = (low - self.QUARTER) << 1
                    high = ((high - self.QUARTER) << 1) | 1
                else:
                    break

        # Flush final bits
        underflow_bits += 1
        if low < self.QUARTER:
            output_bit(0)
            for _ in range(underflow_bits):
                output_bit(1)
        else:
            output_bit(1)
            for _ in range(underflow_bits):
                output_bit(0)

        # Pack bit stream into bytes
        bit_array = np.array(output_bit_buffer, dtype=np.uint8)
        packed_payload = np.packbits(bit_array).tobytes()
        num_stream_bits = len(output_bit_buffer)

        # Frame structure:
        # [Magic: 4B "ARTH"][Original Size: 4B][Num Stream Bits: 4B][Bitmap: 32B][Active Freqs: 2B*N][Packed Stream]
        header = struct.pack(">4sII", b"ARTH", raw_size, num_stream_bits)
        compressed_bytes = header + bytes(presence_bitmap) + bytes(freq_table_bytes) + packed_payload

        duration = time.perf_counter() - t0
        comp_size = len(compressed_bytes)
        cr = float(raw_size / comp_size) if comp_size > 0 else 0.0
        saving = float((raw_size - comp_size) / raw_size * 100.0) if raw_size > 0 else 0.0
        meta_overhead = len(header) + len(presence_bitmap) + len(freq_table_bytes)

        stats = {
            'raw_bytes': raw_size,
            'compressed_bytes': comp_size,
            'compression_ratio': cr,
            'space_saving_pct': saving,
            'encoding_duration_ms': duration * 1000.0,
            'entropy_bits_per_symbol': entropy,
            'metadata_overhead_bytes': meta_overhead
        }
        return compressed_bytes, stats

    def decode(self, compressed_bytes: bytes, return_as_string: bool = True) -> Union[str, bytes]:
        """
        Decompress an arithmetic-coded byte stream.
        
        Args:
            compressed_bytes: The byte stream produced by encode().
            return_as_string: If True, decode to UTF-8 str; if False, return raw bytes.
            
        Returns:
            Reconstructed string or bytes.
        """
        t0 = time.perf_counter()

        if len(compressed_bytes) < 12:
            raise ValueError("Malformed arithmetic coded stream: header too short.")

        magic, raw_size, num_stream_bits = struct.unpack_from(">4sII", compressed_bytes, 0)
        if magic != b"ARTH":
            raise ValueError(f"Invalid arithmetic stream magic bytes: {magic}")

        if raw_size == 0:
            return "" if return_as_string else b""

        if len(compressed_bytes) < 44:  # 12 header + 32 bitmap
            raise ValueError("Malformed arithmetic coded stream: truncated presence bitmap.")

        bitmap = compressed_bytes[12:44]
        active_symbols = []
        for sym in range(256):
            if bitmap[sym >> 3] & (1 << (sym & 7)):
                active_symbols.append(sym)

        table_len = len(active_symbols) * 2
        table_offset = 44
        if len(compressed_bytes) < table_offset + table_len:
            raise ValueError("Malformed stream: truncated frequency table.")

        counts = np.ones(257, dtype=np.uint64)
        for i, sym in enumerate(active_symbols):
            c_val = struct.unpack_from(">H", compressed_bytes, table_offset + i * 2)[0]
            counts[sym] = 1 + c_val
        counts[256] = 1  # EOF symbol count

        # Cumulative frequencies
        cum_freq = np.zeros(258, dtype=np.uint64)
        np.cumsum(counts, out=cum_freq[1:])
        total = int(cum_freq[-1])

        # Extract packed bitstream
        stream_offset = table_offset + table_len
        packed_payload = compressed_bytes[stream_offset:]
        if len(packed_payload) * 8 < num_stream_bits:
            raise ValueError("Malformed stream: compressed bitstream length mismatch.")

        unpacked_bits = np.unpackbits(np.frombuffer(packed_payload, dtype=np.uint8))[:num_stream_bits]

        # Decoder state
        bit_idx = 0
        def read_bit() -> int:
            nonlocal bit_idx
            if bit_idx < len(unpacked_bits):
                b = int(unpacked_bits[bit_idx])
                bit_idx += 1
                return b
            return 0

        # Prime the code register with first 32 bits
        code = 0
        for _ in range(self.PRECISION):
            code = (code << 1) | read_bit()

        low = 0
        high = self.MAX_CODE
        decoded_bytes = bytearray()

        while len(decoded_bytes) < raw_size:
            range_val = high - low + 1
            # Current scaled cumulative frequency
            scaled_value = ((code - low + 1) * total - 1) // range_val

            # Binary search to identify symbol
            # cum_freq[sym] <= scaled_value < cum_freq[sym+1]
            symbol = int(np.searchsorted(cum_freq, scaled_value, side='right') - 1)
            symbol = max(0, min(256, symbol))

            if symbol == 256:
                # Reached EOF symbol
                break

            decoded_bytes.append(symbol)

            # Update interval
            sym_low = int(cum_freq[symbol])
            sym_high = int(cum_freq[symbol + 1])
            high = low + (range_val * sym_high // total) - 1
            low = low + (range_val * sym_low // total)

            # Renormalization
            while True:
                if high < self.HALF:
                    low = low << 1
                    high = (high << 1) | 1
                    code = ((code << 1) | read_bit()) & self.MAX_CODE
                elif low >= self.HALF:
                    low = (low - self.HALF) << 1
                    high = ((high - self.HALF) << 1) | 1
                    code = (((code - self.HALF) << 1) | read_bit()) & self.MAX_CODE
                elif low >= self.QUARTER and high < self.THREE_QUARTER:
                    low = (low - self.QUARTER) << 1
                    high = ((high - self.QUARTER) << 1) | 1
                    code = (((code - self.QUARTER) << 1) | read_bit()) & self.MAX_CODE
                else:
                    break

        if len(decoded_bytes) != raw_size:
            raise ValueError(f"Arithmetic decoding size mismatch: expected {raw_size} bytes, got {len(decoded_bytes)}.")

        result = bytes(decoded_bytes)
        if return_as_string:
            return result.decode("utf-8", errors="replace")
        return result
