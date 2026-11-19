"""ONPH validation suite: five falsifiable experiment families.

E1  factorial ablation: confirmation x downscaling x replay gating
E2  dose-response: confirmation strength -> consolidation probability
E3  phase diagram: downscaling pressure x replay threshold
E4  instinct arm: initial weight x endogenous drive, no external input
E5  robustness: boundary rule, noise, initial weight, gains

Run ``python -m src.experiments`` from the repository root.  All outputs
land in ``results/``.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .model import Params, simulate
from .stats_utils import (CRITERION, cohens_d, describe, overlap_coefficient,
                          risk_difference_ci, spearman)

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
N_DAYS = 7
BASE_SEED = 2026


# --------------------------------------------------------------------- E1
def run_e1(n_per_arm: int = 30000) -> pd.DataFrame:
    rows, traj, store = [], [], {}
    arm = 0
    for confirm in (0.6, 0.0):
        for beta in (0.18, 0.0):
            for gating in ("sigmoid", "linear", "none"):
                p = Params(beta=beta)
                w = simulate(p, n=n_per_arm, days=N_DAYS, confirm=confirm,
                             gating=gating, seed=BASE_SEED + arm)
                key = f"c{confirm}_b{beta}_{gating}"
                store[key] = w[:, -1].astype(np.float32)
                row = {"arm": key, "confirm": confirm, "beta": beta,
                       "gating": gating, **describe(w[:, -1])}
                # trajectory quantiles (median + 10/90 band)
                for d in range(N_DAYS + 1):
                    q10, q50, q90 = np.percentile(w[:, d], [10, 50, 90])
                    traj.append({"arm": key, "day": d, "q10": q10,
                                 "median": q50, "q90": q90,
                                 "mean": float(w[:, d].mean())})
                rows.append(row)
                arm += 1

    df = pd.DataFrame(rows)

    # contrast: confirmed vs unconfirmed within each (beta, gating) cell
    extra = []
    for beta in (0.18, 0.0):
        for gating in ("sigmoid", "linear", "none"):
            a = store[f"c0.6_b{beta}_{gating}"].astype(float)
            b = store[f"c0.0_b{beta}_{gating}"].astype(float)
            rd = risk_difference_ci(a, b, CRITERION, seed=BASE_SEED)
            extra.append({"beta": beta, "gating": gating,
                          "risk_diff": rd["risk_diff"],
                          "rd_lo": rd["ci_low"], "rd_hi": rd["ci_high"],
                          "cohens_d": cohens_d(a, b),
                          "overlap": overlap_coefficient(a, b)})
    np.savez_compressed(RESULTS / "e1_day7.npz", **store)
    pd.DataFrame(traj).to_csv(RESULTS / "e1_trajectories.csv", index=False)
    pd.DataFrame(extra).to_csv(RESULTS / "e1_contrasts.csv", index=False)
    return df


# --------------------------------------------------------------------- E2
def run_e2(n_per_arm: int = 20000) -> pd.DataFrame:
    grid = np.round(np.linspace(0.0, 0.9, 16), 3)
    rows = []
    for i, c in enumerate(grid):
        w = simulate(Params(), n=n_per_arm, days=N_DAYS, confirm=float(c),
                     gating="sigmoid", seed=BASE_SEED + 100 + i)
        rows.append({"confirm": float(c), **describe(w[:, -1])})
    df = pd.DataFrame(rows)
    df.attrs["spearman"] = spearman(df["confirm"].to_numpy(),
                                    df["p_criterion"].to_numpy())
    return df


# --------------------------------------------------------------------- E3
def run_e3(n_per_arm: int = 4000) -> pd.DataFrame:
    betas = np.round(np.linspace(0.0, 0.30, 16), 4)
    thetas = np.round(np.linspace(0.40, 0.95, 14), 4)
    rows = []
    arm = 0
    for beta in betas:
        for theta in thetas:
            p = Params(beta=float(beta), theta=float(theta))
            vals = {}
            for confirm in (0.6, 0.0):
                w = simulate(p, n=n_per_arm, days=N_DAYS, confirm=confirm,
                             gating="sigmoid", seed=BASE_SEED + 500 + arm)
                vals[confirm] = describe(w[:, -1], threshold=CRITERION)
                arm += 1
            rows.append({
                "beta": float(beta), "theta": float(theta),
                "p_confirm": vals[0.6]["p_criterion"],
                "p_single": vals[0.0]["p_criterion"],
                "separation": vals[0.6]["p_criterion"] - vals[0.0]["p_criterion"],
                "mean_confirm": vals[0.6]["mean"],
                "mean_single": vals[0.0]["mean"],
            })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- E4
def run_e4(n_per_arm: int = 10000) -> pd.DataFrame:
    deltas = (0.0, 0.06, 0.12, 0.18, 0.24, 0.30)
    rows = []
    arm = 0
    for w0 in (0.05, 0.65):
        for delta in deltas:
            p = Params(delta=delta)
            w = simulate(p, n=n_per_arm, days=N_DAYS, confirm=0.0,
                         gating="sigmoid", instinct=True, w0=w0,
                         first_day=0.0, seed=BASE_SEED + 900 + arm)
            rows.append({"w0": w0, "delta": float(delta),
                         **describe(w[:, -1])})
            arm += 1
    return pd.DataFrame(rows)


# --------------------------------------------------------------------- E5
def run_e5(n_per_arm: int = 10000) -> pd.DataFrame:
    variants = [
        ("baseline", {}, 0.05),
        ("bounds=fold", {"bounds": "fold"}, 0.05),
        ("bounds=none", {"bounds": "none"}, 0.05),
        ("noise=0.04", {"noise": 0.04}, 0.05),
        ("noise=0.12", {"noise": 0.12}, 0.05),
        ("w0=0.10", {}, 0.10),
        ("w0=0.20", {}, 0.20),
        ("alpha=0.18", {"alpha": 0.18}, 0.05),
        ("alpha=0.26", {"alpha": 0.26}, 0.05),
        ("theta=0.58", {"theta": 0.58}, 0.05),
        ("theta=0.72", {"theta": 0.72}, 0.05),
    ]
    rows = []
    for i, (label, over, w0) in enumerate(variants):
        p = Params(**over)
        res = {}
        for beta in (0.18, 0.0):
            pb = p.with_(beta=beta)
            a = simulate(pb, n=n_per_arm, days=N_DAYS, confirm=0.6,
                         gating="sigmoid", w0=w0,
                         seed=BASE_SEED + 1300 + 2 * i)
            b = simulate(pb, n=n_per_arm, days=N_DAYS, confirm=0.0,
                         gating="sigmoid", w0=w0,
                         seed=BASE_SEED + 1301 + 2 * i)
            rd = risk_difference_ci(a[:, -1], b[:, -1], CRITERION,
                                    n_boot=1000, seed=BASE_SEED)
            res[f"sep_b{beta}"] = rd["risk_diff"]
            res[f"sep_b{beta}_lo"] = rd["ci_low"]
            res[f"sep_b{beta}_hi"] = rd["ci_high"]
            res[f"confirm_p_b{beta}"] = float((a[:, -1] >= CRITERION).mean())
        rows.append({"variant": label, "w0": w0, **res})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------- main
def main() -> None:
    RESULTS.mkdir(exist_ok=True)
    t0 = time.time()
    summary = {}

    print("[1/5] E1 factorial ablation ...", flush=True)
    e1 = run_e1()
    e1.to_csv(RESULTS / "e1_factorial.csv", index=False)

    print("[2/5] E2 dose-response ...", flush=True)
    e2 = run_e2()
    e2.to_csv(RESULTS / "e2_dose_response.csv", index=False)

    print("[3/5] E3 phase diagram ...", flush=True)
    e3 = run_e3()
    e3.to_csv(RESULTS / "e3_phase_map.csv", index=False)

    print("[4/5] E4 instinct arm ...", flush=True)
    e4 = run_e4()
    e4.to_csv(RESULTS / "e4_instinct.csv", index=False)

    print("[5/5] E5 robustness ...", flush=True)
    e5 = run_e5()
    e5.to_csv(RESULTS / "e5_robustness.csv", index=False)

    def pick(df, **kw):
        m = np.ones(len(df), bool)
        for k, v in kw.items():
            m &= np.isclose(df[k], v)
        return df[m].iloc[0]

    cons = pd.read_csv(RESULTS / "e1_contrasts.csv")
    full = cons[(np.isclose(cons.beta, 0.18)) & (cons.gating == "sigmoid")].iloc[0]
    null = cons[(np.isclose(cons.beta, 0.0)) & (cons.gating == "none")].iloc[0]
    summary["e1_full_separation"] = float(full.risk_diff)
    summary["e1_full_separation_ci"] = [float(full.rd_lo), float(full.rd_hi)]
    summary["e1_null_separation"] = float(null.risk_diff)
    summary["e1_null_separation_ci"] = [float(null.rd_lo), float(null.rd_hi)]
    summary["e1_table"] = cons.round(4).to_dict(orient="records")
    summary["e2_spearman"] = float(e2.attrs["spearman"])
    summary["e2_p_at_0"] = float(pick(e2, confirm=0.0)["p_criterion"])
    summary["e2_p_at_max"] = float(pick(e2, confirm=0.9)["p_criterion"])
    summary["e3_frac_positive"] = float((e3["separation"] > 0.10).mean())
    summary["e3_beta_at_zero_sep"] = float(
        e3[np.isclose(e3.beta, 0.0)]["separation"].mean())
    inst = pick(e4, w0=0.65, delta=0.18)
    noinst = pick(e4, w0=0.65, delta=0.0)
    summary["e4_maintained_with_drive"] = float(inst["p_criterion"])
    summary["e4_maintained_without_drive"] = float(noinst["p_criterion"])
    summary["e4_low_w0_with_drive"] = float(pick(e4, w0=0.05, delta=0.18)["p_criterion"])
    summary["e5_min_separation"] = float(e5["sep_b0.18"].min())
    summary["e5_max_separation"] = float(e5["sep_b0.18"].max())
    summary["runtime_sec"] = round(time.time() - t0, 1)
    summary["total_trajectories"] = int(
        30000 * 12 + 20000 * 16 + 4000 * 16 * 14 * 2 + 10000 * 12 + 10000 * 11 * 4)

    with open(RESULTS / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(json.dumps(summary, indent=2, ensure_ascii=False)[:2000])
    print(f"\nDone in {summary['runtime_sec']} s -> {RESULTS}")


if __name__ == "__main__":
    main()
