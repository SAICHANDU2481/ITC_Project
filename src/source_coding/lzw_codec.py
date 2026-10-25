"""
Modern LZW (Lempel-Ziv-Welch) Dictionary Source Encoder and Decoder.
Implements universal dictionary source coding as introduced by Welch (1984)
and widely applied in modern wireline network protocols.
Eliminates static frequency tables required by Huffman or Shannon-Fano coding.
"""

from typing import List, Tuple, Union, Optional
import numpy as np
from .binary_converter import BinaryConverter


class LZWCodec:
    """
    Adaptive LZW Source Encoder and Decoder.
    Maps variable-length symbol sequences to fixed-width binary codewords.
    """

    def __init__(self, bit_depth: int = 12):
        """
        Args:
            bit_depth: Width of each output codeword in bits (default: 12 bits -> 4096 code dictionary).
        """
        self.bit_depth = bit_depth
        self.max_table_size = 1 << bit_depth

    def encode(self, data: Union[str, bytes]) -> Tuple[np.ndarray, dict]:
        """
        Encode raw string or byte sequence into binary bitstream using LZW.
        Returns:
            encoded_bits: np.ndarray of uint8 binary bits.
            stats: Dictionary containing compression statistics.
        """
        if isinstance(data, str):
            raw_bytes = data.encode('utf-8')
        else:
            raw_bytes = bytes(data)

        if len(raw_bytes) == 0:
            return np.array([], dtype=np.uint8), {
                'raw_bytes': 0,
                'raw_bits': 0,
                'compressed_bits': 0,
                'compression_ratio': 1.0,
                'space_saving_pct': 0.0,
                'num_codes': 0
            }

        # Initialize dictionary with all 256 single byte values
        dictionary = {bytes([i]): i for i in range(256)}
        next_code = 256

        compressed_codes: List[int] = []
        current = bytes()

        for byte_val in raw_bytes:
            current_plus_byte = current + bytes([byte_val])
            if current_plus_byte in dictionary:
                current = current_plus_byte
            else:
                compressed_codes.append(dictionary[current])
                if next_code < self.max_table_size:
                    dictionary[current_plus_byte] = next_code
                    next_code += 1
                current = bytes([byte_val])

        if current:
            compressed_codes.append(dictionary[current])

        # Serialize codes to binary array
        encoded_bits = BinaryConverter.ints_to_bits(compressed_codes, bit_depth=self.bit_depth)

        raw_bits = len(raw_bytes) * 8
        compressed_bits = len(encoded_bits)
        cr = (raw_bits / compressed_bits) if compressed_bits > 0 else 1.0
        saving = (1.0 - compressed_bits / raw_bits) * 100.0 if raw_bits > 0 else 0.0

        stats = {
            'raw_bytes': len(raw_bytes),
            'raw_bits': raw_bits,
            'compressed_bits': compressed_bits,
            'compression_ratio': float(cr),
            'space_saving_pct': float(saving),
            'num_codes': len(compressed_codes),
            'bit_depth': self.bit_depth,
            'dictionary_entries_used': next_code
        }

        return encoded_bits, stats

    def decode(self, bits: np.ndarray, return_as_string: bool = True) -> Union[str, bytes]:
        """
        Decode a binary bitstream back into the original reconstructed string or bytes.
        Handles the classic LZW decoder edge condition (cScSc).
        """
        if len(bits) == 0:
            return "" if return_as_string else b""

        codes = BinaryConverter.bits_to_ints(bits, bit_depth=self.bit_depth)
        if not codes:
            return "" if return_as_string else b""

        # Initialize dictionary with 256 single-byte entries
        dictionary = {i: bytes([i]) for i in range(256)}
        next_code = 256

        # Process first code
        prev_code = codes[0]
        if prev_code not in dictionary:
            raise ValueError(f"Corrupted LZW stream: initial code {prev_code} not in base dictionary.")

        decompressed = bytearray(dictionary[prev_code])
        prev_entry = dictionary[prev_code]

        for code in codes[1:]:
            if code in dictionary:
                entry = dictionary[code]
            elif code == next_code:
                # Classic LZW edge case: entry = prev_entry + prev_entry[0:1]
                entry = prev_entry + prev_entry[:1]
            else:
                # Bit errors in channel flipped code to invalid dictionary entry
                # Graceful recovery: substitute fallback single byte
                entry = bytes([code & 0xFF])

            decompressed.extend(entry)

            if next_code < self.max_table_size:
                dictionary[next_code] = prev_entry + entry[:1]
                next_code += 1

            prev_entry = entry

        out_bytes = bytes(decompressed)
        if return_as_string:
            return out_bytes.decode('utf-8', errors='replace')
        return out_bytes
