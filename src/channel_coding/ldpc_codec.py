"""
Low-Density Parity-Check (LDPC) Codec.
Implements Systematic Quasi-Cyclic / Gallager-style LDPC encoding and
Log-Likelihood Ratio (LLR) Belief Propagation / Min-Sum iterative decoding.
Standardized in IEEE 802.3an 10GBASE-T wired Ethernet physical layer.
"""

from typing import Tuple, Optional
import numpy as np
from .base import ChannelCodec


class LDPCCodec(ChannelCodec):
    """
    Systematic LDPC Codec with Log-Domain Belief Propagation (Sum-Product)
    and Min-Sum iterative decoding.
    """

    def __init__(
        self,
        n: int = 64,
        k: int = 32,
        max_iter: int = 25,
        algorithm: str = "sum_product",  # 'sum_product' or 'min_sum'
        min_sum_scale: float = 0.8,
        seed: Optional[int] = 42
    ):
        """
        Construct a systematic (n, k) LDPC code.
        Default: (64, 32) Rate-1/2 code.
        """
        super().__init__(n=n, k=k, name=f"LDPC({n},{k})-{algorithm}")
        self.m = n - k
        self.max_iter = max_iter
        self.algorithm = algorithm.lower()
        self.min_sum_scale = min_sum_scale
        self.seed = seed

        # Generate systematic parity check matrix H = [P | I_m]
        # and generator matrix G = [I_k | P^T]
        self.H, self.G, self.P = self._generate_systematic_ldpc_matrix(n, k, seed=seed)

        # Precompute graph connectivity for fast sparse belief propagation
        # check_nodes_for_var[n] = list of check node indices connected to variable node n
        # var_nodes_for_check[m] = list of variable node indices connected to check node m
        self.check_nodes_for_var = [np.where(self.H[:, j] == 1)[0] for j in range(self.n)]
        self.var_nodes_for_check = [np.where(self.H[i, :] == 1)[0] for i in range(self.m)]

    def _generate_systematic_ldpc_matrix(self, n: int, k: int, seed: Optional[int]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Create a low-density parity matrix in systematic form H = [P | I_m]
        such that G = [I_k | P^T] satisfies G H^T = 0 mod 2.
        P is an (m x k) sparse matrix with regular column degree d_v ~ 3.
        """
        m = n - k
        rng = np.random.default_rng(seed)

        # Target column weight d_v = 3 (standard Gallager column degree)
        d_v = min(3, m - 1)
        P = np.zeros((m, k), dtype=np.uint8)

        for col in range(k):
            # Select d_v distinct row indices for check connections
            rows = rng.choice(m, size=d_v, replace=False)
            P[rows, col] = 1

        # Ensure no check node is completely disconnected
        for row in range(m):
            if np.sum(P[row, :]) == 0:
                c = rng.integers(0, k)
                P[row, c] = 1

        # Assemble full parity check matrix H = [P | I_m] of shape (m, n)
        I_m = np.eye(m, dtype=np.uint8)
        H = np.hstack([P, I_m])

        # Systematic Generator matrix G = [I_k | P^T] of shape (k, n)
        I_k = np.eye(k, dtype=np.uint8)
        G = np.hstack([I_k, P.T])

        # Double check orthogonality: (G @ H.T) % 2 == 0
        syndrome_check = np.mod(G @ H.T, 2)
        assert np.all(syndrome_check == 0), "LDPC Generator and Parity-Check matrices must satisfy G @ H^T = 0 mod 2."

        return H, G, P

    def encode_block(self, message_bits: np.ndarray) -> np.ndarray:
        """
        Systematic encoding: codeword = [m | m @ P^T mod 2].
        Length = k + m = n.
        """
        m_bits = np.asarray(message_bits, dtype=np.uint8).flatten()
        if len(m_bits) != self.k:
            raise ValueError(f"Message block length must be exactly {self.k}, got {len(m_bits)}")

        parity_bits = np.mod(m_bits @ self.P.T, 2).astype(np.uint8)
        codeword = np.concatenate([m_bits, parity_bits])
        return codeword

    def decode_block(self, received: np.ndarray, channel_type: str = "awgn", **kwargs) -> np.ndarray:
        """
        Decode received block using Log-Domain Belief Propagation (Sum-Product or Min-Sum).
        Args:
            received: Received channel block (length n). If awgn, soft samples or LLRs;
                      if bsc, hard bits or transition log-ratios.
            channel_type: 'awgn' or 'bsc'
            snr_db / sigma / p: Channel parameters passed via kwargs.
        """
        y = np.asarray(received, dtype=np.float64).flatten()
        if len(y) != self.n:
            raise ValueError(f"Received block length must be {self.n}, got {len(y)}")

        # Convert received channel observation to initial Log-Likelihood Ratios (LLRs)
        # LLR_n = ln( P(x_n=0|y_n) / P(x_n=1|y_n) )
        # For BPSK: 0 -> +1, 1 -> -1
        if "llrs" in kwargs:
            L_ch = kwargs["llrs"]
        elif channel_type == "awgn":
            sigma = kwargs.get("sigma", 0.5)
            # LLR = 2 * y / sigma^2
            L_ch = (2.0 / (sigma**2)) * y
        elif channel_type == "bsc":
            if np.any(y < 0.0) or np.any(y > 1.0):
                L_ch = y.copy()
            else:
                p = kwargs.get("p", 0.05)
                p = np.clip(p, 1e-12, 0.5 - 1e-12)
                log_ratio = np.log((1.0 - p) / p)
                # If received bit is 0 -> +log_ratio, if 1 -> -log_ratio
                L_ch = log_ratio * (1.0 - 2.0 * y)
        elif channel_type in ("lossless", "ideal"):
            if np.any(y < 0.0) or np.any(y > 1.0):
                L_ch = y.copy()
            else:
                # Binary bits {0, 1}: 0 -> +50.0, 1 -> -50.0
                L_ch = 50.0 * (1.0 - 2.0 * y)
        else:
            if not (np.any(y < 0.0) or np.any(y > 1.0)) and np.all((y == 0.0) | (y == 1.0)):
                # Fallback for binary hard bits {0, 1}
                L_ch = 50.0 * (1.0 - 2.0 * y)
            else:
                # Assume y is already channel LLR
                L_ch = y.copy()

        # Initialize variable-to-check messages q_mn with channel LLRs
        # q_mn[i, j] is message from variable node j to check node i
        # We store messages only on non-zero edges of H
        # Sparse representation: dict or indexed array
        # Given n <= 256, 2D dense float array masked by H is extremely fast and vectorized
        q_mn = np.zeros((self.m, self.n), dtype=np.float64)
        for j in range(self.n):
            q_mn[self.check_nodes_for_var[j], j] = L_ch[j]

        r_mn = np.zeros((self.m, self.n), dtype=np.float64)

        # Iterative message passing
        for it in range(self.max_iter):
            # Check-to-variable update: r_mn
            for i in range(self.m):
                vars_i = self.var_nodes_for_check[i]
                q_vals = q_mn[i, vars_i]

                if self.algorithm == "min_sum":
                    signs = np.sign(q_vals)
                    signs[signs == 0] = 1.0
                    prod_sign = np.prod(signs)
                    abs_vals = np.abs(q_vals)

                    for idx, j in enumerate(vars_i):
                        # Sign of check message is product of all other signs
                        sign_ij = prod_sign * signs[idx]
                        # Min absolute value excluding j
                        other_abs = np.delete(abs_vals, idx)
                        min_val = np.min(other_abs) if len(other_abs) > 0 else 0.0
                        r_mn[i, j] = self.min_sum_scale * sign_ij * min_val

                else:
                    # Log-domain Sum-Product (tanh rule)
                    # Clip to prevent tanh from saturating exactly to +/-1.0 (causing division by zero in atanh)
                    q_clipped = np.clip(q_vals / 2.0, -19.0, 19.0)
                    tanh_vals = np.tanh(q_clipped)
                    prod_tanh = np.prod(tanh_vals)

                    for idx, j in enumerate(vars_i):
                        t_j = tanh_vals[idx]
                        if abs(t_j) > 1e-12:
                            other_prod = prod_tanh / t_j
                        else:
                            other_tanh = np.delete(tanh_vals, idx)
                            other_prod = np.prod(other_tanh)

                        other_prod = np.clip(other_prod, -0.999999999, 0.999999999)
                        r_mn[i, j] = 2.0 * np.arctanh(other_prod)

            # Variable-to-check update and total posterior LLR Q_j
            Q = L_ch.copy()
            for j in range(self.n):
                checks_j = self.check_nodes_for_var[j]
                r_sum = np.sum(r_mn[checks_j, j])
                Q[j] += r_sum

                for i in checks_j:
                    q_mn[i, j] = L_ch[j] + (r_sum - r_mn[i, j])

            # Hard decision on posterior LLR
            c_hat = (Q < 0).astype(np.uint8)

            # Parity check syndrome: s = H @ c_hat mod 2
            syndrome = np.mod(self.H @ c_hat, 2)
            if np.all(syndrome == 0):
                # Valid codeword detected! Early termination
                break

        # Extract systematic message bits (first k bits)
        return c_hat[:self.k]
