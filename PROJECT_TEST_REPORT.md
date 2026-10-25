# Comprehensive Project Test & Verification Report
## Information Theory & Channel Coding — Wired Communication System Simulation

* **Student Name:** Aravind
* **Registration Number:** 23BCE7551
* **Course Track:** Wired Network Digital Communication System (Terminal Digit `1`)
* **Institution:** School of Computer Science and Engineering, VIT-AP University
* **Project Directory:** `C:\Users\saamsung\OneDrive\Desktop\ITC project`
* **Audit Date:** October 25, 2026

---

## A. Environment and Execution Setup

* **Operating System:** Windows 11 Pro / PowerShell environment
* **Python Runtime:** Python 3.11.9 (`C:\Users\saamsung\Python311\python.exe`)
* **Test Runner:** `pytest` version 9.1.1 (pluggy 1.6.0)
* **Core Dependencies Verified:**
  * `numpy`: 2.4.6 (Matrix operations, linear algebra, LLR calculation, vector bit operations)
  * `matplotlib`: 3.11.2 (Publication-grade 300 DPI figure generation)
  * `reportlab`: 5.0.1 (Automated 6-page IEEE conference paper PDF generation)
  * `pytest`: 9.1.1 (Automated unit and integration test framework)
* **Standard Test Execution Command:**
  ```powershell
  python -m pytest tests/ -v
  ```
* **Simulation Demonstration Command:**
  ```powershell
  python main.py --demo
  ```
* **Monte Carlo Experiment & Figure Generation Command:**
  ```powershell
  python main.py --experiments
  ```
* **IEEE Conference Paper PDF Compiler:**
  ```powershell
  python paper/generate_paper_pdf.py
  ```

---

## B. Test Summary Baseline & Final Results

| Metric | Initial State (Baseline) | Post-Audit & Repair State |
| :--- | :--- | :--- |
| **Total Tests Discovered** | 20 | **43** |
| **Tests Passed** | 20 (100%) | **43 (100%)** |
| **Tests Failed** | 0 | **0** |
| **Tests Skipped** | 0 | **0** |
| **Execution Time** | 2.80 seconds | **1.09 seconds** |
| **Code Coverage Focus** | Basic sanity checks | Comprehensive edge cases, error positions, unsupported lengths, & full pipeline sweeps |

---

## C. Component-by-Component Evaluation

### 1. Source Coding (`src/source_coding/`)
* **Universal Dictionary Codec (`LZWCodec`):**
  * Evaluated across 10 distinct input topologies:
    1. *Empty input:* Verified zero-bit output and clean empty string/bytes return.
    2. *Single-character input:* Correctly encodes to a single 12-bit code; compression ratio = 0.667 (demonstrates dictionary overhead on short inputs).
    3. *Repeated-character input:* `A * 1000` compressed from 8000 bits to 456 bits; compression ratio = 17.54x, space savings = 94.3%.
    4. *Normal text:* Exact lossless recovery verified (`Original == Decoded`).
    5. *Long structured telemetry:* Compressed from 5216 raw bits to 4680 bits (CR = 1.115x).
    6. *All 256 unique byte values:* Verified exact byte-for-byte fidelity across full `bytes(range(256))`.
    7. *Repeated patterns (`ABABAB`...):* High compression gain (CR = 8.33x) with classic $cScSc$ edge case handled cleanly.
    8. *Uniform pseudo-random input ($H(X) \approx 1.0$):* Expands data size by 50% (CR = 0.67x), validating Shannon's Source Coding Theorem.
    9. *Dictionary table freeze:* Tested with `bit_depth=9` (table limit 512) and `bit_depth=12` (table limit 4096). Codec freezes gracefully without desynchronization, achieving 100% exact decompression.
* **Binary Serialization (`BinaryConverter`):**
  * Bit-packing and unpacking verified for UTF-8 strings and variable bit-depth integer arrays.

### 2. Channel Coding (`src/channel_coding/`)
* **Systematic Hamming(7,4) Codec (`HammingCodec`):**
  * Matrix dimensions: Generator $G \in \{0, 1\}^{4 \times 7}$, Parity-check $H \in \{0, 1\}^{3 \times 7}$.
  * Orthogonality: $(G \cdot H^T) \pmod 2 = 0_{4 \times 3}$ verified.
  * Information extraction: First 4 bits are systematic information bits.
  * Single-bit error correction: Evaluated all 16 possible 4-bit message words across all 7 error positions ($16 \times 7 = 112$ distinct error vectors). **112 / 112 single-bit error patterns corrected with 100% accuracy.**
  * Double-bit error behavior: Demonstrates error detection/miscorrection under $t > 1$ errors as expected for $d_{\min} = 3$.
  * Input length validation: `encode_block` rejects lengths $\neq 4$; `decode_block` rejects lengths $\neq 7$.
* **Low-Density Parity-Check Codec (`LDPCCodec`):**
  * Parameters: Standard systematic rate-1/2 block code $(n=64, k=32, m=32)$.
  * Matrix dimensions: $G \in \{0, 1\}^{32 \times 64}$, $H \in \{0, 1\}^{32 \times 64}$.
  * Binary orthogonality: $(G \cdot H^T) \pmod 2 = 0_{32 \times 32}$ confirmed.
  * Valid codewords: Generated codewords satisfy $(c \cdot H^T) \pmod 2 = 0$.
  * Iterative Log-Domain Belief Propagation (Sum-Product) & Min-Sum decoding:
    * Numerically stable `atanh` clipping prevents divide-by-zero.
    * Early syndrome stopping condition breaks loop as soon as $(H \cdot \hat{c}) \pmod 2 = 0$.
    * Corrects multi-bit error distributions within channel capacity.
* **Polar Codec (`PolarCodec`):**
  * Construction: Arikan recursive polarization kernel $F_2 = \begin{bmatrix} 1 & 0 \\ 1 & 1 \end{bmatrix}^{\otimes 6}$.
  * Channel reliability sorting: Bhattacharyya recursion correctly partitions into 32 information channels and 32 frozen channels.
  * Successive Cancellation (SC) decoder tree: Verifiably reconstructs systematic information bits with 0 errors under noiseless and high-SNR conditions.
* **Base Interface (`ChannelCodec`):**
  * Arbitrary stream segmentation and zero-padding handling verified.
  * Rejects stream lengths not multiple of $n$, preventing silent bit truncation.

### 3. Channel Models (`src/channel_model/`)
* **Ideal Lossless Channel Baseline:**
  * Transmits bitstreams with strictly zero bit errors ($\text{BER} = 0$, Pre-FEC = 0, Post-FEC = 0).
  * Generates high-confidence LLRs ($\pm 50.0$) for soft belief-propagation decoders.
* **Binary Symmetric Channel (BSC):**
  * Evaluated across transition probabilities $p \in \{0.0, 0.001, 0.01, 0.05, 0.10\}$ across multiple random seeds (`101`, `123`, `202`, `456`, `789`).
  * Measured error flip rate matches target binomial probability within $3.5$ standard errors ($z < 2.04$).
* **Electrical AWGN Physical Wired Link:**
  * BPSK baseband modulation: $0 \to +1.0\text{ V}, 1 \to -1.0\text{ V}$.
  * Noise variance calculation $\sigma^2 = \frac{1}{2 R \cdot 10^{(E_b/N_0)/10}}$ rigorously accounts for code rate $R$. Rate-1/2 coded transmission exhibits $\sigma_{\text{coded}} = \sqrt{2} \cdot \sigma_{\text{uncoded}}$ as required by communication theory.
  * Simulated uncoded BPSK BER empirically verified against exact theoretical Q-function formula $P_b = \frac{1}{2}\text{erfc}\left(\sqrt{E_b/N_0}\right)$ across 0 to 10 dB ($z < 1.10$).

### 4. Metrics & Evaluation (`src/metrics/evaluator.py`)
* Bit Error Rate (BER), Frame Error Rate (FER), and redundancy overhead metrics verified.
* Rule of Three confidence bounds ($3/N$ upper bound for zero observed errors) correctly evaluated.

### 5. End-to-End Pipeline (`src/simulation/pipeline.py`)
* Verified complete path:
  $$\text{Source} \to \text{Binary UTF-8} \to \text{LZW Codec} \to \text{FEC Encode} \to \text{Wired Channel} \to \text{FEC Decode} \to \text{LZW Decompress} \to \text{Verification}$$
* Tested across Custom Text, Structured Telemetry, and Random Binary vectors over Lossless, BSC, and AWGN channels.
* Correctly distinguishes Pre-FEC BER (slicer vs transmitted coded bits) from Post-FEC BER (original vs decoded information bits).

### 6. Experimental Results & Visualizations (`src/simulation/experiment_runner.py`)
* Full Monte Carlo suite executed across:
  * 11 AWGN SNR points ($0.0$ to $10.0$ dB) with 25,600 bits per point ($281,600$ total coded bits).
  * 11 BSC bit-flip probabilities ($0.0005$ to $0.15$) with 25,600 bits per point.
  * 5 saturated source topologies (telemetry, correlated Markov, random).
* All CSV datasets and 5 high-resolution (300 DPI) publication-grade plots generated and verified.

### 7. Web Application & Public Deployment Status
* **Local Web Application:** No Streamlit (`app.py`), Flask, or FastAPI web frontend exists in this repository. Dependencies in `requirements.txt` specify only scientific Python packages (`numpy`, `matplotlib`, `reportlab`, `pytest`).
* **Public Web Deployment:** No public deployment URL is configured or active for this codebase.

---

## D. Defects Identified, Root Causes, and Applied Fixes

### Defect 1: False Negative Exact Recovery for Binary Payloads in Pipeline
* **Severity:** High
* **Affected File & Function:** `src/metrics/evaluator.py` (`PerformanceEvaluator.calculate_ber`) and `src/simulation/pipeline.py` (`CommunicationPipeline.run_single_transmission`).
* **Root Cause:** In `calculate_ber`, the dictionary output only included `'zero_error_observed'`, but lacked the key `'exact_match'`. When binary data (non-string) was transmitted through the pipeline, `pipeline.py` queried `end_to_end_eval.get('exact_match', False)`. Because `'exact_match'` was missing, the pipeline reported `exact_recovery: False` even when zero bit errors occurred and recovery was 100% exact.
* **Fix Applied:** Updated `PerformanceEvaluator.calculate_ber` to explicitly compute and return `'exact_match': (len(tx) == len(rx)) and (num_errors == 0)` and `'length_mismatch': (len(tx) != len(rx))`.
* **Regression Test Added:** `tests/test_pipeline.py::test_pipeline_binary_array_lossless_exact_recovery` and `tests/test_pipeline.py::test_metrics_length_mismatch_detection`.

### Defect 2: Binary Bitstream Length Distortion under Source Coding
* **Severity:** Medium
* **Affected File & Function:** `src/simulation/pipeline.py` (`CommunicationPipeline.run_single_transmission`).
* **Root Cause:** When binary arrays with lengths not divisible by 8 (e.g. 75 bits) were passed to the pipeline with source coding enabled, `np.packbits` zero-padded the data to the next byte boundary. On reception, `np.unpackbits` unpacked all byte bits, producing extra trailing bits (e.g., 80 bits instead of 75 bits).
* **Fix Applied:** Modified `pipeline.py` to trim the unpacked binary array to the exact original input length: `reconstructed_raw_bits = np.unpackbits(...)[:len(raw_bits)]`.
* **Regression Test Added:** `tests/test_pipeline.py::test_pipeline_arbitrary_binary_length_roundtrip`.

### Defect 3: LDPC & Polar Decoder Failure on Lossless Binary Hard Bits
* **Severity:** High
* **Affected File & Function:** `src/channel_coding/ldpc_codec.py` (`LDPCCodec.decode_block`) and `src/channel_coding/polar_codec.py` (`PolarCodec.decode_block`).
* **Root Cause:** In both codecs, `decode_block` converted observations to LLRs for `"awgn"` and `"bsc"`, but for `channel_type="lossless"` (or default), it fell into `else: L_ch = y.copy()`. If binary hard bits $\{0, 1\}$ were passed directly, bit $0$ was assigned LLR $0.0$ (indeterminate), and bit $1$ was assigned LLR $+1.0$ (positive LLR, which signifies bit $0$ in standard BPSK/LLR conventions). As a result, hard-bit inputs completely failed to decode under noiseless/lossless conditions.
* **Fix Applied:** Added explicit handling for `channel_type in ("lossless", "ideal")` and hard binary $\{0, 1\}$ arrays: mapping bit $0 \to +50.0$ and bit $1 \to -50.0$.
* **Regression Test Added:** `tests/test_channel_coding.py::test_ldpc_lossless_hard_bits_recovery` and `tests/test_channel_coding.py::test_polar_lossless_hard_bits_recovery`.

### Defect 4: Missing Input Length Validation on Codec Stream Decoding
* **Severity:** Medium
* **Affected File & Function:** `src/channel_coding/base.py` (`ChannelCodec.decode`).
* **Root Cause:** In `ChannelCodec.decode`, `num_blocks` was computed via integer division `len(received) // self.n`. If `len(received) % self.n != 0`, trailing bits were silently discarded without raising an exception.
* **Fix Applied:** Added strict stream length validation:
  ```python
  if len(received) % self.n != 0:
      raise ValueError(f"Received stream length ({len(received)}) must be a multiple of codeword length n ({self.n}).")
  ```
* **Regression Test Added:** `tests/test_channel_coding.py::test_channel_codec_stream_decode_length_validation`.

### Defect 5: Unvalidated Padding Parameter in ChannelCodec.decode
* **Severity:** Low
* **Affected File & Function:** `src/channel_coding/base.py` (`ChannelCodec.decode`).
* **Root Cause:** Negative `pad_len` or `pad_len \ge k` was not guarded against, risking array slicing errors.
* **Fix Applied:** Added range validation ensuring $0 \le \text{pad\_len} < k$.
* **Regression Test Added:** `tests/test_channel_coding.py::test_channel_codec_stream_decode_length_validation`.

---

## E. Experimental Validation Data

### 1. AWGN Monte Carlo Sweep Results (25,600 bits/point)
Measured from real simulation run (`results/csv/awgn_ber_comparison.csv`):

| $E_b/N_0$ (dB) | Uncoded Theory BER | Uncoded Sim BER | Hamming(7,4) BER | Polar(64,32) BER | LDPC Sum-Product BER | LDPC Min-Sum BER |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.0** | $7.865 \times 10^{-2}$ | $8.191 \times 10^{-2}$ | $1.193 \times 10^{-1}$ | $1.940 \times 10^{-1}$ | $8.672 \times 10^{-2}$ | $8.973 \times 10^{-2}$ |
| **1.0** | $5.628 \times 10^{-2}$ | $5.617 \times 10^{-2}$ | $8.152 \times 10^{-2}$ | $1.017 \times 10^{-1}$ | $4.727 \times 10^{-2}$ | $4.906 \times 10^{-2}$ |
| **2.0** | $3.751 \times 10^{-2}$ | $3.781 \times 10^{-2}$ | $5.586 \times 10^{-2}$ | $4.004 \times 10^{-2}$ | $2.238 \times 10^{-2}$ | $2.473 \times 10^{-2}$ |
| **3.0** | $2.288 \times 10^{-2}$ | $2.285 \times 10^{-2}$ | $3.363 \times 10^{-2}$ | $1.203 \times 10^{-2}$ | $6.172 \times 10^{-3}$ | $6.680 \times 10^{-3}$ |
| **4.0** | $1.250 \times 10^{-2}$ | $1.285 \times 10^{-2}$ | $1.684 \times 10^{-2}$ | $2.383 \times 10^{-3}$ | $1.992 \times 10^{-3}$ | $2.852 \times 10^{-3}$ |
| **5.0** | $5.954 \times 10^{-3}$ | $5.430 \times 10^{-3}$ | $6.406 \times 10^{-3}$ | $< 1.17 \times 10^{-4*}$ | $3.516 \times 10^{-4}$ | $3.906 \times 10^{-4}$ |
| **6.0** | $2.388 \times 10^{-3}$ | $2.344 \times 10^{-3}$ | $1.836 \times 10^{-3}$ | $< 1.17 \times 10^{-4*}$ | $7.813 \times 10^{-5}$ | $7.813 \times 10^{-5}$ |
| **7.0** | $7.727 \times 10^{-4}$ | $5.859 \times 10^{-4}$ | $3.906 \times 10^{-4}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ |
| **8.0** | $1.909 \times 10^{-4}$ | $7.813 \times 10^{-5}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ |
| **9.0** | $3.363 \times 10^{-5}$ | $< 1.17 \times 10^{-4*}$ | $7.813 \times 10^{-5}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ |
| **10.0** | $3.872 \times 10^{-6}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ | $< 1.17 \times 10^{-4*}$ |

*\*Note on Zero Observed Errors:* 0 errors observed in 25,600 bits corresponds to a 95% confidence upper bound of $\text{BER}_{95\%} < 3 / 25,600 \approx 1.17 \times 10^{-4}$.

### 2. Saturated Source Compression Study Results
Measured from real simulation run (`results/csv/source_compression_study.csv`):

| Source Type | Empirical Entropy $H(X)$ (bits/symbol) | Raw Bits | Compressed Bits | Compression Ratio | Space Savings (%) | Lossless Exact Recovery |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Structured Telemetry** | 4.7612 | 5216 | 4680 | **1.115x** | +10.28% | **True (100%)** |
| **Markov ($p_{01}=0.05, p_{10}=0.05$)** | 0.9996 | 8192 | 4860 | **1.686x** | +40.67% | **True (100%)** |
| **Markov ($p_{01}=0.10, p_{10}=0.20$)** | 0.9228 | 8192 | 7956 | **1.030x** | +2.88% | **True (100%)** |
| **Markov ($p_{01}=0.25, p_{10}=0.25$)** | 0.9996 | 8192 | 10944 | **0.749x** | -33.59% | **True (100%)** |
| **Uniform Random ($H \approx 1.0$)** | 1.0000 | 8192 | 12096 | **0.677x** | -47.66% | **True (100%)** |

---

## F. Remaining Limitations

1. **Absence of Web GUI Application:**
   * No Streamlit or web UI script (`app.py`) exists in the repository. The project is structured strictly as a command-line simulation suite, automated test framework, and academic paper compilation pipeline.
   * If an interactive browser interface is required for classroom demonstration, a lightweight Streamlit dashboard can be added to wrap `CommunicationPipeline`.
2. **Short Block Length Effects ($N=64$):**
   * The LDPC and Polar implementations use $N=64, K=32$ for high-speed simulation in pure Python/NumPy without requiring native C/Cython extensions. While the waterfall behavior is verified, longer block lengths ($N \ge 1024$) would exhibit a steeper error-floor threshold.
3. **Statistical Resolution of Monte Carlo Sample Size:**
   * At 25,600 bits per point, BER values below $10^{-4}$ register 0 observed bit errors. To measure residual BER down to $10^{-7}$, $N \ge 10^8$ bits would be needed, which is computationally prohibitive in pure interpreted Python.

---

## G. Final Verdict

### **PASS FOR DEMONSTRATION**

**Justification:**
1. All core mathematical models, modern source coding (adaptive LZW), modern channel coding (systematic LDPC, Polar, Hamming), and channel models (Lossless, BSC, AWGN) execute without errors.
2. The complete test suite contains **43 automated unit and integration tests, all 43 passing (100%) in 1.09 seconds**.
3. All 5 confirmed defects have been diagnosed, repaired, and protected by dedicated regression tests.
4. The full Monte Carlo simulation suite was independently executed, regenerating all CSV measurement datasets and publication-grade plots.
5. The IEEE conference paper PDF was compiled cleanly via ReportLab and verified.
6. The verdict is not "Pass for Deployment" solely because a web application was not implemented in the repository. For all academic, demonstration, and research submission purposes, the project is completely reliable, robust, and verified.
