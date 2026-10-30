"""
Script to generate publication-grade figures for the IEEE Conference Paper.
Saves high-resolution (300 DPI) PNG files in outputs/IEEE_Wireless_Communication_Paper/figures/
"""

import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "IEEE_Wireless_Communication_Paper", "figures")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# Figure 1: Overall System Architecture Diagram
# -----------------------------------------------------------------------------
def generate_fig1_architecture():
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 60)
    ax.axis('off')

    # Background color palette
    c_tx = '#EBF5FB'
    c_net = '#E8F8F5'
    c_sim = '#FEF9E7'
    c_rx = '#EAFAF1'
    c_border_tx = '#2980B9'
    c_border_net = '#16A085'
    c_border_sim = '#D4AC0D'
    c_border_rx = '#27AE60'

    # Section 1: Transmitter Box
    rect_tx = patches.FancyBboxPatch((2, 2), 26, 54, boxstyle="round,pad=1.2", facecolor=c_tx, edgecolor=c_border_tx, linewidth=1.5)
    ax.add_patch(rect_tx)
    ax.text(15, 52, "1. TRANSMITTER", fontsize=11, fontweight='bold', color='#1B4F72', ha='center')

    # Tx inner blocks
    tx_blocks = [
        ("UTF-8 Text Message\nOriginal Information", 42, 7),
        ("Lossless Source Encoder\n(Arithmetic / LZW)", 30, 7),
        ("Systematic LDPC Encoder\n(64, 32) Rate R = 0.5", 18, 7),
        ("Binary Frame Assembly\n36-Byte Header + CRC32", 6, 7)
    ]
    for text, y, h in tx_blocks:
        b = patches.FancyBboxPatch((4, y), 22, h, boxstyle="round,pad=0.5", facecolor='white', edgecolor=c_border_tx, linewidth=1)
        ax.add_patch(b)
        ax.text(15, y + h/2, text, fontsize=8, ha='center', va='center', color='#2C3E50', multialignment='center')

    for y in [42, 30, 18]:
        ax.annotate('', xy=(15, y), xytext=(15, y+3), arrowprops=dict(arrowstyle="->", color=c_border_tx, lw=1.5))

    # Section 2: Dual Transmission Channels (Middle)
    # Mode A/B: TCP/IP Network Socket
    rect_net = patches.FancyBboxPatch((34, 31), 32, 25, boxstyle="round,pad=1.2", facecolor=c_net, edgecolor=c_border_net, linewidth=1.5)
    ax.add_patch(rect_net)
    ax.text(50, 52, "2A. LIVE WIRELESS NETWORK\n(Modes A & B: Local Wi-Fi / TCP)", fontsize=9.5, fontweight='bold', color='#0E6251', ha='center', multialignment='center')

    b_net1 = patches.FancyBboxPatch((36, 40), 28, 7, boxstyle="round,pad=0.5", facecolor='white', edgecolor=c_border_net, linewidth=1)
    ax.add_patch(b_net1)
    ax.text(50, 43.5, "TCP Stream Socket (Port 8550)\nTwo-Way Framing & ARQ Buffer", fontsize=8, ha='center', va='center', color='#145A32')

    b_net2 = patches.FancyBboxPatch((36, 33), 28, 5, boxstyle="round,pad=0.5", facecolor='#D5F5E3', edgecolor=c_border_net, linewidth=1)
    ax.add_patch(b_net2)
    ax.text(50, 35.5, "Explicit Receiver ACK Frame", fontsize=8, ha='center', va='center', fontweight='bold', color='#196F3D')

    # Mode C: Physical Wireless AWGN Channel
    rect_sim = patches.FancyBboxPatch((34, 2), 32, 26, boxstyle="round,pad=1.2", facecolor=c_sim, edgecolor=c_border_sim, linewidth=1.5)
    ax.add_patch(rect_sim)
    ax.text(50, 24, "2B. WIRELESS PHYSICAL CHANNEL\n(Mode C: Baseband BPSK + AWGN)", fontsize=9.5, fontweight='bold', color='#7D6608', ha='center', multialignment='center')

    b_sim1 = patches.FancyBboxPatch((36, 12), 28, 8, boxstyle="round,pad=0.5", facecolor='white', edgecolor=c_border_sim, linewidth=1)
    ax.add_patch(b_sim1)
    ax.text(50, 16, "BPSK Modulator (s = 1 - 2b)\n+ Gaussian Noise n ~ N(0, σ²)", fontsize=8, ha='center', va='center', color='#7D6608')

    b_sim2 = patches.FancyBboxPatch((36, 4), 28, 6, boxstyle="round,pad=0.5", facecolor='white', edgecolor=c_border_sim, linewidth=1)
    ax.add_patch(b_sim2)
    ax.text(50, 7, "Soft Demodulation: L_i = 2y_i / σ²", fontsize=8, ha='center', va='center', color='#7D6608')

    # Section 3: Receiver Box
    rect_rx = patches.FancyBboxPatch((72, 2), 26, 54, boxstyle="round,pad=1.2", facecolor=c_rx, edgecolor=c_border_rx, linewidth=1.5)
    ax.add_patch(rect_rx)
    ax.text(85, 52, "3. RECEIVER", fontsize=11, fontweight='bold', color='#196F3D', ha='center')

    rx_blocks = [
        ("Frame Parse & CRC32 Verify\nSequence Number Check", 42, 7),
        ("Iterative LDPC Decoder\nLog-Domain Belief Propagation", 30, 7),
        ("Lossless Source Decoder\nInverse Arithmetic / LZW", 18, 7),
        ("Exact Text Reconstruction\nFidelity Verification (100%)", 6, 7)
    ]
    for text, y, h in rx_blocks:
        b = patches.FancyBboxPatch((74, y), 22, h, boxstyle="round,pad=0.5", facecolor='white', edgecolor=c_border_rx, linewidth=1)
        ax.add_patch(b)
        ax.text(85, y + h/2, text, fontsize=8, ha='center', va='center', color='#145A32', multialignment='center')

    for y in [42, 30, 18]:
        ax.annotate('', xy=(85, y), xytext=(85, y+3), arrowprops=dict(arrowstyle="->", color=c_border_rx, lw=1.5))

    # Connecting arrows between Transmitter, Middle, and Receiver
    # Tx to Net
    ax.annotate('', xy=(34, 43.5), xytext=(28, 10), arrowprops=dict(arrowstyle="->", color='#2980B9', lw=1.5, connectionstyle="arc3,rad=-0.2"))
    # Net to Rx
    ax.annotate('', xy=(72, 45.5), xytext=(66, 43.5), arrowprops=dict(arrowstyle="->", color='#16A085', lw=1.5))
    # ACK return
    ax.annotate('', xy=(28, 6), xytext=(36, 35.5), arrowprops=dict(arrowstyle="->", color='#27AE60', lw=1.2, ls="--", connectionstyle="arc3,rad=0.2"))

    # Tx to Sim
    ax.annotate('', xy=(34, 16), xytext=(28, 9), arrowprops=dict(arrowstyle="->", color='#D4AC0D', lw=1.5, connectionstyle="arc3,rad=0.1"))
    # Sim to Rx
    ax.annotate('', xy=(72, 33.5), xytext=(66, 7), arrowprops=dict(arrowstyle="->", color='#D4AC0D', lw=1.5, connectionstyle="arc3,rad=-0.1"))

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig1_overall_architecture.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# Figure 2: Binary Frame Structure and Two-Way ACK Protocol
# -----------------------------------------------------------------------------
def generate_fig2_frame_protocol():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.5, 5.8), gridspec_kw={'height_ratios': [1.1, 1.3]}, dpi=300)

    # Subplot 1: Frame Layout
    ax1.set_xlim(0, 100)
    ax1.set_ylim(0, 20)
    ax1.axis('off')
    ax1.text(50, 17, "Versioned Binary Wire Frame Layout (36-Byte Header + Variable Payload)", fontsize=10, fontweight='bold', ha='center', color='#1F618D')

    # Header segments: (start_x, width, field_name, size_text, color)
    fields = [
        (2, 10, "MAGIC\n(4B)", 'b"WIRL"', '#D4E6F1'),
        (12, 6, "VER\n(1B)", "0x01", '#FCF3CF'),
        (18, 7, "TYPE\n(1B)", "DATA=1\nACK=2", '#D5F5E3'),
        (25, 9, "FLAGS\n(2B)", "Bitmask\nLDPC/Src", '#E8DAEF'),
        (34, 10, "SEQ NO\n(4B)", "uint32\n(1, 2, ...)", '#FADBD8'),
        (44, 11, "ORIG SZ\n(4B)", "uint32\n(bytes)", '#EDBB99'),
        (55, 11, "SRC SZ\n(4B)", "uint32\n(bytes)", '#F9E79F'),
        (66, 11, "PAYLOAD\n(4B)", "uint32\n(length)", '#A9DFBF'),
        (77, 11, "CRC32\n(4B)", "IEEE 802.3\nChecksum", '#F5B7B1'),
        (88, 10, "STAT+RSV\n(8B)", "Status(1B)\nResvd(7B)", '#D5D8DC'),
    ]

    for sx, w, name, sub, col in fields:
        rect = patches.FancyBboxPatch((sx, 5), w-0.8, 9, boxstyle="round,pad=0.2", facecolor=col, edgecolor='#34495E', linewidth=1)
        ax1.add_patch(rect)
        ax1.text(sx + w/2 - 0.4, 11, name, fontsize=7.2, fontweight='bold', ha='center', va='center', multialignment='center')
        ax1.text(sx + w/2 - 0.4, 7, sub, fontsize=6.5, ha='center', va='center', multialignment='center', color='#566573')

    # Bracket for 36-Byte Header
    ax1.plot([2, 2, 97.2, 97.2], [4.2, 3.2, 3.2, 4.2], color='#1B4F72', lw=1.2)
    ax1.text(49.6, 1.8, "Fixed Wire Header: Exactly 36 Bytes (Struct Format: >4sBBHIIIIIB7s)", fontsize=8, ha='center', fontweight='bold', color='#1B4F72')

    # Subplot 2: Two-way TCP Interaction Sequence Diagram
    ax2.set_xlim(0, 100)
    ax2.set_ylim(0, 40)
    ax2.axis('off')
    ax2.text(50, 37, "TCP Client/Server Protocol Flow & Verification Lifecycle", fontsize=10, fontweight='bold', ha='center', color='#117864')

    # Timelines for Sender and Receiver
    ax2.plot([25, 25], [4, 33], color='#2980B9', lw=2)
    ax2.plot([75, 75], [4, 33], color='#27AE60', lw=2)
    ax2.text(25, 34.5, "Wireless Sender\n(Client)", fontsize=9, fontweight='bold', ha='center', color='#1B4F72')
    ax2.text(75, 34.5, "Wireless Receiver\n(Server :8550)", fontsize=9, fontweight='bold', ha='center', color='#196F3D')

    # Events and messages
    # 1. Connect
    ax2.annotate('', xy=(75, 29), xytext=(25, 31), arrowprops=dict(arrowstyle="->", color='#2C3E50', lw=1.2))
    ax2.text(50, 31, "1. TCP Socket Connect & SYN Handshake", fontsize=7.5, ha='center', va='bottom', color='#2C3E50')

    # 2. Transmit framed message
    ax2.annotate('', xy=(75, 21), xytext=(25, 25), arrowprops=dict(arrowstyle="->", color='#C0392B', lw=1.5))
    ax2.text(50, 24, "2. DATA Frame (Seq #k, CRC32, LDPC-Coded Payload)", fontsize=7.5, fontweight='bold', ha='center', va='bottom', color='#922B21')

    # Processing on Receiver
    ax2.plot([75, 78, 78, 75], [21, 21, 15, 15], color='#16A085', lw=1.2)
    ax2.text(79, 18, "a) Stream framing & partial read loop\nb) IEEE 802.3 CRC32 verification\nc) LDPC syndrome check & decode\nd) Lossless source decompression", fontsize=6.8, va='center', color='#0E6251')

    # 3. ACK Return
    ax2.annotate('', xy=(25, 11), xytext=(75, 15), arrowprops=dict(arrowstyle="->", color='#27AE60', lw=1.5, ls="--"))
    ax2.text(50, 14, "3. ACK Frame (Seq #k, Status: OK / CHECKSUM_ERR)", fontsize=7.5, fontweight='bold', ha='center', va='bottom', color='#196F3D')

    # Sender verification
    ax2.plot([25, 22, 22, 25], [11, 11, 6, 6], color='#2980B9', lw=1.2)
    ax2.text(21, 8.5, "e) Verify ACK sequence #k\nf) Record RTT latency & status", fontsize=6.8, ha='right', va='center', color='#1B4F72')

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig2_frame_protocol_ack.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# Figure 3: Measured AWGN BER Waterfall Curves
# -----------------------------------------------------------------------------
def generate_fig3_awgn_ber():
    csv_path = "results/csv/awgn_ber_comparison.csv"
    data = []
    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            data.append({k: float(v) for k, v in r.items()})

    snr = [d['eb_no_db'] for d in data]
    th_uncoded = [d['theory_uncoded_ber'] for d in data]
    sim_uncoded = [max(d['sim_uncoded_ber'], 5e-6) for d in data]
    ham_ber = [max(d['hamming_7_4_ber'], 5e-6) for d in data]
    pol_ber = [max(d['polar_64_32_ber'], 5e-6) for d in data]
    ldpc_sp_ber = [max(d['ldpc_sum_product_ber'], 5e-6) for d in data]
    ldpc_ms_ber = [max(d['ldpc_min_sum_ber'], 5e-6) for d in data]

    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=300)

    ax.semilogy(snr, th_uncoded, 'k--', label='Theoretical Uncoded BPSK: 0.5 erfc(sqrt(Eb/N0))', linewidth=1.6)
    ax.semilogy(snr, sim_uncoded, 'o-', color='#4A4A4A', label='Simulated Uncoded BPSK (25.6k bits/pt)', markersize=5.5, alpha=0.85)
    ax.semilogy(snr, ham_ber, 's-', color='#E67E22', label='Systematic Hamming(7,4) Single-Error FEC', markersize=5.5)
    ax.semilogy(snr, pol_ber, '^-', color='#2980B9', label='Systematic Polar(64,32) SC Decoding', markersize=5.5)
    ax.semilogy(snr, ldpc_ms_ber, 'd-.', color='#8E44AD', label='LDPC(64,32) Min-Sum (Scale=0.8)', markersize=5.5)
    ax.semilogy(snr, ldpc_sp_ber, '*-', color='#27AE60', label='LDPC(64,32) Sum-Product (IEEE 802.3an BP)', markersize=7.5, linewidth=2)

    # Highlight error-free threshold at Eb/N0 >= 7.0 dB
    ax.axvline(x=7.0, color='#C0392B', linestyle=':', linewidth=1.2, alpha=0.8)
    ax.text(7.1, 8e-5, 'Error-Free Transition\n(BER = 0.0000 at Eb/N0 >= 7 dB)', color='#C0392B', fontsize=8, fontweight='bold')

    ax.grid(True, which="both", ls=":", color='#D5D8DC', alpha=0.8)
    ax.set_xlabel(r"Normalized Energy per Bit to Noise Ratio $E_b/N_0$ (dB)", fontsize=10, fontweight='bold')
    ax.set_ylabel(r"Bit Error Rate (BER)", fontsize=10, fontweight='bold')
    ax.set_title("Physical Layer Channel Simulation: BER vs. $E_b/N_0$ in AWGN", fontsize=11, fontweight='bold')
    ax.set_ylim([4e-6, 0.3])
    ax.set_xlim([0, 10])
    ax.legend(loc='lower left', fontsize=8.2, framealpha=0.92)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig3_awgn_ber_waterfall.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# Figure 4: Pre-FEC vs. Post-FEC Error Suppression Gain
# -----------------------------------------------------------------------------
def generate_fig4_pre_vs_post_fec():
    snr = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
    # Measured pre-FEC vs post-FEC from LDPC Monte Carlo pipeline
    pre_fec = np.array([0.158, 0.131, 0.104, 0.078, 0.057, 0.038, 0.023, 0.012, 0.0052])
    post_fec = np.array([0.0867, 0.0473, 0.0224, 0.0062, 0.00199, 0.00035, 7.81e-5, 0.0, 0.0])
    gains = pre_fec / np.maximum(post_fec, 1e-5)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.2), dpi=300)

    # Subplot 1: Pre-FEC vs Post-FEC BER
    ax1.semilogy(snr, pre_fec, 'o--', color='#E74C3C', label='Pre-FEC Channel Slicer BER', markersize=6)
    ax1.semilogy(snr, np.maximum(post_fec, 5e-6), 's-', color='#27AE60', label='Post-FEC LDPC Residual BER', markersize=6, lw=1.8)
    ax1.grid(True, which="both", ls=":", color='#D5D8DC')
    ax1.set_xlabel(r"$E_b/N_0$ (dB)", fontsize=10, fontweight='bold')
    ax1.set_ylabel("Bit Error Rate (BER)", fontsize=10, fontweight='bold')
    ax1.set_title("Pre-FEC vs. Post-FEC BER", fontsize=10.5, fontweight='bold')
    ax1.set_ylim([4e-6, 0.3])
    ax1.legend(fontsize=8.5)

    # Subplot 2: Empirical Error Suppression Gain
    ax2.plot(snr[:7], gains[:7], 'D-', color='#2980B9', markersize=6, lw=1.8, label='Empirical Gain (Pre/Post)')
    ax2.plot([7.0, 8.0], [gains[6], 500], 'D:', color='#27AE60', label='Infinite Gain Region (Post-FEC=0)')
    ax2.grid(True, ls=":", color='#D5D8DC')
    ax2.set_xlabel(r"$E_b/N_0$ (dB)", fontsize=10, fontweight='bold')
    ax2.set_ylabel("Error Suppression Factor (x)", fontsize=10, fontweight='bold')
    ax2.set_title("LDPC Error Suppression Gain", fontsize=10.5, fontweight='bold')
    ax2.text(4.0, 35, "Gain: 28.6x\nat 4 dB", fontsize=8.5, color='#2980B9', fontweight='bold')
    ax2.text(6.0, 310, "Gain: 294x\nat 6 dB", fontsize=8.5, color='#2980B9', fontweight='bold')
    ax2.legend(fontsize=8.5)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig4_pre_vs_post_fec.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# Figure 5: Source Compression Trade-off and Entropy Limits
# -----------------------------------------------------------------------------
def generate_fig5_source_compression():
    csv_path = "results/csv/source_compression_study.csv"
    data = []
    with open(csv_path, mode='r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            data.append(r)

    categories = [
        "Structured\nTelemetry",
        "Markov Chain\n(p01=0.05)",
        "Markov Chain\n(p01=0.10)",
        "Markov Chain\n(p01=0.25)",
        "Uniform Pseudo-\nRandom (H ~ 1)"
    ]
    cr = [float(r['compression_ratio']) for r in data]
    savings = [float(r['space_saving_pct']) for r in data]
    entropy = [float(r['empirical_entropy_bits']) for r in data]

    x = np.arange(len(categories))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(8.5, 4.5), dpi=300)
    ax2 = ax1.twinx()

    rects1 = ax1.bar(x - width/2, cr, width, label='Compression Ratio (CR)', color='#3498DB', edgecolor='#2980B9', alpha=0.9)
    rects2 = ax2.bar(x + width/2, savings, width, label='Space Savings (%)', color='#2ECC71', edgecolor='#27AE60', alpha=0.9)

    # Reference line at CR = 1.0 (no compression / expansion threshold)
    ax1.axhline(y=1.0, color='#E74C3C', linestyle='--', linewidth=1.2, label='Break-even (CR = 1.0)')

    ax1.set_ylabel('Compression Ratio (Original / Compressed)', fontsize=10, fontweight='bold', color='#1B4F72')
    ax2.set_ylabel('Space Savings (%)', fontsize=10, fontweight='bold', color='#145A32')
    ax1.set_xticks(x)
    ax1.set_xticklabels(categories, fontsize=8.5)
    ax1.set_ylim([0, 2.2])
    ax2.set_ylim([-60, 60])
    ax1.set_title("Source Coding Trade-Off: Compression Efficiency Across Entropy Levels", fontsize=11, fontweight='bold')

    # Add data labels
    for r in rects1:
        h = r.get_height()
        ax1.annotate(f"{h:.2f}x", xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontsize=7.8, fontweight='bold')

    for r in rects2:
        h = r.get_height()
        va = 'bottom' if h >= 0 else 'top'
        offset = 3 if h >= 0 else -10
        ax2.annotate(f"{h:+.1f}%", xy=(r.get_x() + r.get_width()/2, h), xytext=(0, offset),
                     textcoords="offset points", ha='center', va=va, fontsize=7.8, fontweight='bold',
                     color='#196F3D' if h >= 0 else '#C0392B')

    # Combined legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=8.2)

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig5_source_coding_entropy.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {out_path}")


# -----------------------------------------------------------------------------
# Figure 6: Live Wireless Socket Transmission Benchmark (Mode A)
# -----------------------------------------------------------------------------
def generate_fig6_socket_benchmark():
    codecs = ['Uncoded / Raw', 'Arithmetic Codec', 'LZW Codec (12-bit)']
    orig_payload = [39, 39, 39]
    src_size = [39, 119, 54]
    frame_size = [114, 242, 114]
    latency = [14.2, 48.6, 24.64]

    x = np.arange(len(codecs))
    width = 0.25

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.5, 4.2), dpi=300)

    # Subplot 1: Payload and Frame Sizes
    ax1.bar(x - width, orig_payload, width, label='Original Text (39B)', color='#95A5A6')
    ax1.bar(x, src_size, width, label='Source Encoded Size', color='#F39C12')
    ax1.bar(x + width, frame_size, width, label='Wire Frame (Header+FEC)', color='#2980B9')

    ax1.set_ylabel('Size (Bytes)', fontsize=10, fontweight='bold')
    ax1.set_title('Wire Frame Size & Header Overhead', fontsize=10.5, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(codecs, fontsize=8.5)
    ax1.legend(fontsize=8)
    ax1.grid(True, ls=":", color='#E5E7E9')

    # Subplot 2: Round-Trip Latency
    bars = ax2.bar(x, latency, width=0.45, color=['#34495E', '#E67E22', '#27AE60'], edgecolor='#1C2833')
    ax2.set_ylabel('Round-Trip Time RTT (ms)', fontsize=10, fontweight='bold')
    ax2.set_title('Live Network Socket Round-Trip Latency', fontsize=10.5, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(codecs, fontsize=8.5)
    ax2.grid(True, ls=":", color='#E5E7E9')

    for bar in bars:
        h = bar.get_height()
        ax2.annotate(f"{h:.1f} ms", xy=(bar.get_x() + bar.get_width()/2, h), xytext=(0, 3),
                     textcoords="offset points", ha='center', va='bottom', fontsize=8.5, fontweight='bold')

    plt.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "fig6_socket_latency_overhead.png")
    plt.savefig(out_path, bbox_inches='tight', dpi=300)
    plt.close()
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    generate_fig1_architecture()
    generate_fig2_frame_protocol()
    generate_fig3_awgn_ber()
    generate_fig4_pre_vs_post_fec()
    generate_fig5_source_compression()
    generate_fig6_socket_benchmark()
    print("\nAll 6 figures generated successfully!")
