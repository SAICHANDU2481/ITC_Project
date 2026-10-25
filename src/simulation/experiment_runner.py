"""
Experimental Evaluation and Monte Carlo Simulation Suite.
Executes multi-condition channel sweeps across:
1. AWGN wired link Eb/N0 sweep (0 to 10 dB) comparing Uncoded, Hamming(7,4), Polar(64,32), and LDPC(64,32).
2. BSC bit-flip probability sweep (0.0001 to 0.15).
3. Saturated source compression study and lossless channel recovery verification.
Saves measured empirical data to CSV and generates publication-grade plots.
"""

import os
import csv
import time
from typing import Dict, List, Any
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ..source_coding import SaturatedSource, BinaryConverter, LZWCodec
from ..channel_coding import LDPCCodec, PolarCodec, HammingCodec
from ..channel_model import WiredChannel, ChannelAnalyzer
from ..metrics import PerformanceEvaluator


class ExperimentRunner:
    """
    Manages automated Monte Carlo simulations and figures generation.
    """

    def __init__(self, output_dir: str = "results", seed: int = 42):
        self.output_dir = output_dir
        self.csv_dir = os.path.join(output_dir, "csv")
        self.plots_dir = os.path.join(output_dir, "plots")
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.plots_dir, exist_ok=True)
        self.seed = seed

    def run_awgn_experiment(
        self,
        eb_no_range: List[float] = None,
        bits_per_point: int = 20480,
        seed: int = 42
    ) -> str:
        """
        Sweep Eb/N0 over wired AWGN channel.
        Compares:
        1. Theoretical Uncoded BPSK
        2. Simulated Uncoded BPSK
        3. Systematic Hamming (7, 4)
        4. Systematic Polar (64, 32) SC
        5. Systematic LDPC (64, 32) Sum-Product
        6. Systematic LDPC (64, 32) Min-Sum
        """
        if eb_no_range is None:
            eb_no_range = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        print(f"\n[EXPERIMENT 1] Running AWGN Eb/N0 Sweep ({min(eb_no_range)} to {max(eb_no_range)} dB, {bits_per_point} bits/point)...")

        # Initialize codecs
        ldpc_sp = LDPCCodec(n=64, k=32, max_iter=25, algorithm="sum_product", seed=seed)
        ldpc_ms = LDPCCodec(n=64, k=32, max_iter=25, algorithm="min_sum", seed=seed)
        polar = PolarCodec(n=64, k=32, design_snr_db=3.0)
        hamming = HammingCodec()

        source = SaturatedSource(seed=seed)
        channel = WiredChannel(seed=seed)

        records = []

        for snr in eb_no_range:
            t0 = time.time()
            # Generate test bits for this point
            raw_bits = source.generate_random_bits(bits_per_point, p_one=0.5)

            # Theoretical uncoded BER
            ber_theory = WiredChannel.theoretical_uncoded_ber_awgn(snr)

            # 1. Uncoded simulation
            rx_hard_uncoded, _, _, _ = channel.transmit_awgn(raw_bits, eb_no_db=snr, code_rate=1.0)
            ber_uncoded = PerformanceEvaluator.calculate_ber(raw_bits, rx_hard_uncoded)['ber']

            # 2. Hamming (7, 4)
            tx_ham, pad_ham = hamming.encode(raw_bits)
            _, rx_soft_ham, _, sig_ham = channel.transmit_awgn(tx_ham, eb_no_db=snr, code_rate=hamming.rate)
            dec_ham = hamming.decode(rx_soft_ham, pad_len=pad_ham, channel_type="awgn")
            ber_ham = PerformanceEvaluator.calculate_ber(raw_bits, dec_ham)['ber']

            # 3. Polar (64, 32)
            tx_pol, pad_pol = polar.encode(raw_bits)
            _, rx_soft_pol, _, sig_pol = channel.transmit_awgn(tx_pol, eb_no_db=snr, code_rate=polar.rate)
            dec_pol = polar.decode(rx_soft_pol, pad_len=pad_pol, channel_type="awgn", sigma=sig_pol)
            ber_pol = PerformanceEvaluator.calculate_ber(raw_bits, dec_pol)['ber']

            # 4. LDPC (64, 32) Sum-Product
            tx_ldpc, pad_ldpc = ldpc_sp.encode(raw_bits)
            _, rx_soft_ldpc, _, sig_ldpc = channel.transmit_awgn(tx_ldpc, eb_no_db=snr, code_rate=ldpc_sp.rate)
            dec_ldpc_sp = ldpc_sp.decode(rx_soft_ldpc, pad_len=pad_ldpc, channel_type="awgn", sigma=sig_ldpc)
            ber_ldpc_sp = PerformanceEvaluator.calculate_ber(raw_bits, dec_ldpc_sp)['ber']

            # 5. LDPC (64, 32) Min-Sum
            dec_ldpc_ms = ldpc_ms.decode(rx_soft_ldpc, pad_len=pad_ldpc, channel_type="awgn", sigma=sig_ldpc)
            ber_ldpc_ms = PerformanceEvaluator.calculate_ber(raw_bits, dec_ldpc_ms)['ber']

            duration = time.time() - t0
            print(f"  Eb/N0 = {snr:4.1f} dB | Uncoded: {ber_uncoded:.4e} | Ham: {ber_ham:.4e} | Polar: {ber_pol:.4e} | LDPC-SP: {ber_ldpc_sp:.4e} | ({duration:.1f}s)")

            records.append({
                'eb_no_db': snr,
                'theory_uncoded_ber': ber_theory,
                'sim_uncoded_ber': ber_uncoded,
                'hamming_7_4_ber': ber_ham,
                'polar_64_32_ber': ber_pol,
                'ldpc_sum_product_ber': ber_ldpc_sp,
                'ldpc_min_sum_ber': ber_ldpc_ms,
                'bits_tested': bits_per_point
            })

        # Save to CSV
        csv_path = os.path.join(self.csv_dir, "awgn_ber_comparison.csv")
        with open(csv_path, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

        print(f"-> Saved AWGN results to {csv_path}")
        return csv_path

    def run_bsc_experiment(
        self,
        p_range: List[float] = None,
        bits_per_point: int = 20480,
        seed: int = 42
    ) -> str:
        """
        Sweep bit-flip probability p over Binary Symmetric Channel.
        """
        if p_range is None:
            p_range = [0.0005, 0.001, 0.005, 0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15]

        print(f"\n[EXPERIMENT 2] Running BSC Bit-Flip Sweep ({min(p_range)} to {max(p_range)}, {bits_per_point} bits/point)...")

        ldpc = LDPCCodec(n=64, k=32, max_iter=25, algorithm="sum_product", seed=seed)
        polar = PolarCodec(n=64, k=32, design_snr_db=3.0)
        hamming = HammingCodec()
        source = SaturatedSource(seed=seed)
        channel = WiredChannel(seed=seed)

        records = []

        for p in p_range:
            t0 = time.time()
            raw_bits = source.generate_random_bits(bits_per_point, p_one=0.5)

            # 1. Uncoded
            rx_uncoded, _ = channel.transmit_bsc(raw_bits, p=p)
            ber_uncoded = PerformanceEvaluator.calculate_ber(raw_bits, rx_uncoded)['ber']

            # 2. Hamming
            tx_ham, pad_ham = hamming.encode(raw_bits)
            rx_ham, _ = channel.transmit_bsc(tx_ham, p=p)
            dec_ham = hamming.decode(rx_ham, pad_len=pad_ham, channel_type="bsc")
            ber_ham = PerformanceEvaluator.calculate_ber(raw_bits, dec_ham)['ber']

            # 3. Polar
            tx_pol, pad_pol = polar.encode(raw_bits)
            rx_pol, _ = channel.transmit_bsc(tx_pol, p=p)
            dec_pol = polar.decode(rx_pol, pad_len=pad_pol, channel_type="bsc", p=p)
            ber_pol = PerformanceEvaluator.calculate_ber(raw_bits, dec_pol)['ber']

            # 4. LDPC
            tx_ldpc, pad_ldpc = ldpc.encode(raw_bits)
            rx_ldpc, _ = channel.transmit_bsc(tx_ldpc, p=p)
            dec_ldpc = ldpc.decode(rx_ldpc, pad_len=pad_ldpc, channel_type="bsc", p=p)
            ber_ldpc = PerformanceEvaluator.calculate_ber(raw_bits, dec_ldpc)['ber']

            duration = time.time() - t0
            print(f"  p = {p:6.4f} | Uncoded: {ber_uncoded:.4e} | Ham: {ber_ham:.4e} | Polar: {ber_pol:.4e} | LDPC: {ber_ldpc:.4e} | ({duration:.1f}s)")

            records.append({
                'p_channel': p,
                'uncoded_ber': ber_uncoded,
                'hamming_7_4_ber': ber_ham,
                'polar_64_32_ber': ber_pol,
                'ldpc_64_32_ber': ber_ldpc,
                'bits_tested': bits_per_point
            })

        csv_path = os.path.join(self.csv_dir, "bsc_ber_comparison.csv")
        with open(csv_path, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

        print(f"-> Saved BSC results to {csv_path}")
        return csv_path

    def run_source_compression_study(self, seed: int = 42) -> str:
        """
        Evaluate source coding on different saturated sources:
        1. Repetitive Telemetry Text
        2. Correlated Markov Binary Sources of varying entropy H(X)
        3. Completely Random Uniform Bits (demonstrating Shannon source coding limit)
        """
        print("\n[EXPERIMENT 3] Running Saturated Source Coding and Lossless Channel Recovery Study...")

        source = SaturatedSource(seed=seed)
        codec = LZWCodec(bit_depth=12)
        channel = WiredChannel(seed=seed)

        records = []

        # Case A: Telemetry packets stream
        text_stream = source.generate_text_stream(num_packets=10)
        h_text = source.compute_empirical_entropy(text_stream)
        comp_bits, stats_text = codec.encode(text_stream)
        # Transmit through lossless channel
        rx_bits, _ = channel.transmit_lossless(comp_bits)
        reconstructed_text = codec.decode(rx_bits, return_as_string=True)
        exact_text = (reconstructed_text == text_stream)

        records.append({
            'source_type': 'Structured Telemetry Stream',
            'empirical_entropy_bits': round(h_text, 4),
            'raw_bits': stats_text['raw_bits'],
            'compressed_bits': stats_text['compressed_bits'],
            'compression_ratio': round(stats_text['compression_ratio'], 3),
            'space_saving_pct': round(stats_text['space_saving_pct'], 2),
            'lossless_exact_recovery': exact_text
        })

        # Case B: Correlated Markov Streams (low entropy to medium entropy)
        markov_configs = [
            ("Correlated Markov (p01=0.05, p10=0.05)", 0.05, 0.05),
            ("Correlated Markov (p01=0.10, p10=0.20)", 0.10, 0.20),
            ("Correlated Markov (p01=0.25, p10=0.25)", 0.25, 0.25),
        ]

        for name, p01, p10 in markov_configs:
            m_bits = source.generate_markov_bits(num_bits=8192, p01=p01, p10=p10)
            h_m = source.compute_empirical_entropy(m_bits)
            packed = np.packbits(m_bits).tobytes()
            c_bits, s_m = codec.encode(packed)
            rx_m, _ = channel.transmit_lossless(c_bits)
            dec_bytes = codec.decode(rx_m, return_as_string=False)
            rec_m = np.unpackbits(np.frombuffer(dec_bytes, dtype=np.uint8))[:len(m_bits)]
            exact_m = np.array_equal(rec_m, m_bits)

            records.append({
                'source_type': name,
                'empirical_entropy_bits': round(h_m, 4),
                'raw_bits': s_m['raw_bits'],
                'compressed_bits': s_m['compressed_bits'],
                'compression_ratio': round(s_m['compression_ratio'], 3),
                'space_saving_pct': round(s_m['space_saving_pct'], 2),
                'lossless_exact_recovery': exact_m
            })

        # Case C: Uniform random bits (H ~ 1.0)
        u_bits = source.generate_random_bits(num_bits=8192, p_one=0.5)
        h_u = source.compute_empirical_entropy(u_bits)
        packed_u = np.packbits(u_bits).tobytes()
        c_bits_u, s_u = codec.encode(packed_u)
        rx_u, _ = channel.transmit_lossless(c_bits_u)
        dec_bytes_u = codec.decode(rx_u, return_as_string=False)
        rec_u = np.unpackbits(np.frombuffer(dec_bytes_u, dtype=np.uint8))[:len(u_bits)]
        exact_u = np.array_equal(rec_u, u_bits)

        records.append({
            'source_type': 'Uniform Pseudo-Random Bits (H ~ 1)',
            'empirical_entropy_bits': round(h_u, 4),
            'raw_bits': s_u['raw_bits'],
            'compressed_bits': s_u['compressed_bits'],
            'compression_ratio': round(s_u['compression_ratio'], 3),
            'space_saving_pct': round(s_u['space_saving_pct'], 2),
            'lossless_exact_recovery': exact_u
        })

        csv_path = os.path.join(self.csv_dir, "source_compression_study.csv")
        with open(csv_path, mode='w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)

        print(f"-> Saved Source Compression results to {csv_path}")
        return csv_path

    def generate_all_plots(self, paper_fig_dir: str = "paper/figures") -> List[str]:
        """
        Generate publication-grade figures from actual CSV data.
        """
        os.makedirs(paper_fig_dir, exist_ok=True)
        generated_files = []

        # ----------------------------------------------------
        # Plot 1: AWGN BER Waterfall Curves
        # ----------------------------------------------------
        awgn_csv = os.path.join(self.csv_dir, "awgn_ber_comparison.csv")
        if os.path.exists(awgn_csv):
            data = []
            with open(awgn_csv, mode='r') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    data.append({k: float(v) for k, v in r.items()})

            snr = [d['eb_no_db'] for d in data]
            th_uncoded = [d['theory_uncoded_ber'] for d in data]
            sim_uncoded = [max(d['sim_uncoded_ber'], 1e-5) for d in data]
            ham_ber = [max(d['hamming_7_4_ber'], 1e-5) for d in data]
            pol_ber = [max(d['polar_64_32_ber'], 1e-5) for d in data]
            ldpc_sp_ber = [max(d['ldpc_sum_product_ber'], 1e-5) for d in data]
            ldpc_ms_ber = [max(d['ldpc_min_sum_ber'], 1e-5) for d in data]

            plt.figure(figsize=(7.5, 5.2), dpi=300)
            plt.semilogy(snr, th_uncoded, 'k--', label='Theoretical Uncoded BPSK', linewidth=1.5)
            plt.semilogy(snr, sim_uncoded, 'o-', color='#333333', label='Simulated Uncoded BPSK', markersize=6, alpha=0.8)
            plt.semilogy(snr, ham_ber, 's-', color='#e67e22', label='Systematic Hamming(7,4)', markersize=6)
            plt.semilogy(snr, pol_ber, '^-', color='#2980b9', label='Polar(64,32) SC Decoder', markersize=6)
            plt.semilogy(snr, ldpc_ms_ber, 'd-.', color='#8e44ad', label='LDPC(64,32) Min-Sum', markersize=6)
            plt.semilogy(snr, ldpc_sp_ber, '*-', color='#27ae60', label='LDPC(64,32) Sum-Product (IEEE 802.3an)', markersize=8, linewidth=2)

            plt.grid(True, which="both", ls=":", color='#cccccc', alpha=0.8)
            plt.xlabel(r"Wired Link $E_b/N_0$ (dB)", fontsize=11, fontweight='bold')
            plt.ylabel(r"Bit Error Rate (BER)", fontsize=11, fontweight='bold')
            plt.title("Wired Communication System: BER vs. $E_b/N_0$ Performance", fontsize=12, fontweight='bold')
            plt.ylim([5e-6, 0.3])
            plt.xlim([min(snr), max(snr)])
            plt.legend(loc='lower left', fontsize=9, framealpha=0.9)
            plt.tight_layout()

            p1 = os.path.join(self.plots_dir, "fig1_awgn_ber_curves.png")
            plt.savefig(p1)
            plt.savefig(os.path.join(paper_fig_dir, "fig1_awgn_ber_curves.png"))
            plt.close()
            generated_files.append(p1)

        # ----------------------------------------------------
        # Plot 2: BSC Bit-Flip Sweep
        # ----------------------------------------------------
        bsc_csv = os.path.join(self.csv_dir, "bsc_ber_comparison.csv")
        if os.path.exists(bsc_csv):
            data = []
            with open(bsc_csv, mode='r') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    data.append({k: float(v) for k, v in r.items()})

            p_vals = [d['p_channel'] for d in data]
            uncoded = [d['uncoded_ber'] for d in data]
            ham = [max(d['hamming_7_4_ber'], 1e-5) for d in data]
            pol = [max(d['polar_64_32_ber'], 1e-5) for d in data]
            ldpc = [max(d['ldpc_64_32_ber'], 1e-5) for d in data]

            plt.figure(figsize=(7.5, 5.2), dpi=300)
            plt.loglog(p_vals, uncoded, 'k--', label='Uncoded Channel (BER = p)', linewidth=1.5)
            plt.loglog(p_vals, ham, 's-', color='#e67e22', label='Hamming(7,4)', markersize=6)
            plt.loglog(p_vals, pol, '^-', color='#2980b9', label='Polar(64,32) SC', markersize=6)
            plt.loglog(p_vals, ldpc, '*-', color='#27ae60', label='LDPC(64,32) BP', markersize=8, linewidth=2)

            plt.grid(True, which="both", ls=":", color='#cccccc', alpha=0.8)
            plt.xlabel("Channel Bit-Flip Probability $p$", fontsize=11, fontweight='bold')
            plt.ylabel("Post-Decoding Bit Error Rate (BER)", fontsize=11, fontweight='bold')
            plt.title("Parametric BSC Wired Link: FEC Error-Suppression Thresholds", fontsize=12, fontweight='bold')
            plt.ylim([5e-6, 0.4])
            plt.legend(loc='lower right', fontsize=9, framealpha=0.9)
            plt.tight_layout()

            p2 = os.path.join(self.plots_dir, "fig2_bsc_ber_curves.png")
            plt.savefig(p2)
            plt.savefig(os.path.join(paper_fig_dir, "fig2_bsc_ber_curves.png"))
            plt.close()
            generated_files.append(p2)

        # ----------------------------------------------------
        # Plot 3: Pre-FEC vs Post-FEC BER Waterfall
        # ----------------------------------------------------
        if os.path.exists(awgn_csv):
            plt.figure(figsize=(7.0, 5.0), dpi=300)
            plt.loglog(sim_uncoded, sim_uncoded, 'k--', label='Uncoded (Pre-FEC = Post-FEC)')
            plt.loglog(sim_uncoded, ham_ber, 's-', color='#e67e22', label='Hamming(7,4) Slicer')
            plt.loglog(sim_uncoded, pol_ber, '^-', color='#2980b9', label='Polar(64,32) SC')
            plt.loglog(sim_uncoded, ldpc_sp_ber, '*-', color='#27ae60', label='LDPC(64,32) BP (IEEE 802.3an)', linewidth=2)

            plt.grid(True, which="both", ls=":", color='#cccccc', alpha=0.8)
            plt.xlabel("Raw Pre-FEC Bit Error Rate", fontsize=11, fontweight='bold')
            plt.ylabel("Decoded Post-FEC Bit Error Rate", fontsize=11, fontweight='bold')
            plt.title("Pre-FEC vs. Post-FEC Performance (Wired FEC Waterfall)", fontsize=12, fontweight='bold')
            plt.ylim([5e-6, 0.2])
            plt.xlim([5e-5, 0.2])
            plt.gca().invert_xaxis()
            plt.legend(loc='upper right', fontsize=9)
            plt.tight_layout()

            p3 = os.path.join(self.plots_dir, "fig3_pre_vs_post_fec.png")
            plt.savefig(p3)
            plt.savefig(os.path.join(paper_fig_dir, "fig3_pre_vs_post_fec.png"))
            plt.close()
            generated_files.append(p3)

        # ----------------------------------------------------
        # Plot 4: Source Compression vs. Empirical Entropy
        # ----------------------------------------------------
        src_csv = os.path.join(self.csv_dir, "source_compression_study.csv")
        if os.path.exists(src_csv):
            src_data = []
            with open(src_csv, mode='r') as f:
                reader = csv.DictReader(f)
                for r in reader:
                    src_data.append(r)

            names = [r['source_type'] for r in src_data]
            entropies = [float(r['empirical_entropy_bits']) for r in src_data]
            crs = [float(r['compression_ratio']) for r in src_data]
            savings = [float(r['space_saving_pct']) for r in src_data]

            fig, ax1 = plt.subplots(figsize=(8.0, 4.8), dpi=300)
            x = np.arange(len(names))
            width = 0.35

            rects1 = ax1.bar(x - width/2, crs, width, label='Compression Ratio (CR)', color='#3498db', edgecolor='#2980b9')
            ax1.set_ylabel('Compression Ratio ($L_{raw} / L_{comp}$)', color='#2980b9', fontsize=10, fontweight='bold')
            ax1.set_xticks(x)
            ax1.set_xticklabels(['Telemetry\nPackets', 'Markov\n(p=0.05)', 'Markov\n(p=0.10)', 'Markov\n(p=0.25)', 'Uniform\nRandom (H~1)'], fontsize=9)
            ax1.set_ylim([0, max(crs) * 1.25])
            ax1.axhline(1.0, color='gray', linestyle=':', label='Threshold CR = 1.0')

            ax2 = ax1.twinx()
            rects2 = ax2.bar(x + width/2, entropies, width, label='Source Entropy $H(X)$ (bits)', color='#e74c3c', edgecolor='#c0392b', alpha=0.85)
            ax2.set_ylabel('Empirical Entropy $H(X)$ (bits/symbol)', color='#c0392b', fontsize=10, fontweight='bold')
            ax2.set_ylim([0, max(entropies) * 1.3])

            plt.title('Saturated Source Coding Efficiency vs. Source Entropy', fontsize=11, fontweight='bold')
            fig.tight_layout()

            p4 = os.path.join(self.plots_dir, "fig4_source_compression_tradeoff.png")
            plt.savefig(p4)
            plt.savefig(os.path.join(paper_fig_dir, "fig4_source_compression_tradeoff.png"))
            plt.close()
            generated_files.append(p4)

        # ----------------------------------------------------
        # Plot 5: Architecture Pipeline Overview Diagram
        # ----------------------------------------------------
        fig, ax = plt.subplots(figsize=(10.0, 3.2), dpi=300)
        ax.axis('off')

        box_props = dict(boxstyle='round,pad=0.5', facecolor='#eef2f7', edgecolor='#2c3e50', linewidth=1.5)
        ch_box_props = dict(boxstyle='round,pad=0.5', facecolor='#fce4ec', edgecolor='#c2185b', linewidth=1.5)

        boxes = [
            ("Saturated\nSource", 0.08, 0.5),
            ("Binary\nConverter", 0.22, 0.5),
            ("LZW Source\nEncoder", 0.36, 0.5),
            ("IEEE 802.3an\nLDPC Encoder", 0.50, 0.5),
            ("Wired Link\n(AWGN/Lossless)", 0.64, 0.5),
            ("LDPC BP\nDecoder", 0.78, 0.5),
            ("LZW Source\nDecoder", 0.92, 0.5),
        ]

        for text, px, py in boxes:
            props = ch_box_props if "Wired" in text else box_props
            ax.text(px, py, text, ha='center', va='center', bbox=props, fontsize=8.5, fontweight='bold')

        for i in range(len(boxes) - 1):
            x1 = boxes[i][1] + 0.045
            x2 = boxes[i+1][1] - 0.045
            ax.annotate('', xy=(x2, 0.5), xytext=(x1, 0.5),
                        arrowprops=dict(arrowstyle="->", color='#2c3e50', lw=1.8))

        # Bottom return arrow to BER Evaluator
        ax.text(0.50, 0.12, "Performance Evaluator (Pre/Post-FEC BER, FER, Reconstruction Fidelity)",
                ha='center', va='center', bbox=dict(boxstyle='round,pad=0.4', facecolor='#e8f8f5', edgecolor='#16a085', lw=1.5),
                fontsize=8.5, fontweight='bold')

        p5 = os.path.join(self.plots_dir, "fig5_pipeline_architecture.png")
        plt.savefig(p5)
        plt.savefig(os.path.join(paper_fig_dir, "fig5_pipeline_architecture.png"))
        plt.close()
        generated_files.append(p5)

        print(f"-> Generated {len(generated_files)} publication-grade plots in {self.plots_dir} and {paper_fig_dir}")
        return generated_files
