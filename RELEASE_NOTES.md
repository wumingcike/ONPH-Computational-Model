# Release notes

## v2.0.0 — 2026-11-19

**A falsifiable reconstruction of the computational part.** The theory is unchanged; what changed is whether the simulation can fail.

### Added

- `src/model.py` — the update rule as a discrete-time stochastic difference equation (not an SDE), with four orthogonal switches: confirmation strength `c`, downscaling `beta`, replay gating `{sigmoid, linear, none}`, endogenous drive `delta`.
- `src/experiments.py` — five experiment families, **3,032,000 Monte Carlo trajectories**, fixed seeds, ~10 s on a laptop CPU:
  - **E1** factorial ablation 2 confirmation × 2 downscaling × 3 gating, N = 30,000/arm
  - **E2** dose–response over confirmation strength (16 levels)
  - **E3** phase diagram over downscaling × gate threshold (448 cells)
  - **E4** instinct arm: initial weight × endogenous drive, no external input
  - **E5** robustness: 11 structural variants
- `src/figures.py` — Figures 1–5, rendered headless.
- `src/stats_utils.py` — Wilson intervals, bootstrap risk differences, Cohen's d, histogram overlap, Spearman. **No pseudo-replicated ANOVA.**
- `results/` — machine-readable outputs plus `summary.json` and the day-7 weights of all 12 factorial arms.
- `docs/validation_zh.md`, `docs/validation_en.md` — full report with pre-registered falsification conditions.
- `CITATION.cff`, `requirements.txt`.

### Changed

- All arms now start from the same initial weight (W₀ = 0.05). The previous version started the "instinct" arm at 0.6, which confounded initial value with mechanism.
- Wake input is drawn from a truncated normal instead of `max(N(μ, 0.1), 0)`, removing a upward bias of ≈ 0.04 in the mean drive.
- `w_wake` is bounded before entering the replay gate; weights can no longer leave [0, 1] at any point, including the initial condition.
- The primary endpoint is P(W_day7 ≥ 0.65), a boundary-robust binary outcome, reported together with median, 10/90 quantiles and the fraction of trajectories pinned to 0 and 1.

### Results (headline)

| Contrast | Value |
|---|---|
| Full model separation P(confirmed) − P(single), β = 0.18, gated | **0.892** [0.888, 0.895] |
| Same, downscaling removed (β = 0) | 0.016 [0.015, 0.018] |
| Same, gate removed | 0.276 [0.271, 0.281] |
| Same, both removed (null model) | **0.000** |
| Dose–response Spearman ρ | 0.990 |
| Phase-plane fraction with separation > 0.1 | 81% |
| Instinct survival, δ = 0 vs 0.18 (W₀ = 0.65, no input) | 1.9% vs 99.4% |
| Minimum separation across 11 robustness variants | 0.507 |

### Removed

- `117-111.py`, `ONPH_Raw_Data_Full.csv`, `ONPH_Statistical_Report.txt`, `ONPH_Final_Validated_Plot.png` → moved to `archive_v1/` with an explanation of why each was retired.

### Notes

- The Zenodo DOI `10.5281/zenodo.18132447` refers to the archived v1 record. A v2 DOI is minted when this release is archived; cite the version you actually used.
- This is a model-generated simulation with calibrated (not fitted) parameters. It is not empirical validation.

---

## v1.0 — 2025

Single script (`117-111.py`) with three hard-coded scenarios, a 30,000-row CSV of Monte Carlo replicates, and one-way ANOVA on those replicates. Retired; see `archive_v1/README.md`.
