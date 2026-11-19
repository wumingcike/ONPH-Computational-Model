"""Statistics helpers used by the ONPH validation suite.

Monte Carlo replicates are *not* biological samples, so inference is based
on effect sizes, risk differences with Wilson intervals and bootstrap
intervals -- never on pseudo-replicated ANOVA p-values (review point M6).
"""

from __future__ import annotations

import numpy as np

CRITERION = 0.65  # fixed "long-term potentiation" criterion for w on day 7


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1.0 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def risk_difference_ci(a: np.ndarray, b: np.ndarray, threshold: float = CRITERION,
                       n_boot: int = 2000, seed: int = 0) -> dict:
    """Risk difference P(a >= thr) - P(b >= thr) with a bootstrap CI."""
    rng = np.random.default_rng(seed)
    pa, pb = float((a >= threshold).mean()), float((b >= threshold).mean())
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        sa = a[rng.integers(0, a.size, a.size)] >= threshold
        sb = b[rng.integers(0, b.size, b.size)] >= threshold
        diffs[i] = sa.mean() - sb.mean()
    return {
        "risk_a": pa,
        "risk_b": pb,
        "risk_diff": pa - pb,
        "ci_low": float(np.percentile(diffs, 2.5)),
        "ci_high": float(np.percentile(diffs, 97.5)),
    }


def cohens_d(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = a.size, b.size
    va, vb = a.var(ddof=1), b.var(ddof=1)
    pooled = np.sqrt(((na - 1) * va + (nb - 1) * vb) / max(na + nb - 2, 1))
    if pooled == 0:
        return 0.0
    return float((a.mean() - b.mean()) / pooled)


def overlap_coefficient(a: np.ndarray, b: np.ndarray, bins: int = 100) -> float:
    """Histogram overlap of two samples (OVL, 0 = disjoint, 1 = identical)."""
    lo = min(a.min(), b.min())
    hi = max(a.max(), b.max())
    if hi == lo:
        return 1.0
    edges = np.linspace(lo, hi, bins + 1)
    ha, _ = np.histogram(a, bins=edges, density=True)
    hb, _ = np.histogram(b, bins=edges, density=True)
    return float(np.minimum(ha, hb).sum() * (edges[1] - edges[0]))


def _rank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(x.size, dtype=float)
    ranks[order] = np.arange(1, x.size + 1)
    # average ties
    _, inv, counts = np.unique(x, return_inverse=True, return_counts=True)
    if (counts > 1).any():
        sums = np.zeros(counts.size)
        np.add.at(sums, inv, ranks)
        ranks = (sums / counts)[inv]
    return ranks


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    rx, ry = _rank(np.asarray(x, float)), _rank(np.asarray(y, float))
    rx -= rx.mean()
    ry -= ry.mean()
    denom = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / denom) if denom else 0.0


def describe(w: np.ndarray, threshold: float = CRITERION) -> dict:
    k = int((w >= threshold).sum())
    lo, hi = wilson(k, w.size)
    return {
        "n": int(w.size),
        "mean": float(w.mean()),
        "sd": float(w.std(ddof=1)),
        "median": float(np.median(w)),
        "q10": float(np.percentile(w, 10)),
        "q90": float(np.percentile(w, 90)),
        "p_ceiling": float((w >= 0.999).mean()),
        "p_floor": float((w <= 0.001).mean()),
        "p_criterion": k / w.size,
        "p_criterion_lo": lo,
        "p_criterion_hi": hi,
    }
