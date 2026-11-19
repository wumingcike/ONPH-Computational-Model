# archive_v1

The previous single-script version of the model, kept only for provenance.
**Do not cite these outputs as results.**

| File | What it is | Why it was retired |
|---|---|---|
| `117-111.py` | 195-line script with three hard-coded scenarios | group fate was fixed by the input schedule before simulation; no ablation was possible |
| `ONPH_Raw_Data_Full.csv` | 30,000 rows = 3 scenarios × 10,000 Monte Carlo replicates | not 30,000 independent circuits; replicates are not biological samples |
| `ONPH_Statistical_Report.txt` | one-way ANOVA + Tukey HSD on the replicates | pseudo-replicated p-values (F = 52207.8) carry no evidence |
| `ONPH_Final_Validated_Plot.png` | the "validated" figure | mean curves hide heavy boundary mass (A: 79% pinned at 1.0, C: 99%) |

The current model lives in `src/`; the current report is `docs/validation_zh.md`.
