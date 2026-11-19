"""Figures 1-5 for the ONPH validation suite.

Usage: ``python -m src.figures`` (reads ``results/*.csv``, writes
``figures/fig*.png``).  Rendering is headless (Agg).
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .model import Params, simulate
from .stats_utils import CRITERION

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
FIGS = ROOT / "figures"

C_CONFIRM = "#1f6feb"
C_SINGLE = "#d1495b"
C_NEUTRAL = "#6b7280"
C_ACCENT = "#f0a202"

plt.rcParams.update({
    "figure.dpi": 160,
    "savefig.dpi": 200,
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "legend.frameon": False,
})


def _save(fig, name: str) -> None:
    FIGS.mkdir(exist_ok=True)
    fig.savefig(FIGS / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  wrote figures/{name}")


# ------------------------------------------------------------------ fig 1
def fig1_factorial() -> None:
    cons = pd.read_csv(RESULTS / "e1_contrasts.csv")
    traj = pd.read_csv(RESULTS / "e1_trajectories.csv")
    summ = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))

    fig = plt.figure(figsize=(11.5, 7.2))
    gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 1.0], hspace=0.42,
                          wspace=0.32)

    # A: 2x3 separation map
    ax = fig.add_subplot(gs[0, :2])
    mat = np.zeros((2, 3))
    for j, g in enumerate(["sigmoid", "linear", "none"]):
        for i, b in enumerate([0.18, 0.0]):
            mat[i, j] = cons[(np.isclose(cons.beta, b)) &
                             (cons.gating == g)]["risk_diff"].iloc[0]
    im = ax.imshow(mat, cmap="Blues", vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(3))
    ax.set_xticklabels(["gated\nsigmoid", "linear", "ungated\n(constant)"])
    ax.set_yticks(range(2))
    ax.set_yticklabels(["downscaling ON\n(β = 0.18)", "downscaling OFF\n(β = 0)"])
    for i in range(2):
        for j in range(3):
            ax.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center",
                    fontsize=13, fontweight="bold",
                    color="white" if mat[i, j] > 0.55 else "#111")
    ax.set_title("(A) Adjudication strength: P(consolidated | confirmed) − P(consolidated | single exposure)\n"
                 "the two null models in the bottom row / right column abolish the effect",
                 loc="left", fontsize=9.5)
    ax.grid(False)
    ax.add_patch(plt.Rectangle((1.5, -0.5), 1, 2, fill=False, ec=C_ACCENT,
                               lw=2.2))
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02, label="risk difference")

    # B: null-model comparison bars
    axb = fig.add_subplot(gs[0, 2])
    labels = ["full model\nβ=0.18, gated", "no downscaling\nβ=0", "no gating\n(β=0.18)"]
    rows = [cons[(np.isclose(cons.beta, 0.18)) & (cons.gating == "sigmoid")].iloc[0],
            cons[(np.isclose(cons.beta, 0.0)) & (cons.gating == "sigmoid")].iloc[0],
            cons[(np.isclose(cons.beta, 0.18)) & (cons.gating == "none")].iloc[0]]
    vals = [float(r.risk_diff) for r in rows]
    lo = [float(r.rd_lo) for r in rows]
    hi = [float(r.rd_hi) for r in rows]
    colors = [C_CONFIRM, C_NEUTRAL, C_NEUTRAL]
    axb.bar(range(3), vals, color=colors, alpha=0.85, width=0.62)
    axb.errorbar(range(3), vals, yerr=[np.array(vals) - np.array(lo),
                                       np.array(hi) - np.array(vals)],
                 fmt="none", ecolor="#222", lw=1.2, capsize=3)
    for k, v in enumerate(vals):
        axb.text(k, v + 0.05, f"{v:.2f}", ha="center", fontsize=10,
                 fontweight="bold")
    axb.set_xticks(range(3))
    axb.set_xticklabels(labels, fontsize=7.5)
    axb.set_ylim(0, 1.08)
    axb.set_ylabel("risk difference")
    axb.set_title("(B) Each mechanism is necessary\n(removing it collapses the effect)",
                  loc="left")

    # C: trajectories
    axc = fig.add_subplot(gs[1, :2])
    pick = [("c0.6_b0.18_sigmoid", C_CONFIRM, "confirmed + downscaling (full model)"),
            ("c0.0_b0.18_sigmoid", C_SINGLE, "single exposure + downscaling"),
            ("c0.0_b0.18_none", C_NEUTRAL, "single exposure, no gate (β=0.18)")]
    for key, col, lab in pick:
        d = traj[traj.arm == key]
        axc.fill_between(d.day, d.q10, d.q90, color=col, alpha=0.16, lw=0)
        axc.plot(d.day, d["median"], color=col, lw=2.2, label=lab)
    axc.axhline(CRITERION, ls="--", color="#444", lw=1)
    axc.text(0.05, CRITERION + 0.03, "consolidation criterion (0.65)", fontsize=7.5,
             color="#444")
    axc.set_xlabel("day"); axc.set_ylabel("synaptic weight W")
    axc.set_ylim(-0.02, 1.04); axc.set_xlim(0, 7)
    axc.set_title("(C) Median with 10–90% band (n = 30,000 per arm)", loc="left")
    axc.legend(loc="lower left", fontsize=7.5)

    # D: final distributions
    axd = fig.add_subplot(gs[1, 2])
    z = np.load(RESULTS / "e1_day7.npz")
    a = z["c0.6_b0.18_sigmoid"]; b = z["c0.0_b0.18_sigmoid"]
    bins = np.linspace(0, 1, 41)
    axd.hist(a, bins=bins, density=True, color=C_CONFIRM, alpha=0.55,
             label="confirmed", histtype="stepfilled", lw=1.2, edgecolor=C_CONFIRM)
    axd.hist(b, bins=bins, density=True, color=C_SINGLE, alpha=0.45,
             label="single", histtype="stepfilled", lw=1.2, edgecolor=C_SINGLE)
    axd.set_xlabel("W on day 7"); axd.set_ylabel("density")
    axd.set_title("(D) Day-7 distribution\n(boundary mass is reported)", loc="left")
    axd.legend(fontsize=7.5)
    axd.text(0.02, axd.get_ylim()[1] * 0.62,
             f"floor≤0.001: {np.mean(b <= 0.001):.0%} (single)\n"
             f"ceiling≥0.999: {np.mean(a >= 0.999):.0%} (confirmed)",
             fontsize=7, color="#333")

    fig.suptitle("Figure 1  Factorial ablation of the ONPH adjudication mechanism",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    _save(fig, "fig1_factorial.png")


# ------------------------------------------------------------------ fig 2
def fig2_dose_response() -> None:
    df = pd.read_csv(RESULTS / "e2_dose_response.csv")
    summ = json.loads((RESULTS / "summary.json").read_text(encoding="utf-8"))

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.9))

    ax = axes[0]
    ax.fill_between(df.confirm, df.p_criterion_lo, df.p_criterion_hi,
                    color=C_CONFIRM, alpha=0.2, lw=0)
    ax.plot(df.confirm, df.p_criterion, "o-", color=C_CONFIRM, lw=2, ms=4)
    ax.axhline(0.5, ls=":", color="#444", lw=1)
    ax.axhline(0.107, ls="--", color=C_SINGLE, lw=1)
    ax.text(0.02, 0.13, "single exposure\n(no confirmation): 10.7%",
            fontsize=7.5, color=C_SINGLE)
    ax.set_xlabel("confirmation strength c (daily re-exposure amplitude)")
    ax.set_ylabel("P(W ≥ 0.65 on day 7)")
    ax.set_ylim(-0.03, 1.05)
    ax.set_title(f"(A) Dose–response, Spearman ρ = {summ['e2_spearman']:.3f}",
                 loc="left")

    ax2 = axes[1]
    ax2.plot(df.confirm, df["median"], "o-", color=C_NEUTRAL, lw=1.8, ms=4,
             label="median W")
    ax2.plot(df.confirm, df["mean"], "s--", color=C_ACCENT, lw=1.5, ms=3.5,
             label="mean W (boundary-compressed)")
    ax2.fill_between(df.confirm, df.q10, df.q90, color=C_NEUTRAL, alpha=0.13, lw=0)
    ax2.axhline(CRITERION, ls="--", color="#444", lw=1)
    ax2.set_xlabel("confirmation strength c  (c = 0 → single exposure)")
    ax2.set_ylabel("W on day 7")
    ax2.set_title("(B) Median vs mean: boundary compression of the mean", loc="left")
    ax2.legend(fontsize=7.5, loc="lower right")

    fig.suptitle("Figure 2  A threshold in confirmation strength (c ≈ 0.05), not a gradual dial",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, "fig2_dose_response.png")


# ------------------------------------------------------------------ fig 3
def fig3_phase_map() -> None:
    df = pd.read_csv(RESULTS / "e3_phase_map.csv")
    betas = np.sort(df.beta.unique())
    thetas = np.sort(df.theta.unique())
    Z = df.pivot(index="beta", columns="theta", values="separation").loc[betas, thetas].to_numpy()

    fig = plt.figure(figsize=(11.0, 4.0))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1.0], wspace=0.3)

    ax = fig.add_subplot(gs[0, 0])
    im = ax.imshow(Z, origin="lower", aspect="auto", cmap="viridis",
                   vmin=0, vmax=1,
                   extent=[thetas[0], thetas[-1], betas[0], betas[-1]])
    cs = ax.contour(thetas, betas, Z, levels=[0.1, 0.5, 0.9],
                    colors="white", linewidths=[0.8, 1.3, 0.8],
                    linestyles=["--", "-", "--"])
    ax.clabel(cs, fmt="%.1f", fontsize=7)
    ax.plot([0.65] * 2, [0.14, 0.22], color=C_ACCENT, lw=2.2)
    ax.plot(0.65, 0.18, "o", color=C_ACCENT, ms=7)
    ax.annotate("calibrated\n(θ=0.65, β=0.18)", (0.65, 0.18),
                xytext=(0.78, 0.245), fontsize=7.5, color="white",
                arrowprops=dict(arrowstyle="->", color="white", lw=1))
    ax.set_xlabel("replay gate threshold θ"); ax.set_ylabel("downscaling pressure β")
    ax.set_title("(A) Separation over the (β, θ) plane", loc="left")
    ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.035, pad=0.02,
                 label="P(conf) − P(single)")

    ax2 = fig.add_subplot(gs[0, 1])
    for target, col, lw in [(0.53, C_NEUTRAL, 1.2), (0.65, C_CONFIRM, 2.4),
                            (0.78, C_ACCENT, 1.2)]:
        th = thetas[np.argmin(np.abs(thetas - target))]
        d = df[np.isclose(df.theta, th)].sort_values("beta")
        ax2.plot(d.beta, d.separation, "o-", color=col, lw=lw, ms=3,
                 label=f"θ = {th:.2f}")
    ax2.axhline(0.0, color="#333", lw=0.8)
    ax2.set_xlabel("downscaling pressure β"); ax2.set_ylabel("separation")
    ax2.set_ylim(-0.05, 1.05)
    ax2.set_title("(B) Collapse as downscaling is removed", loc="left")
    ax2.legend(fontsize=7.5)

    fig.suptitle("Figure 3  Phase diagram: where adjudication exists",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    _save(fig, "fig3_phase_map.png")


# ------------------------------------------------------------------ fig 4
def fig4_instinct() -> None:
    df = pd.read_csv(RESULTS / "e4_instinct.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.9))

    ax = axes[0]
    for w0, col, lab in [(0.65, C_CONFIRM, "pre-existing instinct (W₀ = 0.65)"),
                         (0.05, C_SINGLE, "no prior instinct (W₀ = 0.05)")]:
        d = df[np.isclose(df.w0, w0)].sort_values("delta")
        ax.fill_between(d.delta, d.p_criterion_lo, d.p_criterion_hi,
                        color=col, alpha=0.18, lw=0)
        ax.plot(d.delta, d.p_criterion, "o-", color=col, lw=2, ms=4, label=lab)
    ax.axhline(0.02, ls=":", color="#444", lw=1)
    ax.axvline(0.18, ls=":", color=C_ACCENT, lw=1.2)
    ax.text(0.205, 0.42, "δ = β = 0.18\nmaintenance threshold", fontsize=7.2,
            color="#8a6400", rotation=90, va="center")
    ax.set_xlabel("endogenous drive δ (per sleep cycle)")
    ax.set_ylabel("P(W ≥ 0.65 on day 7)")
    ax.set_ylim(-0.03, 1.05)
    ax.set_title("(A) A maintenance bifurcation at δ ≈ β", loc="left")
    ax.legend(fontsize=7.5, loc="upper left")

    # trajectories for the two extremes
    ax2 = axes[1]
    for delta, col, ls in [(0.0, C_SINGLE, "-"), (0.18, C_CONFIRM, "-")]:
        p = Params(delta=delta)
        w = simulate(p, n=6000, confirm=0.0, gating="sigmoid", instinct=True,
                     w0=0.65, first_day=0.0, seed=77)
        ax2.fill_between(range(8), np.percentile(w, 10, axis=0),
                         np.percentile(w, 90, axis=0), color=col, alpha=0.16, lw=0)
        ax2.plot(range(8), np.median(w, axis=0), color=col, lw=2.1,
                 label=f"δ = {delta}")
    ax2.axhline(CRITERION, ls="--", color="#444", lw=1)
    ax2.set_xlabel("day"); ax2.set_ylabel("W")
    ax2.set_ylim(-0.02, 1.04)
    ax2.set_title("(B) Trajectories without any external input", loc="left")
    ax2.legend(fontsize=8)

    fig.suptitle("Figure 4  The instinct arm: maintenance above a threshold",
                 x=0.02, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save(fig, "fig4_instinct.png")


# ------------------------------------------------------------------ fig 5
def fig5_robustness() -> None:
    df = pd.read_csv(RESULTS / "e5_robustness.csv")
    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    y = np.arange(len(df))[::-1]
    for yi, (_, r) in zip(y, df.iterrows()):
        col = C_CONFIRM if r.variant == "baseline" else C_NEUTRAL
        ax.plot([r["sep_b0.18_lo"], r["sep_b0.18_hi"]], [yi, yi],
                color=col, lw=2.6, alpha=0.55, solid_capstyle="round")
        ax.plot(r["sep_b0.18"], yi, "o", color=col, ms=6,
                mfc="white" if r.variant != "baseline" else col)
        ax.text(r["sep_b0.18_hi"] + 0.012, yi, f"{r['sep_b0.18']:.2f}",
                va="center", fontsize=7.5, color="#333")
    ax.set_yticks(y)
    ax.set_yticklabels(df.variant, fontsize=8)
    ax.set_xlabel("separation: P(consolidated | confirmed) − P(consolidated | single)")
    ax.set_xlim(0.4, 1.03)
    ax.set_title("Figure 5  The effect survives every structural perturbation\n"
                 "(95% bootstrap CI; separation ≥ 0.5 in all 11 variants)",
                 loc="left", fontsize=10)
    ax.axvline(0.5, ls=":", color="#444", lw=1)
    _save(fig, "fig5_robustness.png")


def main() -> None:
    print("rendering figures ...")
    fig1_factorial()
    fig2_dose_response()
    fig3_phase_map()
    fig4_instinct()
    fig5_robustness()
    print("done ->", FIGS)


if __name__ == "__main__":
    main()

