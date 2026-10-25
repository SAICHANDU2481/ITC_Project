"""
Binary Source Representation and Serialization Utilities.
Converts text, byte streams, and integer sequences into binary representations
and back with zero loss.
"""

from typing import Union, List
import numpy as np


class BinaryConverter:
    """
    Handles robust conversion between raw information symbols and binary vectors.
    """

    @staticmethod
    def text_to_bits(text: str) -> np.ndarray:
        """
        Convert string to a 1D NumPy array of binary bits (uint8) using UTF-8 encoding.
        Each character byte is converted to 8 bits MSB first.
        """
        raw_bytes = text.encode('utf-8')
        byte_array = np.frombuffer(raw_bytes, dtype=np.uint8)
        # Unpack bits: shape (N * 8,)
        bits = np.unpackbits(byte_array)
        return bits.astype(np.uint8)

    @staticmethod
    def bits_to_text(bits: np.ndarray) -> str:
        """
        Convert a 1D binary array of bits back to string.
        Truncates extra padding bits to the nearest 8-bit boundary.
        """
        bits = np.asarray(bits, dtype=np.uint8).flatten()
        # Ensure length is multiple of 8
        valid_len = (len(bits) // 8) * 8
        if valid_len == 0:
            return ""
        trimmed_bits = bits[:valid_len]
        packed_bytes = np.packbits(trimmed_bits)
        return bytes(packed_bytes).decode('utf-8', errors='replace')

    @staticmethod
    def ints_to_bits(integers: List[int], bit_depth: int = 12) -> np.ndarray:
        """
        Convert a sequence of integers (e.g. LZW indices) into a binary bitstream
        where each integer is represented by exactly `bit_depth` bits.
        """
        total_bits = len(integers) * bit_depth
        bits = np.zeros(total_bits, dtype=np.uint8)
        for idx, val in enumerate(integers):
            offset = idx * bit_depth
            for b in range(bit_depth):
                # MSB first
                bits[offset + b] = (val >> (bit_depth - 1 - b)) & 1
        return bits

    @staticmethod
    def bits_to_ints(bits: np.ndarray, bit_depth: int = 12) -> List[int]:
        """
        Convert a binary bitstream back into a list of integers of width `bit_depth`.
        """
        bits = np.asarray(bits, dtype=np.uint8).flatten()
        num_ints = len(bits) // bit_depth
        integers = []
        for idx in range(num_ints):
            offset = idx * bit_depth
            val = 0
            for b in range(bit_depth):
                val = (val << 1) | int(bits[offset + b])
            integers.append(val)
        return integers
