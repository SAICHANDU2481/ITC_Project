"""
End-to-End Digital Communication Pipeline Orchestrator.
Connects Information Source -> Binary Representation -> Source Encoder ->
Channel Encoder -> Wired Channel -> Channel Decoder -> Source Decoder ->
Reconstruction -> Performance Metrics Evaluation.
"""

from typing import Dict, Any, Optional, Union
import numpy as np
import time

from ..source_coding import SaturatedSource, BinaryConverter, LZWCodec
from ..channel_coding import ChannelCodec, LDPCCodec, PolarCodec, HammingCodec
from ..channel_model import WiredChannel, ChannelAnalyzer
from ..metrics import PerformanceEvaluator


class CommunicationPipeline:
    """
    Simulates the complete transmitter-to-receiver wired communication pipeline.
    """

    def __init__(
        self,
        channel_codec: Optional[ChannelCodec] = None,
        use_source_coding: bool = True,
        lzw_bit_depth: int = 12,
        seed: Optional[int] = 42
    ):
        self.channel_codec = channel_codec
        self.use_source_coding = use_source_coding
        self.lzw_codec = LZWCodec(bit_depth=lzw_bit_depth) if use_source_coding else None
        self.channel = WiredChannel(seed=seed)
        self.source = SaturatedSource(seed=seed)
        self.seed = seed

    def run_single_transmission(
        self,
        input_data: Union[str, np.ndarray],
        channel_mode: str = "awgn",
        channel_param: float = 4.0,  # Eb/N0 in dB if awgn, p if bsc
        source_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Execute a single end-to-end transmission cycle.
        """
        start_time = time.perf_counter()

        # Step 1: Input source representation
        if isinstance(input_data, str):
            original_text = input_data
            raw_bits = BinaryConverter.text_to_bits(input_data)
        else:
            original_text = ""
            raw_bits = np.asarray(input_data, dtype=np.uint8).flatten()

        # Step 2: Source Coding
        source_stats = {}
        if self.use_source_coding and self.lzw_codec is not None:
            if original_text:
                source_encoded_bits, source_stats = self.lzw_codec.encode(original_text)
            else:
                # Encode binary array by packing into bytes
                packed = np.packbits(raw_bits).tobytes()
                source_encoded_bits, source_stats = self.lzw_codec.encode(packed)
        else:
            source_encoded_bits = raw_bits.copy()
            source_stats = {
                'raw_bits': len(raw_bits),
                'compressed_bits': len(raw_bits),
                'compression_ratio': 1.0,
                'space_saving_pct': 0.0
            }

        # Step 3: Channel Encoding
        pad_len = 0
        if self.channel_codec is not None:
            tx_bits, pad_len = self.channel_codec.encode(source_encoded_bits)
            code_rate = self.channel_codec.rate
        else:
            tx_bits = source_encoded_bits.copy()
            code_rate = 1.0

        # Step 4: Wired Channel Transmission
        channel_mode = channel_mode.lower()
        if channel_mode == "lossless":
            rx_hard, rx_llrs = self.channel.transmit_lossless(tx_bits)
            channel_info = {'mode': 'lossless'}
        elif channel_mode == "bsc":
            p = float(channel_param)
            rx_hard, rx_llrs = self.channel.transmit_bsc(tx_bits, p=p)
            channel_info = {'mode': 'bsc', 'p': p}
        elif channel_mode == "awgn":
            eb_no_db = float(channel_param)
            rx_hard, rx_soft, rx_llrs, sigma = self.channel.transmit_awgn(
                tx_bits, eb_no_db=eb_no_db, code_rate=code_rate
            )
            channel_info = {'mode': 'awgn', 'eb_no_db': eb_no_db, 'sigma': sigma}
        else:
            raise ValueError(f"Unknown channel mode: {channel_mode}")

        # Measure Pre-FEC Channel BER (slicer output vs transmitted bits)
        pre_fec_eval = PerformanceEvaluator.calculate_ber(tx_bits, rx_hard)

        # Step 5: Channel Decoding
        if self.channel_codec is not None:
            if channel_mode == "awgn":
                decoded_source_bits = self.channel_codec.decode(
                    rx_soft, pad_len=pad_len, channel_type="awgn", sigma=channel_info.get('sigma', 0.5)
                )
            elif channel_mode == "bsc":
                decoded_source_bits = self.channel_codec.decode(
                    rx_llrs, pad_len=pad_len, channel_type="bsc", p=channel_info.get('p', 0.05)
                )
            else:
                decoded_source_bits = self.channel_codec.decode(
                    rx_llrs, pad_len=pad_len, channel_type="lossless"
                )
        else:
            decoded_source_bits = rx_hard.copy()

        # Measure Post-FEC Channel BER (decoded source bits vs original source_encoded_bits)
        post_fec_eval = PerformanceEvaluator.calculate_ber(source_encoded_bits, decoded_source_bits)

        # Step 6: Source Decoding & Reconstruction
        reconstructed_text = ""
        reconstructed_raw_bits = decoded_source_bits.copy()

        if self.use_source_coding and self.lzw_codec is not None:
            try:
                if original_text:
                    reconstructed_text = self.lzw_codec.decode(decoded_source_bits, return_as_string=True)
                else:
                    dec_bytes = self.lzw_codec.decode(decoded_source_bits, return_as_string=False)
                    reconstructed_raw_bits = np.unpackbits(np.frombuffer(dec_bytes, dtype=np.uint8))[:len(raw_bits)]
            except Exception as e:
                reconstructed_text = f"[SOURCE_DECODE_ERROR: {str(e)}]"
        else:
            if original_text:
                reconstructed_text = BinaryConverter.bits_to_text(decoded_source_bits)

        # Step 7: End-to-End Fidelity Evaluation
        if original_text:
            end_to_end_eval = PerformanceEvaluator.calculate_reconstruction_accuracy(
                original_text, reconstructed_text
            )
        else:
            end_to_end_eval = PerformanceEvaluator.calculate_ber(raw_bits, reconstructed_raw_bits)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            'original_input_excerpt': original_text[:80] if original_text else f"{len(raw_bits)} bits",
            'reconstructed_output_excerpt': reconstructed_text[:80] if reconstructed_text else f"{len(reconstructed_raw_bits)} bits",
            'exact_recovery': end_to_end_eval.get('exact_match', False),
            'source_stats': source_stats,
            'tx_bits_count': len(tx_bits),
            'pre_fec_errors': pre_fec_eval['bit_errors'],
            'pre_fec_ber': pre_fec_eval['ber'],
            'post_fec_errors': post_fec_eval['bit_errors'],
            'post_fec_ber': post_fec_eval['ber'],
            'post_fec_zero_errors': post_fec_eval['zero_error_observed'],
            'end_to_end_eval': end_to_end_eval,
            'channel_info': channel_info,
            'codec_name': self.channel_codec.name if self.channel_codec else "Uncoded",
            'elapsed_ms': elapsed_ms
        }
