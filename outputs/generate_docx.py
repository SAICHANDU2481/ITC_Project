"""
Compiles the complete IEEE Conference Research Paper into editable DOCX format using python-docx.
Implements standard IEEE 2-column conference formatting, professional typography,
author block with three authors, embedded high-resolution figures, formatted tables,
mathematical formulas, and numbered IEEE citations.
"""

import os
import docx
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

DOCX_FILENAME = "outputs/IEEE_Wireless_Communication_Paper/IEEE_Wireless_Communication_Paper.docx"
FIG_DIR = "outputs/IEEE_Wireless_Communication_Paper/figures"


def set_cell_background(cell, hex_color):
    shading_xml = f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>'
    cell._tc.get_or_add_tcPr().append(parse_xml(shading_xml))


def set_table_borders(table, color="D3D3D3"):
    tblPr = table._tbl.tblPr
    borders_xml = f'''
    <w:tblBorders {nsdecls("w")}>
        <w:top w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:bottom w:val="single" w:sz="6" w:space="0" w:color="{color}"/>
        <w:insideH w:val="single" w:sz="4" w:space="0" w:color="{color}"/>
        <w:insideV w:val="none"/>
        <w:left w:val="none"/>
        <w:right w:val="none"/>
    </w:tblBorders>
    '''
    tblPr.append(parse_xml(borders_xml))


def build_docx(filename=DOCX_FILENAME):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    doc = Document()

    # ----------------------------------------------------
    # SECTION 1: Page Setup & Margins (1 Column for Title)
    # ----------------------------------------------------
    sec1 = doc.sections[0]
    sec1.top_margin = Inches(0.6)
    sec1.bottom_margin = Inches(0.6)
    sec1.left_margin = Inches(0.6)
    sec1.right_margin = Inches(0.6)
    sec1.page_width = Inches(8.5)
    sec1.page_height = Inches(11.0)

    # Configure Default Style
    style_normal = doc.styles['Normal']
    style_normal.font.name = 'Times New Roman'
    style_normal.font.size = Pt(9.5)
    style_normal.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    # ----------------------------------------------------
    # TITLE
    # ----------------------------------------------------
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(12)
    run_title = p_title.add_run("Wireless Digital Communication System Simulation Using Source Coding, LDPC Error Correction, and TCP/IP Networking")
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(18)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x00, 0x28, 0x55)

    # ----------------------------------------------------
    # THREE AUTHORS BLOCK (Border-free 3-column table)
    # ----------------------------------------------------
    author_table = doc.add_table(rows=2, cols=3)
    author_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    author_table.autofit = False

    col_widths = [Inches(2.4), Inches(2.4), Inches(2.4)]
    for row in author_table.rows:
        for i, cell in enumerate(row.cells):
            cell.width = col_widths[i]

    # Row 0: Author Names & Reg Numbers
    authors = [
        ("Aravind M", "Registration No.: 23BCE7551"),
        ("Sai Chandu", "Registration No.: 23BCE20304"),
        ("Rahul L", "Registration No.: 23BCE7890")
    ]
    for i, (name, reg) in enumerate(authors):
        cell = author_table.cell(0, i)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        r_name = p.add_run(name)
        r_name.font.bold = True
        r_name.font.size = Pt(10.5)
        p.add_run("\n" + reg).font.size = Pt(9)

    # Row 1: Affiliations
    for i in range(3):
        cell = author_table.cell(1, i)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        r_affil = p.add_run("School of Computer Science and Engineering\nVIT-AP University, Amaravati, India")
        r_affil.font.italic = True
        r_affil.font.size = Pt(8.5)
        r_affil.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

    # Abstract Paragraph
    p_abs = doc.add_paragraph()
    p_abs.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_abs.paragraph_format.space_before = Pt(8)
    p_abs.paragraph_format.space_after = Pt(4)
    p_abs.paragraph_format.left_indent = Inches(0.2)
    p_abs.paragraph_format.right_indent = Inches(0.2)
    r_abs_hdr = p_abs.add_run("Abstract—")
    r_abs_hdr.font.bold = True
    r_abs_hdr.font.italic = True
    r_abs_body = p_abs.add_run(
        "Reliable information transmission across digital communication networks requires the harmonious integration of data "
        "compression, forward error correction (FEC), transport framing, and channel modulation. This paper presents the architecture, "
        "implementation, and empirical evaluation of an end-to-end digital communication simulation platform developed in Python with an "
        "interactive Streamlit graphical interface. The system couples lossless source coding (finite-precision Arithmetic coding and "
        "universal adaptive Lempel-Ziv-Welch dictionary coding) with systematic Low-Density Parity-Check (LDPC) channel coding based on a "
        "rate-1/2 (64, 32) code decoded via log-domain Belief Propagation (Sum-Product and Min-Sum algorithms). To bridge theoretical "
        "information theory with practical networking, the platform implements a dual-mode operational architecture: (1) a live wireless network "
        "transmission mode operating over TCP/IP stream sockets using a 36-byte versioned binary frame with IEEE 802.3 CRC32 integrity checks and "
        "sequence-confirmed acknowledgments, and (2) an analog wireless physical layer simulation executing baseband Binary Phase Shift Keying (BPSK) "
        "modulation over an Additive White Gaussian Noise (AWGN) channel. Rigorous Monte Carlo experiments across Eb/N0 sweeps from 0.0 to 10.0 dB "
        "demonstrate that the LDPC (64, 32) code achieves steep waterfall error suppression, reducing a pre-FEC bit error rate of 5.71e-2 at 4.0 dB "
        "to a post-FEC residual rate of 1.32e-3 (43.3x error reduction gain) and achieving zero residual errors at Eb/N0 >= 7.0 dB with 100% "
        "exact message reconstruction."
    )
    r_abs_body.font.bold = True
    r_abs_body.font.size = Pt(9)

    # Keywords Paragraph
    p_kw = doc.add_paragraph()
    p_kw.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_kw.paragraph_format.space_before = Pt(2)
    p_kw.paragraph_format.space_after = Pt(12)
    p_kw.paragraph_format.left_indent = Inches(0.2)
    p_kw.paragraph_format.right_indent = Inches(0.2)
    r_kw_hdr = p_kw.add_run("Keywords—")
    r_kw_hdr.font.bold = True
    r_kw_hdr.font.italic = True
    r_kw_body = p_kw.add_run(
        "Wireless digital communication, source coding, Arithmetic coding, LZW, Low-Density Parity-Check (LDPC), BPSK modulation, "
        "AWGN channel, Bit Error Rate (BER), CRC32 integrity check, TCP/IP networking, communication system simulation."
    )
    r_kw_body.font.bold = True
    r_kw_body.font.size = Pt(9)

    # ----------------------------------------------------
    # SECTION 2: Continuous Break into Two Columns
    # ----------------------------------------------------
    sec2 = doc.add_section(WD_SECTION.CONTINUOUS)
    sec2.top_margin = Inches(0.6)
    sec2.bottom_margin = Inches(0.6)
    sec2.left_margin = Inches(0.6)
    sec2.right_margin = Inches(0.6)

    # Enable 2 Columns
    sectPr = sec2._sectPr
    cols = sectPr.xpath('./w:cols')
    if cols:
        cols[0].set(qn('w:num'), '2')
        cols[0].set(qn('w:space'), '540')  # 0.375 inch gap
    else:
        sectPr.append(parse_xml(f'<w:cols {nsdecls("w")} w:num="2" w:space="540"/>'))

    def add_h1(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(3)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x28, 0x55)
        return h

    def add_h2(text):
        h = doc.add_paragraph()
        h.paragraph_format.space_before = Pt(6)
        h.paragraph_format.space_after = Pt(2)
        h.paragraph_format.keep_with_next = True
        r = h.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(9)
        r.font.bold = True
        r.font.italic = True
        return h

    def add_p(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.line_spacing = 1.05
        r = p.add_run(text)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(8.5)
        return p

    def add_eq(text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(text)
        r.font.name = 'Courier New'
        r.font.size = Pt(8)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x1F, 0x3F)
        return p

    def add_img(img_path, caption):
        if os.path.exists(img_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(2)
            p.add_run().add_picture(img_path, width=Inches(3.4))
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(6)
            r = p_cap.add_run(caption)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7.5)
            r.font.italic = True

    # ----------------------------------------------------
    # SECTION I: INTRODUCTION
    # ----------------------------------------------------
    add_h1("I. INTRODUCTION")
    add_p(
        "Modern telecommunications infrastructure demands high-fidelity, high-throughput digital transmission across physical channels "
        "inherently impaired by thermal noise, dispersion, and channel perturbations. In Shannon's foundational mathematical theory of "
        "communication [1], the communication problem is partitioned into two distinct operations governed by the Source-Channel Separation Theorem: "
        "source coding, which eliminates statistical redundancy from the information source to approach the empirical entropy H(X), and channel coding, "
        "which systematically introduces controlled algebraic redundancy to protect transmitted symbols up to the channel capacity C."
    )
    add_p(
        "While classic classroom curricula frequently treat these mechanisms in theoretical isolation—often assuming ideal noiseless conduits or abstract "
        "bit-flip models—real-world engineering deployments necessitate an integrated pipeline. In practical wireless and networked systems, raw binary data "
        "must be packaged into structured wire frames, protected with forward error correction, modulated into baseband waveforms, transmitted across "
        "physical media, and verified through link-layer cyclic redundancy checks (CRC) and transport-layer protocols such as TCP/IP [10]."
    )
    add_p(
        "Crucially, an important architectural distinction must be maintained between transport-layer network reliability and physical-layer error correction. "
        "Transport protocols such as TCP provide reliable, ordered byte delivery by utilizing automatic repeat request (ARQ) retransmissions over lower-layer "
        "hardware interfaces. Consequently, observing zero packet losses over a local Wi-Fi or loopback TCP socket does not imply that the underlying physical "
        "channel is noiseless; rather, hardware-level physical decoders and transport-level retransmissions mask underlying transmission impairments. "
        "Conversely, physical-layer forward error correction must be evaluated by observing continuous analog signal-to-noise ratios (Eb/N0), calculating "
        "channel log-likelihood ratios (LLRs), and measuring pre-FEC versus post-FEC bit error rates (BER)."
    )
    add_p(
        "To address these pedagogical and engineering objectives, this project designs, implements, and evaluates an extensible digital communication "
        "system simulation. The contributions of this work are threefold: (1) We implement a complete, reproducible software transceiver pipeline combining "
        "finite-precision Arithmetic coding, adaptive LZW source coding, and systematic (64, 32) LDPC forward error correction decoded via log-domain Belief "
        "Propagation (Sum-Product and Min-Sum). (2) We formulate a versioned binary wire frame protocol featuring a 36-byte structured header, sequence counters, "
        "IEEE 802.3 CRC32 checksums, and a thread-safe TCP/IP socket transceiver with continuous streaming and bounded backpressure monitoring. (3) We simulate "
        "baseband BPSK modulation over a wireless AWGN link, benchmarking theoretical uncoded BER against empirical LDPC, Polar (64, 32), and Hamming (7, 4) "
        "codes, providing verifiable Monte Carlo performance curves and evaluating the sensitivity of source decompression to uncorrected channel errors."
    )

    # ----------------------------------------------------
    # SECTION II: RELATED WORK
    # ----------------------------------------------------
    add_h1("II. RELATED WORK")
    add_p(
        "The theoretical foundations of digital communications originate from Shannon's 1948 paper [1], which established fundamental limits on source "
        "compression and channel capacity. In 1962, Gallager introduced Low-Density Parity-Check (LDPC) codes [2], demonstrating that linear codes defined "
        "by sparse parity-check matrices can be decoded in linear time via iterative message passing. However, computational constraints delayed their "
        "widespread adoption until MacKay and Neal [3] rediscovered LDPC codes in 1996, proving that log-domain Belief Propagation over bipartite Tanner graphs "
        "approaches the Shannon limit within fractions of a decibel."
    )
    add_p(
        "In standardized engineering, LDPC codes were codified in IEEE Std 802.3an-2006 for 10GBASE-T Ethernet [8], utilizing quasi-cyclic structures to guarantee "
        "bit error rates below 10^-12 over copper twisted-pair cabling. Simultaneously, LDPC codes were adopted in modern satellite broadcasting (DVB-S2) and "
        "5G New Radio (3GPP TS 38.212) data channels due to their high parallelization efficiency and low decoding latency compared to convolutional turbo codes. "
        "In 2009, Arikan proved that Polar codes achieve the symmetric capacity of discrete memoryless channels using channel polarization and Successive "
        "Cancellation (SC) decoding [4], leading to their adoption in 5G control channels. Earlier linear block codes, such as Hamming's (7, 4) code [11], "
        "remain vital pedagogical baselines for single-error correction and syndrome decoding."
    )
    add_p(
        "On the source coding front, universal data compression algorithms operate without requiring static, pre-computed symbol codebooks. Welch's 1984 "
        "formalization of the Lempel-Ziv-Welch (LZW) algorithm [5] established an adaptive dictionary method that dynamically parses recurring symbol sequences "
        "into fixed-width tokens. Concurrently, Rissanen and Langdon [6], followed by Witten, Neal, and Cleary [7], developed practical finite-precision "
        "Arithmetic coding, which represents entire message streams as a single interval in [0, 1), breaking the integer-length penalty of Huffman coding and "
        "achieving near-entropy compression. In packet-switched communication, framing protocols rely on Cyclic Redundancy Checks (CRC), formalized by "
        "Peterson and Brown [9], to detect burst perturbations with negligible computational overhead. Modern network transport implementations universally rely "
        "on TCP [10] for reliable flow-controlled stream delivery. Comprehensive treatments of digital modulation over AWGN channels, soft demodulation, and "
        "error probability calculations are detailed by Proakis and Salehi [12]."
    )

    # ----------------------------------------------------
    # SECTION III: PROPOSED SYSTEM ARCHITECTURE
    # ----------------------------------------------------
    add_h1("III. PROPOSED SYSTEM ARCHITECTURE")
    add_p(
        "The implemented system architecture comprises three primary functional domains: the Transmitter, the Dual Communication Transport Layer, and "
        "the Receiver, as shown in Fig. 1."
    )
    add_h2("A. Transmitter Processing Chain")
    add_p(
        "The transmitter processes arbitrary UTF-8 text messages or structured telemetry bitstreams through four sequential stages: "
        "(1) Binary Serialization: Input character sequences are converted into 8-bit ASCII/UTF-8 byte streams and unpacked into binary bit vectors. "
        "(2) Lossless Source Coding: Redundancy is reduced using either finite-precision integer Arithmetic coding or 12-bit adaptive LZW universal dictionary coding. "
        "(3) Channel Forward Error Correction: The compressed stream is partitioned into K=32 bit blocks and encoded into N=64 bit systematic codewords using the "
        "LDPC (64, 32) encoder, appending zero-padding if necessary. (4) Binary Frame Assembly: Coded bits, padding indicators, and flags are packed into a "
        "versioned binary frame with a 36-byte header and IEEE 802.3 CRC32 checksum."
    )
    add_h2("B. Dual Communication Transport Media")
    add_p(
        "A critical feature of our system is the explicit decoupling between live network transport and physical channel simulation: "
        "(1) Mode A & B (Live Wireless Network Transport): Operates over live TCP/IP stream sockets bound to local Wi-Fi or loopback interfaces (default port 8550). "
        "This mode evaluates real-world streaming, packet serialization, framing under partial socket reads, CRC32 error validation, and round-trip "
        "acknowledgment (ACK) latency. (2) Mode C (Physical Wireless AWGN Channel Simulation): Isolates the analog physical layer by bypassing TCP ARQ mechanisms. "
        "Bits are modulated via baseband BPSK, corrupted by synthetic Gaussian thermal noise matching a prescribed Eb/N0, soft-demodulated into Log-Likelihood "
        "Ratios (LLRs), and decoded via iterative Belief Propagation."
    )
    add_h2("C. Receiver Processing Chain")
    add_p(
        "At the receiver, incoming bitstreams or network frames undergo inverse processing: (1) Frame Parsing & CRC32 Verification: The wire receiver reads "
        "the 36-byte header, verifies magic bytes and length fields, and computes the 32-bit CRC. Frames with checksum mismatches are rejected. "
        "(2) LDPC Decoding: In physical simulation, soft channel samples are decoded using log-domain Belief Propagation. In network socket mode, "
        "hard decision bits are verified against the parity-check matrix H. Systematic information bits are extracted, and zero-padding is removed. "
        "(3) Lossless Source Decompression: The recovered bitstream is decompressed using inverse Arithmetic or LZW decoding. (4) Exact Reconstruction "
        "Verification: The reconstructed message is compared against the transmitted message to verify 100% bit-for-bit fidelity."
    )

    add_img(os.path.join(FIG_DIR, "fig1_overall_architecture.png"), "Fig. 1. Overall system architecture illustrating the transmitter, dual transport media (TCP socket vs. BPSK-AWGN simulation), and receiver.")

    # ----------------------------------------------------
    # SECTION IV: METHODOLOGY AND IMPLEMENTATION
    # ----------------------------------------------------
    add_h1("IV. METHODOLOGY AND IMPLEMENTATION")
    add_h2("A. Source Coding Algorithms")
    add_p(
        "1) Finite-Precision Arithmetic Codec: Our Arithmetic codec utilizes 32-bit integer register arithmetic to guarantee platform-independent, "
        "exact lossless compression. Symbol frequencies are computed with Laplace add-one smoothing over byte alphabet Sigma = {0,...,255} plus an EOF symbol (256):"
    )
    add_eq("C(s) = 1 + sum(I(x_i = s)),  Total = sum(C(s))   (1)")
    add_p(
        "Encoding maintains an active search range [L, H) in 32-bit unsigned integers. Bounds are updated iteratively based on cumulative frequencies F(s), "
        "and renormalized via bit-shifting under E1, E2, and E3 scaling conditions. Exact reconstruction is achieved through inverse interval subdivision."
    )
    add_p(
        "2) Universal LZW Dictionary Codec: The LZW codec dynamically builds an adaptive dictionary of recurring character n-grams, mapping variable-length "
        "symbol sequences to fixed 12-bit binary integers (max table size 2^12 = 4096). The dictionary is initialized with 256 single-byte entries. When the "
        "dictionary capacity is reached, table growth freezes gracefully without desynchronization."
    )

    add_h2("B. Systematic LDPC Forward Error Correction")
    add_p(
        "The channel codec implements a systematic (N=64, K=32, M=32) LDPC code with code rate R = K/N = 0.5. The parity-check matrix H is structured as "
        "H = [P | I_32], where P is a 32x32 sparse matrix with regular column degree d_v = 3. The systematic generator matrix G = [I_32 | P^T] satisfies "
        "G * H^T = 0 mod 2. For any 32-bit information vector m, the 64-bit codeword is c = [m | m * P^T mod 2]."
    )
    add_p(
        "Iterative decoding operates over the bipartite Tanner graph using the log-domain Sum-Product algorithm. Variable-to-check and check-to-variable "
        "messages are updated as follows:"
    )
    add_eq("q_mn = L_n + sum_{c in C(n)\\m} r_cn   (2)")
    add_eq("r_mn = 2 atanh [ prod_{j in V(m)\\n} tanh(q_mj / 2) ]   (3)")
    add_p(
        "where L_n is the channel LLR. Numerical stability is ensured by clipping q_mj/2 to [-19.0, +19.0]. Total posterior LLRs Q_n = L_n + sum_{c in C(n)} r_cn "
        "determine hard decisions: c_hat_n = 0 if Q_n >= 0, else 1. The decoder terminates immediately when syndrome H * c_hat^T = 0 mod 2, up to max 25 iterations."
    )

    add_h2("C. Binary Frame Protocol & CRC32")
    add_p(
        "To ensure robust streaming across byte sockets, we implement a 36-byte binary wire header shown in Fig. 2. Fields include: Magic bytes (4B: b'WIRL'), "
        "Version (1B: 0x01), Type (1B: DATA=1, ACK=2, STREAM=3), Flags (2B bitmask), Sequence Number (4B uint32), Original Payload Size (4B), Source Compressed Size (4B), "
        "Payload Length (4B), CRC32 Checksum (4B IEEE 802.3), Status Code (1B), and Reserved (7B). Partial socket reads are handled via dedicated recv() loops."
    )

    add_img(os.path.join(FIG_DIR, "fig2_frame_protocol_ack.png"), "Fig. 2. 36-byte binary wire frame layout and two-way TCP acknowledgment protocol sequence.")

    add_h2("D. Physical BPSK-AWGN Channel Simulation")
    add_p(
        "In Mode C, binary bits b_i in {0, 1} are modulated via antipodal BPSK signaling: s_i = 1.0 - 2.0 b_i in {+1.0 V, -1.0 V}. For target Eb/N0 in dB and code rate R, "
        "channel noise standard deviation is scaled as:"
    )
    add_eq("sigma = 1 / sqrt( 2 * R * 10^(Eb/N0 / 10) )   (4)")
    add_p(
        "Received samples y_i = s_i + n_i, where n_i ~ N(0, sigma^2), are soft-demodulated into exact channel LLRs via L_i = (2 / sigma^2) * y_i. "
        "Theoretical uncoded BPSK error probability is P_b = 0.5 erfc( sqrt(10^(Eb/N0 / 10)) )."
    )

    # ----------------------------------------------------
    # SECTION V: EXPERIMENTAL SETUP
    # ----------------------------------------------------
    add_h1("V. EXPERIMENTAL SETUP")
    add_p(
        "The simulation platform was developed and evaluated under the following verified technical parameters: "
        "(1) Python 3.11.9 runtime with NumPy 2.4.6, Matplotlib 3.11.2, ReportLab 5.0.1, and Pytest 9.1.1 on Windows 11 Pro. "
        "(2) Rate-1/2 LDPC (64, 32) codec with Gallager d_v=3 and 25 max BP iterations. (3) Benchmark codecs: Systematic Polar (64, 32) with "
        "Successive Cancellation decoding at design SNR 3.0 dB, and Systematic Hamming (7, 4) with syndrome table decoding. "
        "(4) Monte Carlo evaluation: Eb/N0 swept from 0.0 to 10.0 dB in steps of 1.0 dB with 25,600 bits tested per point (400 LDPC blocks/point). "
        "Multi-trial physical channel experiments simulated across 10 independent noise realizations (600 LDPC blocks, 38,400 codeword bits). "
        "(5) Streamlit interactive 5-tab web dashboard for real-time live messaging, continuous source streaming, and channel analysis."
    )

    # ----------------------------------------------------
    # SECTION VI: RESULTS AND DISCUSSION
    # ----------------------------------------------------
    add_h1("VI. RESULTS AND DISCUSSION")
    add_h2("A. BER Waterfall Performance in AWGN")
    add_p(
        "The measured bit error rates across the Eb/N0 sweep are reported in Table I and plotted in Fig. 3. "
        "The simulated uncoded BPSK curve matches the theoretical error function with high precision (e.g. 0.05617 vs 0.05628 at 1.0 dB). "
        "The LDPC (64, 32) Sum-Product decoder exhibits a steep waterfall descent starting around Eb/N0 = 3.0 dB. "
        "Between 2.0 dB and 4.0 dB, the post-FEC BER drops by over an order of magnitude (from 2.24e-2 to 1.99e-3). "
        "At Eb/N0 >= 7.0 dB, both Sum-Product and Min-Sum LDPC decoders achieve zero residual errors (BER = 0.0000), enabling 100% exact message reconstruction."
    )

    # Insert Table I
    t1_rows = [
        ["Eb/N0", "Theory", "Sim.", "Hamming", "Polar", "LDPC", "LDPC"],
        ["(dB)", "Uncoded", "Uncoded", "(7, 4)", "(64, 32)", "Min-Sum", "Sum-Prod."],
        ["0.0", "0.07865", "0.08191", "0.11934", "0.19402", "0.08973", "0.08672"],
        ["1.0", "0.05628", "0.05617", "0.08152", "0.10172", "0.04906", "0.04727"],
        ["2.0", "0.03751", "0.03781", "0.05586", "0.04004", "0.02473", "0.02238"],
        ["3.0", "0.02288", "0.02285", "0.03363", "0.01203", "0.00668", "0.00617"],
        ["4.0", "0.01250", "0.01285", "0.01684", "0.00238", "0.00285", "0.00199"],
        ["5.0", "0.00595", "0.00543", "0.00641", "0.00000", "0.00039", "0.00035"],
        ["6.0", "0.00239", "0.00234", "0.00184", "0.00000", "7.81e-5", "7.81e-5"],
        ["7.0", "0.00077", "0.00059", "0.00039", "0.00000", "0.00000", "0.00000"],
        ["8.0", "0.00019", "7.81e-5", "0.00000", "0.00000", "0.00000", "0.00000"],
        ["9.0", "3.36e-5", "0.00000", "7.81e-5", "0.00000", "0.00000", "0.00000"],
        ["10.0", "3.87e-6", "0.00000", "0.00000", "0.00000", "0.00000", "0.00000"],
    ]
    tbl1 = doc.add_table(rows=len(t1_rows), cols=7)
    tbl1.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl1.autofit = True
    set_table_borders(tbl1)
    for r_idx, row in enumerate(t1_rows):
        for c_idx, val in enumerate(row):
            cell = tbl1.cell(r_idx, c_idx)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7)
            if r_idx < 2:
                r.font.bold = True
                set_cell_background(cell, "EAF2F8")
            elif c_idx == 6:
                r.font.bold = True

    p_cap1 = doc.add_paragraph()
    p_cap1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap1.paragraph_format.space_after = Pt(6)
    r_cap1 = p_cap1.add_run("TABLE I: Measured Bit Error Rate (BER) vs. Eb/N0 in AWGN (25,600 Bits/Point)")
    r_cap1.font.size = Pt(7.5)
    r_cap1.font.bold = True

    add_img(os.path.join(FIG_DIR, "fig3_awgn_ber_waterfall.png"), "Fig. 3. Measured BER vs. Eb/N0 waterfall curves over the simulated BPSK-AWGN physical channel.")

    add_h2("B. Pre-FEC vs. Post-FEC Error Suppression Gain")
    add_p(
        "In our 10-trial Monte Carlo evaluation at Eb/N0 = 4.0 dB (38,400 total codeword bits, 18,960 information bits), the channel introduced "
        "2,191 hard decision bit errors (pre-FEC BER = 5.71e-2). LDPC Belief Propagation corrected 2,166 errors, leaving only 25 residual bit errors "
        "(post-FEC BER = 1.32e-3), corresponding to an empirical error reduction gain of Gain = 5.7057e-2 / 1.3186e-3 = 43.3x. "
        "At Eb/N0 = 7.0 dB, the LDPC decoder eliminated all 461 channel bit errors across all 600 blocks (pre-FEC BER = 1.20e-2 -> post-FEC BER = 0.0000), "
        "yielding infinite empirical gain and 100% exact recovery."
    )

    add_img(os.path.join(FIG_DIR, "fig4_pre_vs_post_fec.png"), "Fig. 4. Pre-FEC channel slicer BER vs. Post-FEC LDPC residual BER and empirical error suppression gain.")

    add_h2("C. Source Compression Study & Overhead Analysis")
    add_p(
        "Empirical results from our source compression benchmark across diverse information topologies are summarized in Table II and Fig. 5. "
        "Correlated Markov streams (p01=0.05, p10=0.05) achieve a compression ratio of 1.686x (40.67% space savings). "
        "Conversely, for high-entropy sources (H ~ 1.0) and uniform pseudo-random bits, dictionary compression causes data expansion (CR = 0.677x, -47.66% space savings), "
        "empirically validating Shannon's Source Coding Theorem. Furthermore, on short text strings (e.g. 39 bytes), Arithmetic coding incurs a frequency table header "
        "overhead expanding data to 119 bytes (CR = 0.33x), while LZW expands to 54 bytes (CR = 0.72x) due to initial unigram dictionary initialization."
    )

    # Insert Table II
    t2_rows = [
        ["Source Topology", "H(X) (b)", "Raw (b)", "Comp (b)", "CR", "Savings (%)"],
        ["Structured Telemetry", "4.7612", "5216", "4680", "1.115x", "+10.28%"],
        ["Markov (p01=0.05)", "0.9996", "8192", "4860", "1.686x", "+40.67%"],
        ["Markov (p01=0.10)", "0.9228", "8192", "7956", "1.030x", "+2.88%"],
        ["Markov (p01=0.25)", "0.9996", "8192", "10944", "0.749x", "-33.59%"],
        ["Uniform Random", "1.0000", "8192", "12096", "0.677x", "-47.66%"],
    ]
    tbl2 = doc.add_table(rows=len(t2_rows), cols=6)
    tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl2.autofit = True
    set_table_borders(tbl2)
    for r_idx, row in enumerate(t2_rows):
        for c_idx, val in enumerate(row):
            cell = tbl2.cell(r_idx, c_idx)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7)
            if r_idx == 0:
                r.font.bold = True
                set_cell_background(cell, "EAF2F8")

    p_cap2 = doc.add_paragraph()
    p_cap2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap2.paragraph_format.space_after = Pt(6)
    r_cap2 = p_cap2.add_run("TABLE II: Source Compression Benchmark Across Information Topologies")
    r_cap2.font.size = Pt(7.5)
    r_cap2.font.bold = True

    add_img(os.path.join(FIG_DIR, "fig5_source_coding_entropy.png"), "Fig. 5. Source coding trade-off: empirical entropy vs. compression ratio across source topologies.")

    add_h2("D. Live Wireless Socket Transmission (Mode A)")
    add_p(
        "Table III and Fig. 6 report the measured live network performance transmitting 'Hello, this is my wireless ITC project!' (39 bytes). "
        "All frames achieved valid CRC32 verification and sequence-confirmed delivery. Measured round-trip latency was 14.20 ms for raw text, "
        "24.64 ms for LZW, and 48.60 ms for Arithmetic coding, reflecting socket streaming overhead and syndrome verification."
    )

    # Insert Table III
    t3_rows = [
        ["Codec", "Orig (B)", "Src (B)", "Frame (B)", "RTT (ms)", "Fidelity"],
        ["Raw Text", "39", "39", "114", "14.20", "100% (CRC OK)"],
        ["Arithmetic", "39", "119", "242", "48.60", "100% (CRC OK)"],
        ["LZW (12-bit)", "39", "54", "114", "24.64", "100% (CRC OK)"],
    ]
    tbl3 = doc.add_table(rows=len(t3_rows), cols=6)
    tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl3.autofit = True
    set_table_borders(tbl3)
    for r_idx, row in enumerate(t3_rows):
        for c_idx, val in enumerate(row):
            cell = tbl3.cell(r_idx, c_idx)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(7)
            if r_idx == 0:
                r.font.bold = True
                set_cell_background(cell, "EAF2F8")

    p_cap3 = doc.add_paragraph()
    p_cap3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap3.paragraph_format.space_after = Pt(6)
    r_cap3 = p_cap3.add_run("TABLE III: Live Wireless Socket Transmission Metrics (Mode A)")
    r_cap3.font.size = Pt(7.5)
    r_cap3.font.bold = True

    add_img(os.path.join(FIG_DIR, "fig6_socket_latency_overhead.png"), "Fig. 6. Wire frame size and round-trip ACK latency under live TCP socket transmission.")

    add_h2("E. Decompression Sensitivity to Channel Errors")
    add_p(
        "A critical observation from Mode C simulation is the catastrophic sensitivity of compressed bitstreams to residual channel errors. "
        "At Eb/N0 = 4.0 dB, two residual block errors corrupted the compressed bitstream, causing the Arithmetic decompressor to raise a "
        "MalformedStreamException and failing text recovery. At Eb/N0 >= 7.0 dB, where the LDPC decoder achieved zero residual errors, 100% exact "
        "reconstruction was restored. This proves that powerful FEC is mandatory when transmitting source-compressed information."
    )

    # ----------------------------------------------------
    # SECTION VII: LIMITATIONS
    # ----------------------------------------------------
    add_h1("VII. LIMITATIONS")
    add_p(
        "Several practical engineering constraints must be noted: (1) Simulated AWGN vs. Real Radio Propagation: The physical channel models "
        "ideal thermal noise, whereas real-world Wi-Fi links experience multipath reflections, Rayleigh/Rician fading, Doppler shifts, and hardware "
        "carrier offsets. (2) TCP ARQ Masking: Sockets operate over TCP, which guarantees reliable delivery via retransmissions, masking raw radio "
        "packet loss. (3) Finite Blocklength: The implemented LDPC code has blocklength N=64. Standard industrial LDPC codes (e.g. IEEE 802.3an N=2048) "
        "exhibit much steeper waterfall thresholds. (4) Simulation Runtime: Evaluating extreme error floors (BER < 10^-8) requires transmitting "
        "billions of bits, exceeding interactive execution constraints."
    )

    # ----------------------------------------------------
    # SECTION VIII: CONCLUSION AND FUTURE WORK
    # ----------------------------------------------------
    add_h1("VIII. CONCLUSION AND FUTURE WORK")
    add_p(
        "This paper presented the design, implementation, and empirical verification of an end-to-end digital communication simulation system. "
        "By integrating finite-precision Arithmetic coding, adaptive LZW compression, systematic rate-1/2 LDPC (64, 32) coding with log-domain "
        "Belief Propagation, and a 36-byte versioned binary frame protocol with CRC32 integrity verification, the system successfully bridges "
        "theoretical information theory and real-world networking. Empirical evaluations demonstrated that the LDPC decoder achieves a 43.3x "
        "error suppression gain at Eb/N0 = 4.0 dB and delivers error-free transmission (BER = 0.0000) with 100% exact text reconstruction at Eb/N0 >= 7.0 dB."
    )
    add_p(
        "Future extensions include: (1) Implementing higher-order digital modulations, such as QPSK, 16-QAM, and OFDM. "
        "(2) Scaling LDPC codes to standardized quasi-cyclic parity-check matrices (N >= 1024) utilizing GPU-accelerated Belief Propagation. "
        "(3) Interfacing the simulation with Software-Defined Radio (SDR) hardware (e.g. RTL-SDR, HackRF, or USRP) to conduct over-the-air RF experiments."
    )

    # ----------------------------------------------------
    # REFERENCES
    # ----------------------------------------------------
    add_h1("REFERENCES")
    refs = [
        "[1] C. E. Shannon, \"A mathematical theory of communication,\" The Bell System Technical Journal, vol. 27, no. 3, pp. 379–423, Jul. 1948. DOI: 10.1002/j.1538-7305.1948.tb01338.x",
        "[2] R. G. Gallager, \"Low-density parity-check codes,\" IRE Transactions on Information Theory, vol. 8, no. 1, pp. 21–28, Jan. 1962. DOI: 10.1109/TIT.1962.1057683",
        "[3] D. J. C. MacKay and R. M. Neal, \"Near Shannon limit performance of low density parity check codes,\" Electronics Letters, vol. 32, no. 18, pp. 1645–1646, Aug. 1996. DOI: 10.1049/el:19961141",
        "[4] E. Arıkan, \"Channel polarization: A method for constructing capacity-achieving codes for symmetric binary-input memoryless channels,\" IEEE Transactions on Information Theory, vol. 55, no. 7, pp. 3051–3073, Jul. 2009. DOI: 10.1109/TIT.2009.2021379",
        "[5] T. A. Welch, \"A technique for high-performance data compression,\" IEEE Computer, vol. 17, no. 6, pp. 8–19, Jun. 1984. DOI: 10.1109/MC.1984.1659158",
        "[6] J. Rissanen and G. G. Langdon, \"Arithmetic coding,\" IBM Journal of Research and Development, vol. 23, no. 2, pp. 149–162, Mar. 1979. DOI: 10.1147/rd.232.0149",
        "[7] I. H. Witten, R. M. Neal, and J. G. Cleary, \"Arithmetic coding for data compression,\" Communications of the ACM, vol. 30, no. 6, pp. 520–540, Jun. 1987. DOI: 10.1145/214762.214771",
        "[8] IEEE Standard for Information Technology—Specific Requirements Part 3: CSMA/CD Access Method and Physical Layer Specifications Amendment 4: 10 Gb/s Operation, Type 10GBASE-T, IEEE Std 802.3an-2006, pp. 1–181, Sep. 2006. DOI: 10.1109/IEEESTD.2006.246283",
        "[9] W. W. Peterson and D. T. Brown, \"Cyclic codes for error detection,\" Proceedings of the IRE, vol. 49, no. 1, pp. 228–235, Jan. 1961. DOI: 10.1109/JRPROC.1961.287814",
        "[10] J. Postel, \"Transmission Control Protocol,\" RFC 793, Internet Engineering Task Force (IETF), Sep. 1981. DOI: 10.17487/RFC0793",
        "[11] R. W. Hamming, \"Error detecting and error correcting codes,\" The Bell System Technical Journal, vol. 29, no. 2, pp. 147–160, Apr. 1950. DOI: 10.1002/j.1538-7305.1950.tb00463.x",
        "[12] J. G. Proakis and M. Salehi, Digital Communications, 5th ed. New York, NY, USA: McGraw-Hill, 2008."
    ]

    for ref in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.space_after = Pt(2.5)
        p_ref.paragraph_format.left_indent = Inches(0.2)
        p_ref.paragraph_format.first_line_indent = Inches(-0.2)
        r = p_ref.add_run(ref)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(7.5)

    doc.save(filename)
    print(f"Successfully generated DOCX: {filename}")


if __name__ == "__main__":
    build_docx()
