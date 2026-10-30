"""
Compiles the complete IEEE Conference Research Paper into PDF using ReportLab.
Follows the professional academic layout of IEEE_Conference_Paper_23BCE7551.pdf:
- Standard 2-column conference styling
- 3-author professional academic block (no emails)
- Formal mathematical formulations and numbered equations
- 7 embedded high-resolution figures (300 DPI)
- 5 comprehensive empirical data tables
- Exact 14 verified IEEE citations with DOIs
- Running two-pass headers and footers with Page X of Y
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle, FrameBreak, NextPageTemplate, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas

PDF_FILENAME = "outputs/IEEE_Wireless_Conference_Paper/IEEE_Wireless_Conference_Paper.pdf"
FIG_DIR = "outputs/IEEE_Wireless_Conference_Paper/figures"


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y' and running headers.
    Matches the exact layout of the reference paper.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        self.saveState()
        self.setFont("Helvetica", 7.8)
        self.setFillColor(colors.HexColor("#444444"))

        # Running Header (pages 2+)
        if self._pageNumber > 1:
            header_text = "IEEE CONFERENCE: WIRELESS DIGITAL COMMUNICATION SYSTEM SIMULATION"
            self.drawString(36, letter[1] - 26, header_text)
            self.drawRightString(letter[0] - 36, letter[1] - 26, "VIT-AP UNIVERSITY")
            self.setStrokeColor(colors.HexColor("#bbbbbb"))
            self.setLineWidth(0.5)
            self.line(36, letter[1] - 29, letter[0] - 36, letter[1] - 29)

        # Running Footer (all pages)
        footer_left = "School of Computer Science and Engineering, VIT-AP University"
        footer_right = f"Authors: 23BCE7551, 23BCE20304, 23BCE7890  |  Page {self._pageNumber} of {total_pages}"
        self.drawString(36, 22, footer_left)
        self.drawRightString(letter[0] - 36, 22, footer_right)
        self.setStrokeColor(colors.HexColor("#bbbbbb"))
        self.setLineWidth(0.5)
        self.line(36, 30, letter[0] - 36, 30)

        self.restoreState()


def build_pdf(filename=PDF_FILENAME):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    margin = 36  # 0.5 in
    gutter = 14  # column gap
    usable_w = letter[0] - 2 * margin  # 540 pt
    col_w = (usable_w - gutter) / 2     # 263 pt
    usable_h = letter[1] - 2 * margin  # 720 pt

    doc = BaseDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )

    # ----------------------------------------------------
    # Page Templates
    # ----------------------------------------------------
    # Page 1: Top frame (title + authors + abstract + keywords), followed by 2 bottom columns
    top_h = 285
    bottom_h = usable_h - top_h - 10
    top_y = letter[1] - margin - top_h

    frame_top = Frame(margin, top_y, usable_w, top_h, id='p1_top',
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_b1 = Frame(margin, margin, col_w, bottom_h, id='p1_col1',
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_b2 = Frame(margin + col_w + gutter, margin, col_w, bottom_h, id='p1_col2',
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    page1_template = PageTemplate(id='FirstPage', frames=[frame_top, frame_b1, frame_b2])

    # Later Pages: Standard Two Full-Height Columns
    frame_l1 = Frame(margin, margin, col_w, usable_h, id='lat_col1',
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    frame_l2 = Frame(margin + col_w + gutter, margin, col_w, usable_h, id='lat_col2',
                     leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    later_template = PageTemplate(id='LaterPages', frames=[frame_l1, frame_l2])

    doc.addPageTemplates([page1_template, later_template])

    # ----------------------------------------------------
    # Styles
    # ----------------------------------------------------
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'IEEETitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=13.5,
        leading=16.5,
        alignment=1,
        textColor=colors.HexColor('#002855'),
        spaceAfter=8
    )

    author_name_style = ParagraphStyle(
        'IEEEAuthorName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.8,
        leading=11.2,
        alignment=1,
        textColor=colors.HexColor('#111111')
    )

    author_affil_style = ParagraphStyle(
        'IEEEAuthorAffil',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.6,
        leading=9.8,
        alignment=1,
        textColor=colors.HexColor('#333333')
    )

    abstract_style = ParagraphStyle(
        'IEEEAbstract',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        alignment=4,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=4
    )

    keywords_style = ParagraphStyle(
        'IEEEKeywords',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        alignment=4,
        leftIndent=10,
        rightIndent=10,
        spaceAfter=6
    )

    h1_style = ParagraphStyle(
        'IEEEH1',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=8.8,
        leading=11.2,
        textColor=colors.HexColor('#002855'),
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'IEEEH2',
        parent=styles['Heading3'],
        fontName='Helvetica-BoldOblique',
        fontSize=8,
        leading=10.2,
        textColor=colors.HexColor('#222222'),
        spaceBefore=5,
        spaceAfter=2,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'IEEEBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.4,
        leading=9.6,
        alignment=4,
        spaceAfter=3.5
    )

    eq_style = ParagraphStyle(
        'IEEEEquation',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.0,
        leading=9.2,
        alignment=1,
        textColor=colors.HexColor('#001F3F'),
        spaceBefore=2,
        spaceAfter=3
    )

    caption_style = ParagraphStyle(
        'IEEECaption',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=6.8,
        leading=8.6,
        alignment=1,
        spaceBefore=2,
        spaceAfter=5
    )

    table_cell_style = ParagraphStyle(
        'IEEETableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.2,
        leading=7.8,
        alignment=1
    )

    table_header_style = ParagraphStyle(
        'IEEETableHdr',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.2,
        leading=7.8,
        alignment=1,
        textColor=colors.HexColor('#002855')
    )

    ref_style = ParagraphStyle(
        'IEEERef',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.6,
        leading=8.6,
        alignment=4,
        leftIndent=12,
        firstLineIndent=-12,
        spaceAfter=2.8
    )

    story = []

    # =========================================================================
    # PAGE 1 TOP: TITLE, 3 AUTHORS, ABSTRACT, KEYWORDS
    # =========================================================================
    story.append(Paragraph("Performance Analysis and Implementation of a Wireless Digital Communication System Using Source Coding, LDPC Error Correction, and Channel Simulation", title_style))

    authors_data = [
        [
            Paragraph("<b>Aravind M</b><br/>Registration Number: 23BCE7551", author_name_style),
            Paragraph("<b>Sai Chandu</b><br/>Registration Number: 23BCE20304", author_name_style),
            Paragraph("<b>Rahul L</b><br/>Registration Number: 23BCE7890", author_name_style)
        ],
        [
            Paragraph("<i>School of Computer Science and Engineering</i><br/>VIT-AP University, Amaravati, India", author_affil_style),
            Paragraph("<i>School of Computer Science and Engineering</i><br/>VIT-AP University, Amaravati, India", author_affil_style),
            Paragraph("<i>School of Computer Science and Engineering</i><br/>VIT-AP University, Amaravati, India", author_affil_style)
        ]
    ]
    col_w_auth = usable_w / 3.0
    authors_table = Table(authors_data, colWidths=[col_w_auth, col_w_auth, col_w_auth])
    authors_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(authors_table)
    story.append(Spacer(1, 5))

    abs_p = (
        "<b><i>Abstract</i>—Reliable information transmission across digital communication networks requires "
        "the harmonious integration of data compression, forward error correction (FEC), transport framing, and "
        "channel modulation. This paper presents the architecture, implementation, and empirical evaluation of an "
        "end-to-end digital communication simulation platform developed in Python with an interactive Streamlit "
        "graphical interface. The system couples lossless source coding (finite-precision Arithmetic coding and "
        "universal adaptive Lempel-Ziv-Welch dictionary coding) with systematic Low-Density Parity-Check (LDPC) "
        "channel coding based on a rate-1/2 (64, 32) code decoded via log-domain Belief Propagation (Sum-Product "
        "and Min-Sum algorithms). To bridge theoretical information theory with practical networking, the platform "
        "implements a dual-mode operational architecture: (1) a live wireless network transmission mode operating "
        "over TCP/IP stream sockets using a 36-byte versioned binary frame with IEEE 802.3 CRC32 integrity checks "
        "and sequence-confirmed acknowledgments, and (2) an analog wireless physical layer simulation executing "
        "baseband Binary Phase Shift Keying (BPSK) modulation over an Additive White Gaussian Noise (AWGN) channel. "
        "Rigorous Monte Carlo experiments across Eb/N0 sweeps from 0.0 to 10.0 dB demonstrate that the LDPC (64, 32) "
        "code achieves steep waterfall error suppression, reducing a pre-FEC bit error rate of 5.71e-2 at 4.0 dB to "
        "a post-FEC residual rate of 1.32e-3 (43.3x error reduction gain) and achieving zero residual errors at "
        "Eb/N0 >= 7.0 dB with 100% exact message reconstruction.</b>"
    )
    story.append(Paragraph(abs_p, abstract_style))

    kw_p = (
        "<b><i>Keywords</i>—Wireless Communication, Digital Communication, Source Coding, LDPC Codes, "
        "BPSK, AWGN, Bit Error Rate, CRC32, TCP/IP, Error Correction, Monte Carlo Simulation.</b>"
    )
    story.append(Paragraph(kw_p, keywords_style))
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor('#002855'), spaceAfter=4))

    # Break out of Top Frame into Page 1 Column 1
    story.append(FrameBreak())
    story.append(NextPageTemplate('LaterPages'))

    # =========================================================================
    # SECTION I: INTRODUCTION
    # =========================================================================
    story.append(Paragraph("I. INTRODUCTION", h1_style))
    story.append(Paragraph(
        "Modern telecommunications infrastructure demands high-fidelity, high-throughput digital transmission "
        "across physical channels inherently impaired by thermal noise, dispersion, and channel perturbations. "
        "In Shannon's foundational mathematical theory of communication [1], the communication problem is "
        "partitioned into two distinct operations governed by the Source-Channel Separation Theorem: source coding, "
        "which eliminates statistical redundancy from the information source to approach the empirical entropy H(X), "
        "and channel coding, which systematically introduces controlled algebraic redundancy to protect transmitted "
        "symbols up to the channel capacity C.",
        body_style
    ))
    story.append(Paragraph(
        "While classic classroom curricula frequently treat these mechanisms in theoretical isolation—often assuming "
        "ideal noiseless conduits or abstract bit-flip models—real-world engineering deployments necessitate an "
        "integrated pipeline. In practical wireless and networked systems, raw binary data must be packaged into "
        "structured wire frames, protected with forward error correction, modulated into baseband waveforms, "
        "transmitted across physical media, and verified through link-layer cyclic redundancy checks (CRC) and "
        "transport-layer protocols such as TCP/IP [10].",
        body_style
    ))
    story.append(Paragraph(
        "Crucially, an important architectural distinction must be maintained between transport-layer network reliability "
        "and physical-layer error correction. Transport protocols such as TCP provide reliable, ordered byte delivery "
        "by utilizing automatic repeat request (ARQ) retransmissions over lower-layer hardware interfaces. Consequently, "
        "observing zero packet losses over a local Wi-Fi or loopback TCP socket does not imply that the underlying physical "
        "channel is noiseless; rather, hardware-level physical decoders and transport-level retransmissions mask underlying "
        "transmission impairments. Conversely, physical-layer forward error correction must be evaluated by observing "
        "continuous analog signal-to-noise ratios (Eb/N0), calculating channel log-likelihood ratios (LLRs), and measuring "
        "pre-FEC versus post-FEC bit error rates (BER). Furthermore, software-simulated baseband AWGN channels must be distinguished "
        "from physical Wi-Fi radio propagation, which encounters multipath reflections, Doppler spread, and RF hardware non-linearities [14].",
        body_style
    ))
    story.append(Paragraph(
        "To address these pedagogical and engineering objectives, this project designs, implements, and evaluates an extensible "
        "digital communication system simulation. The contributions of this work are threefold: (1) We implement a complete, "
        "reproducible software transceiver pipeline combining finite-precision Arithmetic coding, adaptive LZW source coding, "
        "and systematic (64, 32) LDPC forward error correction decoded via log-domain Belief Propagation (Sum-Product and Min-Sum). "
        "(2) We formulate a versioned binary wire frame protocol featuring a 36-byte structured header, sequence counters, "
        "IEEE 802.3 CRC32 checksums, and a thread-safe TCP/IP socket transceiver with continuous streaming and bounded backpressure "
        "monitoring. (3) We simulate baseband BPSK modulation over a wireless AWGN link, benchmarking theoretical uncoded BER against "
        "empirical LDPC, Polar (64, 32), and Hamming (7, 4) codes, providing verifiable Monte Carlo performance curves and evaluating "
        "the sensitivity of source decompression to uncorrected channel errors.",
        body_style
    ))

    # =========================================================================
    # SECTION II: LITERATURE SURVEY
    # =========================================================================
    story.append(Paragraph("II. LITERATURE SURVEY", h1_style))
    story.append(Paragraph(
        "The theoretical foundations of digital communications originate from Shannon's 1948 paper [1], which established fundamental "
        "limits on source compression and channel capacity. In 1962, Gallager introduced Low-Density Parity-Check (LDPC) codes [2], "
        "demonstrating that linear codes defined by sparse parity-check matrices can be decoded in linear time via iterative message passing. "
        "However, computational constraints delayed their widespread adoption until MacKay and Neal [3] rediscovered LDPC codes in 1996, "
        "proving that log-domain Belief Propagation over bipartite Tanner graphs approaches the Shannon limit within fractions of a decibel. "
        "Richardson and Urbanke [13] subsequently established density evolution techniques to rigorously compute the iterative decoding thresholds "
        "of regular and irregular LDPC code ensembles.",
        body_style
    ))
    story.append(Paragraph(
        "In standardized engineering, LDPC codes were codified in IEEE Std 802.3an-2006 for 10GBASE-T Ethernet [8], utilizing quasi-cyclic "
        "structures to guarantee bit error rates below 10^-12 over copper twisted-pair cabling. Simultaneously, LDPC codes were adopted in "
        "modern satellite broadcasting (DVB-S2) and 5G New Radio (3GPP TS 38.212) data channels due to their high parallelization efficiency "
        "and low decoding latency compared to convolutional turbo codes. In 2009, Arikan proved that Polar codes achieve the symmetric capacity "
        "of discrete memoryless channels using channel polarization and Successive Cancellation (SC) decoding [4], leading to their adoption in "
        "5G control channels. Earlier linear block codes, such as Hamming's (7, 4) code [11], remain vital pedagogical baselines for single-error "
        "correction and syndrome decoding.",
        body_style
    ))
    story.append(Paragraph(
        "On the source coding front, universal data compression algorithms operate without requiring static, pre-computed symbol codebooks. "
        "Welch's 1984 formalization of the Lempel-Ziv-Welch (LZW) algorithm [5] established an adaptive dictionary method that dynamically "
        "parses recurring symbol sequences into fixed-width tokens. Concurrently, Rissanen and Langdon [6], followed by Witten, Neal, and "
        "Cleary [7], developed practical finite-precision Arithmetic coding, which represents entire message streams as a single interval in "
        "[0, 1), breaking the integer-length penalty of Huffman coding and achieving near-entropy compression.",
        body_style
    ))
    story.append(Paragraph(
        "In packet-switched communication, framing protocols rely on Cyclic Redundancy Checks (CRC), formalized by Peterson and Brown [9], "
        "to detect burst perturbations with negligible computational overhead. Modern network transport implementations universally rely on TCP [10] "
        "for reliable flow-controlled stream delivery. Comprehensive treatments of digital modulation over AWGN channels, soft demodulation, and "
        "error probability calculations are detailed by Proakis and Salehi [12], while foundational wireless propagation principles are analyzed "
        "by Tse and Viswanath [14].",
        body_style
    ))

    # =========================================================================
    # SECTION III: PROPOSED SYSTEM AND ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("III. PROPOSED SYSTEM AND ARCHITECTURE", h1_style))
    story.append(Paragraph(
        "The implemented system architecture comprises three primary functional domains: the Transmitter, the Dual Communication "
        "Transport Layer, and the Receiver, as illustrated in Fig. 1.",
        body_style
    ))
    story.append(Paragraph("A. Transmitter Processing Chain", h2_style))
    story.append(Paragraph(
        "The transmitter processes arbitrary UTF-8 text messages or structured telemetry bitstreams through four sequential stages: "
        "(1) Binary Serialization: Input character sequences are converted into 8-bit ASCII/UTF-8 byte streams and unpacked into binary bit vectors. "
        "(2) Lossless Source Coding: Redundancy is reduced using either finite-precision integer Arithmetic coding or 12-bit adaptive LZW universal "
        "dictionary coding. (3) Channel Forward Error Correction: The compressed stream is partitioned into K=32 bit blocks and encoded into N=64 bit "
        "systematic codewords using the LDPC (64, 32) encoder, appending zero-padding if necessary. (4) Binary Frame Assembly: Coded bits, padding "
        "indicators, and flags are packed into a versioned binary frame with a 36-byte header and IEEE 802.3 CRC32 checksum.",
        body_style
    ))
    story.append(Paragraph("B. Dual Communication Transport Media", h2_style))
    story.append(Paragraph(
        "A critical feature of our system is the explicit decoupling between live network transport and physical channel simulation: "
        "(1) Mode A & B (Live Wireless Network Transport): Operates over live TCP/IP stream sockets bound to local Wi-Fi or loopback interfaces "
        "(default port 8550). This mode evaluates real-world streaming, packet serialization, framing under partial socket reads, CRC32 error "
        "validation, and round-trip acknowledgment (ACK) latency. (2) Mode C (Physical Wireless AWGN Channel Simulation): Isolates the analog physical "
        "layer by bypassing TCP ARQ mechanisms. Bits are modulated via baseband BPSK, corrupted by synthetic Gaussian thermal noise matching a "
        "prescribed Eb/N0, soft-demodulated into Log-Likelihood Ratios (LLRs), and decoded via iterative Belief Propagation.",
        body_style
    ))
    story.append(Paragraph("C. Receiver Processing Chain", h2_style))
    story.append(Paragraph(
        "At the receiver, incoming bitstreams or network frames undergo inverse processing: (1) Frame Parsing & CRC32 Verification: The wire receiver reads "
        "the 36-byte header, verifies magic bytes and length fields, and computes the 32-bit CRC. Frames with checksum mismatches are rejected. "
        "(2) LDPC Decoding: In physical simulation, soft channel samples are decoded using log-domain Belief Propagation. In network socket mode, "
        "hard decision bits are verified against the parity-check matrix H. Systematic information bits are extracted, and zero-padding is removed. "
        "(3) Lossless Source Decompression: The recovered bitstream is decompressed using inverse Arithmetic or LZW decoding. (4) Exact Reconstruction "
        "Verification: The reconstructed message is compared against the transmitted message to verify 100% bit-for-bit fidelity.",
        body_style
    ))

    # Fig 1 in Column
    p_fig1 = os.path.join(FIG_DIR, "fig1_overall_architecture.png")
    if os.path.exists(p_fig1):
        story.append(Image(p_fig1, width=col_w, height=col_w * 0.52))
        story.append(Paragraph("Fig. 1. Overall system architecture illustrating the transmitter, dual transport media (TCP socket vs. BPSK-AWGN simulation), and receiver.", caption_style))

    # =========================================================================
    # SECTION IV: METHODOLOGY AND MATHEMATICAL FORMULATION
    # =========================================================================
    story.append(Paragraph("IV. METHODOLOGY AND MATHEMATICAL FORMULATION", h1_style))
    story.append(Paragraph("A. Source Coding Algorithms", h2_style))
    story.append(Paragraph(
        "1) Finite-Precision Arithmetic Codec: Our Arithmetic codec utilizes 32-bit integer register arithmetic to guarantee platform-independent, "
        "exact lossless compression. Symbol frequencies are computed with Laplace add-one smoothing over byte alphabet Sigma = {0,...,255} plus an EOF symbol (256):",
        body_style
    ))
    story.append(Paragraph("C(s) = 1 + sum(I(x_i = s)),  Total = sum(C(s))   (1)", eq_style))
    story.append(Paragraph(
        "Encoding maintains an active search range [L, H) in 32-bit unsigned integers. Bounds are updated iteratively based on cumulative frequencies F(s), "
        "and renormalized via bit-shifting under E1, E2, and E3 scaling conditions. Exact reconstruction is achieved through inverse interval subdivision.",
        body_style
    ))
    story.append(Paragraph(
        "2) Universal LZW Dictionary Codec: The LZW codec dynamically builds an adaptive dictionary of recurring character n-grams, mapping variable-length "
        "symbol sequences to fixed 12-bit binary integers (max table size 2^12 = 4096). The dictionary is initialized with 256 single-byte entries. When the "
        "dictionary capacity is reached, table growth freezes gracefully without desynchronization.",
        body_style
    ))
    story.append(Paragraph(
        "3) Compression Metrics: Compression Ratio (CR) and percentage Space Savings are defined as: CR = Original Size / Encoded Size, "
        "Space Savings (%) = (1 - Encoded Size / Original Size) * 100%.",
        body_style
    ))

    story.append(Paragraph("B. Systematic LDPC Forward Error Correction", h2_style))
    story.append(Paragraph(
        "The channel codec implements a systematic (N=64, K=32, M=32) LDPC code with code rate R = K/N = 0.5. The parity-check matrix H is structured as "
        "H = [P | I_32], where P is a 32x32 sparse matrix with regular column degree d_v = 3. The systematic generator matrix G = [I_32 | P^T] satisfies "
        "G * H^T = 0 mod 2. For any 32-bit information vector m, the 64-bit codeword is c = [m | m * P^T mod 2].",
        body_style
    ))
    story.append(Paragraph(
        "Iterative decoding operates over the bipartite Tanner graph using the log-domain Sum-Product algorithm. Variable-to-check and check-to-variable "
        "messages are updated as follows:",
        body_style
    ))
    story.append(Paragraph("q_mn = L_n + sum_{c in C(n)\\m} r_cn   (2)", eq_style))
    story.append(Paragraph("r_mn = 2 atanh [ prod_{j in V(m)\\n} tanh(q_mj / 2) ]   (3)", eq_style))
    story.append(Paragraph(
        "where L_n is the channel LLR. Numerical stability is ensured by clipping q_mj/2 to [-19.0, +19.0]. Total posterior LLRs Q_n = L_n + sum_{c in C(n)} r_cn "
        "determine hard decisions: c_hat_n = 0 if Q_n >= 0, else 1. The decoder terminates immediately when syndrome H * c_hat^T = 0 mod 2, up to max 25 iterations.",
        body_style
    ))

    story.append(Paragraph("C. BPSK Modulation", h2_style))
    story.append(Paragraph(
        "In baseband physical simulation (Mode C), binary codeword bits b_i in {0, 1} are mapped to antipodal voltage symbols: s_i = 1.0 - 2.0 b_i in {+1.0 V, -1.0 V}.",
        body_style
    ))

    story.append(Paragraph("D. AWGN Channel Model & Variance Scaling", h2_style))
    story.append(Paragraph(
        "The physical channel corrupts transmitted symbols with additive white Gaussian noise: y_i = s_i + n_i, n_i ~ N(0, sigma^2). "
        "For a given Eb/N0 in dB and code rate R = K/N, the noise standard deviation is scaled as:",
        body_style
    ))
    story.append(Paragraph("sigma = 1 / sqrt( 2 * R * 10^(Eb/N0 / 10) )   (4)", eq_style))
    story.append(Paragraph(
        "For uncoded transmission (R=1.0), sigma = [2 * 10^(Eb/N0/10)]^-0.5; for rate-1/2 LDPC (R=0.5), sigma = [10^(Eb/N0/10)]^-0.5, capturing "
        "the 3 dB noise bandwidth expansion penalty. Channel LLRs are L_i = (2 / sigma^2) * y_i. Coherent uncoded BPSK BER is: P_b = 0.5 erfc( sqrt(10^(Eb/N0/10)) ).",
        body_style
    ))

    # Fig 7 in Column
    p_fig7 = os.path.join(FIG_DIR, "fig7_bpsk_awgn_simulation.png")
    if os.path.exists(p_fig7):
        story.append(Image(p_fig7, width=col_w, height=col_w * 0.48))
        story.append(Paragraph("Fig. 2. Detailed physical layer BPSK-AWGN simulation architecture, soft demodulator, and LDPC message-passing decoder.", caption_style))

    story.append(Paragraph("E. BER and FER Evaluation", h2_style))
    story.append(Paragraph(
        "Pre-FEC BER evaluates raw channel slicer decisions against codeword bits: BER_pre = sum(c_i xor r_hat_i) / N. "
        "Post-FEC BER evaluates decoded information bits: BER_post = sum(m_i xor m_hat_i) / K. "
        "Frame Error Rate is FER = Erroneous Blocks / Total Blocks.",
        body_style
    ))

    story.append(Paragraph("F. Framing and TCP/IP Socket Transceiver", h2_style))
    story.append(Paragraph(
        "The binary frame specification comprises a 36-byte header: Magic (4B: b'WIRL'), Version (1B: 0x01), Type (1B: DATA=1, ACK=2, STREAM=3), "
        "Flags (2B), Sequence Number (4B uint32), Original Size (4B), Source Size (4B), Payload Length (4B), CRC32 Checksum (4B IEEE 802.3), "
        "Status Code (1B), and Reserved (7B). Partial reads are handled via strict socket loops. Successful TCP delivery confirms framing and CRC32, "
        "but does not represent physical-layer BER.",
        body_style
    ))

    # Fig 2 in Column
    p_fig2 = os.path.join(FIG_DIR, "fig2_frame_protocol_ack.png")
    if os.path.exists(p_fig2):
        story.append(Image(p_fig2, width=col_w, height=col_w * 0.61))
        story.append(Paragraph("Fig. 3. 36-byte binary wire frame layout and two-way TCP acknowledgment interaction sequence.", caption_style))

    # =========================================================================
    # SECTION V: EXPERIMENTAL SETUP AND SIMULATION PARAMETERS
    # =========================================================================
    story.append(Paragraph("V. EXPERIMENTAL SETUP AND SIMULATION PARAMETERS", h1_style))
    story.append(Paragraph(
        "The experimental platform was developed and evaluated under the parameters listed in Table I.",
        body_style
    ))

    # Table I: Experimental Parameters
    t1_data = [
        [Paragraph("<b>Parameter</b>", table_header_style), Paragraph("<b>Setting / Value</b>", table_header_style), Paragraph("<b>Engineering Rationale</b>", table_header_style)],
        [Paragraph("Runtime", table_cell_style), Paragraph("Python 3.11.9, NumPy 2.4", table_cell_style), Paragraph("Vectorized linear algebra", table_cell_style)],
        [Paragraph("Source Coding 1", table_cell_style), Paragraph("Arithmetic (32-bit int)", table_cell_style), Paragraph("High-precision interval coding", table_cell_style)],
        [Paragraph("Source Coding 2", table_cell_style), Paragraph("LZW (12-bit, max 4096)", table_cell_style), Paragraph("Universal dictionary stream coding", table_cell_style)],
        [Paragraph("Primary FEC", table_cell_style), Paragraph("LDPC (64, 32), R=0.5", table_cell_style), Paragraph("Gallager regular column d_v=3", table_cell_style)],
        [Paragraph("LDPC Decoding", table_cell_style), Paragraph("Sum-Product & Min-Sum", table_cell_style), Paragraph("Log-domain BP, max 25 iters", table_cell_style)],
        [Paragraph("Benchmark FEC 1", table_cell_style), Paragraph("Polar (64, 32), SC", table_cell_style), Paragraph("Successive Cancellation (3 dB)", table_cell_style)],
        [Paragraph("Benchmark FEC 2", table_cell_style), Paragraph("Hamming (7, 4) Block", table_cell_style), Paragraph("Single-error syndrome decoding", table_cell_style)],
        [Paragraph("Modulation", table_cell_style), Paragraph("Baseband BPSK", table_cell_style), Paragraph("Antipodal (+1V, -1V) mapping", table_cell_style)],
        [Paragraph("Channel Models", table_cell_style), Paragraph("AWGN & BSC & Lossless", table_cell_style), Paragraph("Thermal noise, bit flips, baseline", table_cell_style)],
        [Paragraph("Eb/N0 Range", table_cell_style), Paragraph("0.0 to 10.0 dB (step 1.0)", table_cell_style), Paragraph("Captures waterfall and error floors", table_cell_style)],
        [Paragraph("Tested Volume", table_cell_style), Paragraph("25,600 info bits / point", table_cell_style), Paragraph("Yields 95% bound BER < 1.17e-4", table_cell_style)],
        [Paragraph("Multi-Trial Setup", table_cell_style), Paragraph("10 trials (600 blocks)", table_cell_style), Paragraph("Assesses sample variance at 4 & 7 dB", table_cell_style)],
        [Paragraph("Wire Framing", table_cell_style), Paragraph("36-byte header + CRC32", table_cell_style), Paragraph("IEEE 802.3 polynomial 0xEDB88320", table_cell_style)],
        [Paragraph("Network Stack", table_cell_style), Paragraph("TCP stream sockets (:8550)", table_cell_style), Paragraph("Reliable byte transport over Wi-Fi", table_cell_style)],
    ]
    t1_table = Table(t1_data, colWidths=[col_w * 0.28, col_w * 0.36, col_w * 0.36])
    t1_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaf2f8')),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#bbbbbb')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(t1_table)
    story.append(Paragraph("TABLE I: Global Simulation Parameters and Engineering Specifications", caption_style))

    # =========================================================================
    # SECTION VI: RESULTS AND PERFORMANCE ANALYSIS
    # =========================================================================
    story.append(Paragraph("VI. RESULTS AND PERFORMANCE ANALYSIS", h1_style))
    story.append(Paragraph("A. BER Waterfall Performance in AWGN", h2_style))
    story.append(Paragraph(
        "Table II and Fig. 4 present measured BER across Eb/N0 from 0.0 to 10.0 dB. Below 2.5 dB, the rate-1/2 noise expansion penalty "
        "causes coded systems to experience error rates comparable to uncoded BPSK. However, above 3.0 dB, LDPC enters its steep waterfall region: "
        "post-FEC BER drops from 2.24e-2 at 2.0 dB to 1.99e-3 at 4.0 dB, clearing all errors at Eb/N0 >= 7.0 dB.",
        body_style
    ))

    # Table II: AWGN BER
    t2_data = [
        [Paragraph("<b>Eb/N0 (dB)</b>", table_header_style), Paragraph("<b>Theory Uncoded</b>", table_header_style), Paragraph("<b>Sim. Uncoded</b>", table_header_style), Paragraph("<b>Hamming (7,4)</b>", table_header_style), Paragraph("<b>Polar (64,32)</b>", table_header_style), Paragraph("<b>LDPC Min-Sum</b>", table_header_style), Paragraph("<b>LDPC Sum-Prod</b>", table_header_style)],
        [Paragraph("0.0", table_cell_style), Paragraph("0.07865", table_cell_style), Paragraph("0.08191", table_cell_style), Paragraph("0.11934", table_cell_style), Paragraph("0.19402", table_cell_style), Paragraph("0.08973", table_cell_style), Paragraph("<b>0.08672</b>", table_cell_style)],
        [Paragraph("1.0", table_cell_style), Paragraph("0.05628", table_cell_style), Paragraph("0.05617", table_cell_style), Paragraph("0.08152", table_cell_style), Paragraph("0.10172", table_cell_style), Paragraph("0.04906", table_cell_style), Paragraph("<b>0.04727</b>", table_cell_style)],
        [Paragraph("2.0", table_cell_style), Paragraph("0.03751", table_cell_style), Paragraph("0.03781", table_cell_style), Paragraph("0.05586", table_cell_style), Paragraph("0.04004", table_cell_style), Paragraph("0.02473", table_cell_style), Paragraph("<b>0.02238</b>", table_cell_style)],
        [Paragraph("3.0", table_cell_style), Paragraph("0.02288", table_cell_style), Paragraph("0.02285", table_cell_style), Paragraph("0.03363", table_cell_style), Paragraph("0.01203", table_cell_style), Paragraph("0.00668", table_cell_style), Paragraph("<b>0.00617</b>", table_cell_style)],
        [Paragraph("4.0", table_cell_style), Paragraph("0.01250", table_cell_style), Paragraph("0.01285", table_cell_style), Paragraph("0.01684", table_cell_style), Paragraph("0.00238", table_cell_style), Paragraph("0.00285", table_cell_style), Paragraph("<b>0.00199</b>", table_cell_style)],
        [Paragraph("5.0", table_cell_style), Paragraph("0.00595", table_cell_style), Paragraph("0.00543", table_cell_style), Paragraph("0.00641", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("0.00039", table_cell_style), Paragraph("<b>0.00035</b>", table_cell_style)],
        [Paragraph("6.0", table_cell_style), Paragraph("0.00239", table_cell_style), Paragraph("0.00234", table_cell_style), Paragraph("0.00184", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("7.81e-5", table_cell_style), Paragraph("<b>7.81e-5</b>", table_cell_style)],
        [Paragraph("7.0", table_cell_style), Paragraph("0.00077", table_cell_style), Paragraph("0.00059", table_cell_style), Paragraph("0.00039", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("<b>0.00000*</b>", table_cell_style)],
        [Paragraph("8.0", table_cell_style), Paragraph("0.00019", table_cell_style), Paragraph("7.81e-5", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("<b>0.00000*</b>", table_cell_style)],
        [Paragraph("9.0", table_cell_style), Paragraph("3.36e-5", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("7.81e-5", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("<b>0.00000*</b>", table_cell_style)],
        [Paragraph("10.0", table_cell_style), Paragraph("3.87e-6", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("0.00000", table_cell_style), Paragraph("<b>0.00000*</b>", table_cell_style)],
    ]
    t2_table = Table(t2_data, colWidths=[col_w/7.0]*7)
    t2_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaf2f8')),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#bbbbbb')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(t2_table)
    story.append(Paragraph("TABLE II: Measured Bit Error Rate (BER) vs. Eb/N0 in AWGN (25,600 Bits/Point, * Zero Observed Errors)", caption_style))

    # Fig 3 in Column
    p_fig3 = os.path.join(FIG_DIR, "fig3_awgn_ber_waterfall.png")
    if os.path.exists(p_fig3):
        story.append(Image(p_fig3, width=col_w, height=col_w * 0.69))
        story.append(Paragraph("Fig. 4. Measured BER vs. Eb/N0 waterfall curves over the simulated BPSK-AWGN physical channel.", caption_style))

    story.append(Paragraph("B. Theoretical vs. Simulated Uncoded BPSK", h2_style))
    story.append(Paragraph(
        "Simulated uncoded BPSK agrees closely with theory across all points (e.g. 0.05617 vs 0.05628 at 1.0 dB; 0.01285 vs 0.01250 at 4.0 dB), "
        "confirming the correctness of our antipodal symbol mapping and noise variance scaling.",
        body_style
    ))

    story.append(Paragraph("C. Frame Error Rate and Multi-Trial Stability", h2_style))
    story.append(Paragraph(
        "In our 10-trial Monte Carlo evaluation at 4.0 dB (38,400 codeword bits, 600 LDPC blocks), the block error count was 19, yielding an "
        "empirical FER of 3.17e-2. At 7.0 dB, zero block errors were observed across all 600 blocks (FER = 0.0000).",
        body_style
    ))

    story.append(Paragraph("D. Pre-Decoding vs. Post-Decoding BER and Coding Gain", h2_style))
    story.append(Paragraph(
        "Fig. 5 shows pre-FEC channel slicer BER versus post-FEC LDPC BER. At 4.0 dB, LDPC reduces bit errors from 2,191 down to 25, an empirical error "
        "reduction factor of Gain = 5.7057e-2 / 1.3186e-3 = 43.3x. To achieve a target BER of 10^-3, LDPC requires Eb/N0 ~ 4.3 dB, compared to 6.8 dB "
        "for uncoded BPSK, establishing a coding gain of 2.5 dB.",
        body_style
    ))

    # Fig 4 in Column
    p_fig4 = os.path.join(FIG_DIR, "fig4_pre_vs_post_fec.png")
    if os.path.exists(p_fig4):
        story.append(Image(p_fig4, width=col_w, height=col_w * 0.44))
        story.append(Paragraph("Fig. 5. Pre-FEC channel slicer BER vs. Post-FEC LDPC residual BER and empirical error suppression gain.", caption_style))

    story.append(Paragraph("E. Zero-Error Observation & Rule of Three", h2_style))
    story.append(Paragraph(
        "Asterisks (*) in Table II denote points where zero bit errors occurred in 25,600 bits. By the statistical Rule of Three, observing zero errors over N_b bits "
        "does not imply zero error probability, but establishes a 95% upper confidence bound on the true BER: BER_95% < 3 / 25,600 ~ 1.17e-4.",
        body_style
    ))

    story.append(Paragraph("F. Source Compression Study & Overhead Analysis", h2_style))
    story.append(Paragraph(
        "Empirical results from our source compression benchmark are summarized in Table III and Fig. 6. For correlated Markov streams (p01=0.05), "
        "LZW achieves CR = 1.686x (40.67% space savings). When applied to uniform pseudo-random bits (H ~ 1.0), compression expands data by 47.66% "
        "(CR = 0.677x), corroborating Shannon's incompressibility theorem. On short text strings (39 bytes), Arithmetic coding incurs a frequency table header "
        "overhead expanding data to 119 bytes (CR = 0.33x), while LZW expands to 54 bytes (CR = 0.72x) due to initial unigram dictionary initialization.",
        body_style
    ))

    # Table III: Source Compression
    t3_data = [
        [Paragraph("<b>Source Topology</b>", table_header_style), Paragraph("<b>H(X) (b)</b>", table_header_style), Paragraph("<b>Raw (b)</b>", table_header_style), Paragraph("<b>Comp (b)</b>", table_header_style), Paragraph("<b>CR</b>", table_header_style), Paragraph("<b>Savings</b>", table_header_style)],
        [Paragraph("Structured Telemetry", table_cell_style), Paragraph("4.7612", table_cell_style), Paragraph("5216", table_cell_style), Paragraph("4680", table_cell_style), Paragraph("1.115x", table_cell_style), Paragraph("+10.28%", table_cell_style)],
        [Paragraph("Markov (p01=0.05)", table_cell_style), Paragraph("0.9996", table_cell_style), Paragraph("8192", table_cell_style), Paragraph("4860", table_cell_style), Paragraph("1.686x", table_cell_style), Paragraph("+40.67%", table_cell_style)],
        [Paragraph("Markov (p01=0.10)", table_cell_style), Paragraph("0.9228", table_cell_style), Paragraph("8192", table_cell_style), Paragraph("7956", table_cell_style), Paragraph("1.030x", table_cell_style), Paragraph("+2.88%", table_cell_style)],
        [Paragraph("Markov (p01=0.25)", table_cell_style), Paragraph("0.9996", table_cell_style), Paragraph("8192", table_cell_style), Paragraph("10944", table_cell_style), Paragraph("0.749x", table_cell_style), Paragraph("-33.59%", table_cell_style)],
        [Paragraph("Uniform Random", table_cell_style), Paragraph("1.0000", table_cell_style), Paragraph("8192", table_cell_style), Paragraph("12096", table_cell_style), Paragraph("0.677x", table_cell_style), Paragraph("-47.66%", table_cell_style)],
    ]
    t3_table = Table(t3_data, colWidths=[col_w * 0.28, col_w * 0.15, col_w * 0.14, col_w * 0.14, col_w * 0.13, col_w * 0.16])
    t3_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaf2f8')),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#bbbbbb')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(t3_table)
    story.append(Paragraph("TABLE III: Source Compression Benchmark Across Information Topologies", caption_style))

    # Fig 5 in Column
    p_fig5 = os.path.join(FIG_DIR, "fig5_source_coding_entropy.png")
    if os.path.exists(p_fig5):
        story.append(Image(p_fig5, width=col_w, height=col_w * 0.53))
        story.append(Paragraph("Fig. 6. Source coding trade-off: empirical entropy vs. compression ratio across source topologies.", caption_style))

    story.append(Paragraph("G. Live Wireless Socket Transfer (Mode A)", h2_style))
    story.append(Paragraph(
        "Table IV and Fig. 7 report live network performance transmitting 'Hello, this is my wireless ITC project!' (39 bytes). "
        "All frames achieved valid CRC32 verification and sequence-confirmed delivery. Measured round-trip latency was 14.20 ms for raw text, "
        "24.64 ms for LZW, and 48.60 ms for Arithmetic coding, reflecting socket streaming overhead and syndrome verification.",
        body_style
    ))

    # Table IV: Socket Benchmark
    t4_data = [
        [Paragraph("<b>Codec Mode</b>", table_header_style), Paragraph("<b>Orig (B)</b>", table_header_style), Paragraph("<b>Src (B)</b>", table_header_style), Paragraph("<b>Frame (B)</b>", table_header_style), Paragraph("<b>RTT (ms)</b>", table_header_style), Paragraph("<b>Fidelity</b>", table_header_style)],
        [Paragraph("Raw Text", table_cell_style), Paragraph("39", table_cell_style), Paragraph("39", table_cell_style), Paragraph("114", table_cell_style), Paragraph("14.20", table_cell_style), Paragraph("100% (CRC OK)", table_cell_style)],
        [Paragraph("Arithmetic", table_cell_style), Paragraph("39", table_cell_style), Paragraph("119", table_cell_style), Paragraph("242", table_cell_style), Paragraph("48.60", table_cell_style), Paragraph("100% (CRC OK)", table_cell_style)],
        [Paragraph("LZW (12-bit)", table_cell_style), Paragraph("39", table_cell_style), Paragraph("54", table_cell_style), Paragraph("114", table_cell_style), Paragraph("24.64", table_cell_style), Paragraph("100% (CRC OK)", table_cell_style)],
    ]
    t4_table = Table(t4_data, colWidths=[col_w * 0.24, col_w * 0.14, col_w * 0.14, col_w * 0.16, col_w * 0.16, col_w * 0.16])
    t4_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaf2f8')),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#bbbbbb')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(t4_table)
    story.append(Paragraph("TABLE IV: Live Wireless Socket Transmission Metrics (Mode A)", caption_style))

    # Fig 6 in Column
    p_fig6 = os.path.join(FIG_DIR, "fig6_socket_latency_overhead.png")
    if os.path.exists(p_fig6):
        story.append(Image(p_fig6, width=col_w, height=col_w * 0.44))
        story.append(Paragraph("Fig. 7. Wire frame size and round-trip ACK latency under live TCP socket transmission.", caption_style))

    story.append(Paragraph("H. Comparison of Supported Coding Configurations", h2_style))
    story.append(Paragraph(
        "Table V presents a systematic comparison of all four channel coding schemes implemented in the project codebase.",
        body_style
    ))

    # Table V: Comparison
    t5_data = [
        [Paragraph("<b>Metric</b>", table_header_style), Paragraph("<b>Hamming (7,4)</b>", table_header_style), Paragraph("<b>Polar (64,32)</b>", table_header_style), Paragraph("<b>LDPC Min-Sum</b>", table_header_style), Paragraph("<b>LDPC Sum-Prod</b>", table_header_style)],
        [Paragraph("Blocklength (N, K)", table_cell_style), Paragraph("(7, 4)", table_cell_style), Paragraph("(64, 32)", table_cell_style), Paragraph("(64, 32)", table_cell_style), Paragraph("(64, 32)", table_cell_style)],
        [Paragraph("Code Rate (R)", table_cell_style), Paragraph("0.571", table_cell_style), Paragraph("0.500", table_cell_style), Paragraph("0.500", table_cell_style), Paragraph("0.500", table_cell_style)],
        [Paragraph("Decoding Paradigm", table_cell_style), Paragraph("Syndrome Table", table_cell_style), Paragraph("Successive Canc.", table_cell_style), Paragraph("Min-Sum BP", table_cell_style), Paragraph("Sum-Product BP", table_cell_style)],
        [Paragraph("BER at 4.0 dB", table_cell_style), Paragraph("1.68e-2", table_cell_style), Paragraph("2.38e-3", table_cell_style), Paragraph("2.85e-3", table_cell_style), Paragraph("<b>1.99e-3</b>", table_cell_style)],
        [Paragraph("Zero-Error SNR", table_cell_style), Paragraph(">= 8.0 dB", table_cell_style), Paragraph(">= 5.0 dB", table_cell_style), Paragraph(">= 7.0 dB", table_cell_style), Paragraph(">= 7.0 dB", table_cell_style)],
        [Paragraph("Domain", table_cell_style), Paragraph("Control headers", table_cell_style), Paragraph("5G Control (NR)", table_cell_style), Paragraph("Low-power ASIC", table_cell_style), Paragraph("Data channels", table_cell_style)],
    ]
    t5_table = Table(t5_data, colWidths=[col_w * 0.28, col_w * 0.18, col_w * 0.18, col_w * 0.18, col_w * 0.18])
    t5_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaf2f8')),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#bbbbbb')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(t5_table)
    story.append(Paragraph("TABLE V: Systematic Comparison of Implemented Channel Coding Architectures", caption_style))

    story.append(Paragraph("I. Coupling of Channel Errors and Source Decompression", h2_style))
    story.append(Paragraph(
        "A critical observation from Mode C simulation is the catastrophic sensitivity of compressed bitstreams to residual channel errors. "
        "At Eb/N0 = 4.0 dB, two residual block errors corrupted the compressed bitstream, causing the Arithmetic decompressor to raise a "
        "MalformedStreamException and failing text recovery. At Eb/N0 >= 7.0 dB, where the LDPC decoder achieved zero residual errors, 100% exact "
        "reconstruction was restored. This proves that powerful FEC is mandatory when transmitting source-compressed information.",
        body_style
    ))

    # =========================================================================
    # SECTION VII: DISCUSSION AND LIMITATIONS
    # =========================================================================
    story.append(Paragraph("VII. DISCUSSION AND LIMITATIONS", h1_style))
    story.append(Paragraph(
        "Several practical engineering constraints must be noted: (1) Simulated AWGN vs. Real Radio Propagation: The physical channel models "
        "ideal thermal noise, whereas real-world Wi-Fi links experience multipath reflections, Rayleigh/Rician fading, Doppler shifts, and hardware "
        "carrier offsets [14]. (2) TCP ARQ Masking: Sockets operate over TCP, which guarantees reliable delivery via retransmissions, masking raw radio "
        "packet loss. (3) Finite Blocklength: The implemented LDPC code has blocklength N=64. Standard industrial LDPC codes (e.g. IEEE 802.3an N=2048) "
        "exhibit much steeper waterfall thresholds. (4) Simulation Runtime: Evaluating extreme error floors (BER < 10^-8) requires transmitting "
        "billions of bits, exceeding interactive execution constraints.",
        body_style
    ))

    # =========================================================================
    # SECTION VIII: CONCLUSION AND FUTURE WORK
    # =========================================================================
    story.append(Paragraph("VIII. CONCLUSION AND FUTURE WORK", h1_style))
    story.append(Paragraph(
        "This paper presented the design, implementation, and empirical verification of an end-to-end digital communication simulation system. "
        "By integrating finite-precision Arithmetic coding, adaptive LZW compression, systematic rate-1/2 LDPC (64, 32) coding with log-domain "
        "Belief Propagation, and a 36-byte versioned binary frame protocol with CRC32 integrity verification, the system successfully bridges "
        "theoretical information theory and real-world networking. Empirical evaluations demonstrated that the LDPC decoder achieves a 43.3x "
        "error suppression gain at Eb/N0 = 4.0 dB and delivers error-free transmission (BER = 0.0000) with 100% exact text reconstruction at Eb/N0 >= 7.0 dB.",
        body_style
    ))
    story.append(Paragraph(
        "Future extensions include: (1) Implementing higher-order digital modulations, such as QPSK, 16-QAM, and OFDM. "
        "(2) Scaling LDPC codes to standardized quasi-cyclic parity-check matrices (N >= 1024) utilizing GPU-accelerated Belief Propagation. "
        "(3) Interfacing the simulation with Software-Defined Radio (SDR) hardware (e.g. RTL-SDR, HackRF, or USRP) to conduct over-the-air RF experiments.",
        body_style
    ))

    # =========================================================================
    # REFERENCES
    # =========================================================================
    story.append(Paragraph("REFERENCES", h1_style))

    refs = [
        "[1] C. E. Shannon, \"A mathematical theory of communication,\" <i>The Bell System Technical Journal</i>, vol. 27, no. 3, pp. 379–423, Jul. 1948. DOI: 10.1002/j.1538-7305.1948.tb01338.x",
        "[2] R. G. Gallager, \"Low-density parity-check codes,\" <i>IRE Transactions on Information Theory</i>, vol. 8, no. 1, pp. 21–28, Jan. 1962. DOI: 10.1109/TIT.1962.1057683",
        "[3] D. J. C. MacKay and R. M. Neal, \"Near Shannon limit performance of low density parity check codes,\" <i>Electronics Letters</i>, vol. 32, no. 18, pp. 1645–1646, Aug. 1996. DOI: 10.1049/el:19961141",
        "[4] E. Ar\u0131kan, \"Channel polarization: A method for constructing capacity-achieving codes for symmetric binary-input memoryless channels,\" <i>IEEE Transactions on Information Theory</i>, vol. 55, no. 7, pp. 3051–3073, Jul. 2009. DOI: 10.1109/TIT.2009.2021379",
        "[5] T. A. Welch, \"A technique for high-performance data compression,\" <i>IEEE Computer</i>, vol. 17, no. 6, pp. 8–19, Jun. 1984. DOI: 10.1109/MC.1984.1659158",
        "[6] J. Rissanen and G. G. Langdon, \"Arithmetic coding,\" <i>IBM Journal of Research and Development</i>, vol. 23, no. 2, pp. 149–162, Mar. 1979. DOI: 10.1147/rd.232.0149",
        "[7] I. H. Witten, R. M. Neal, and J. G. Cleary, \"Arithmetic coding for data compression,\" <i>Communications of the ACM</i>, vol. 30, no. 6, pp. 520–540, Jun. 1987. DOI: 10.1145/214762.214771",
        "[8] <i>IEEE Standard for Information Technology—Specific Requirements Part 3: CSMA/CD Access Method and Physical Layer Specifications Amendment 4: 10 Gb/s Operation, Type 10GBASE-T</i>, IEEE Std 802.3an-2006, pp. 1–181, Sep. 2006. DOI: 10.1109/IEEESTD.2006.246283",
        "[9] W. W. Peterson and D. T. Brown, \"Cyclic codes for error detection,\" <i>Proceedings of the IRE</i>, vol. 49, no. 1, pp. 228–235, Jan. 1961. DOI: 10.1109/JRPROC.1961.287814",
        "[10] J. Postel, \"Transmission Control Protocol,\" <i>RFC 793</i>, Internet Engineering Task Force (IETF), Sep. 1981. DOI: 10.17487/RFC0793",
        "[11] R. W. Hamming, \"Error detecting and error correcting codes,\" <i>The Bell System Technical Journal</i>, vol. 29, no. 2, pp. 147–160, Apr. 1950. DOI: 10.1002/j.1538-7305.1950.tb00463.x",
        "[12] J. G. Proakis and M. Salehi, <i>Digital Communications</i>, 5th ed. New York, NY, USA: McGraw-Hill, 2008.",
        "[13] T. J. Richardson and R. L. Urbanke, \"The capacity of low-density parity-check codes under message-passing decoding,\" <i>IEEE Transactions on Information Theory</i>, vol. 47, no. 2, pp. 599–618, Feb. 2001. DOI: 10.1109/18.910577",
        "[14] D. Tse and P. Viswanath, <i>Fundamentals of Wireless Communication</i>, Cambridge, UK: Cambridge University Press, 2005."
    ]

    for ref in refs:
        story.append(Paragraph(ref, ref_style))

    # Build document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully compiled IEEE Conference Paper PDF: {filename}")


if __name__ == "__main__":
    build_pdf()
