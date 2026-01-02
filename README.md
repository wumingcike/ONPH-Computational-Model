# ONPH Computational Model: In Silico Validation
# 离线神经可塑性稳态假说 (ONPH) 计算仿真模型

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

## 📖 Introduction / 项目简介

This project provides the **computational verification** for the **Offline Neural Plasticity Homeostasis (ONPH) Hypothesis**. Using stochastic differential equations (SDEs) and large-scale Monte Carlo simulations (N=30,000), we validate that sleep functions as a **bidirectional adjudication system**—consolidating confirmed memories while actively pruning noise—and an **endogenous generator** for instinct preservation.

本项目为 **“离线神经可塑性稳态假说 (ONPH)”** 提供了**计算验证**。通过随机微分方程 (SDE) 和大规模蒙特卡洛模拟 (N=30,000)，我们证实了睡眠作为**双向判定系统**的功能——在巩固经确认记忆的同时主动修剪噪音——并作为本能维持的**内源性发生器**。

---

## 📊 Simulation Results / 仿真结果展示

### The "Golden Bifurcation" of Memory Fate
### 记忆命运的“黄金分叉点”

The visualization below demonstrates the critical phase transition at Day 2. **Wake-phase confirmation** acts as a filter, allowing valid memories (Blue) to breach the replay threshold, while unconfirmed noise (Green) is suppressed by homeostatic pressure. Instincts (Orange) remain stable without external input.

下图展示了第 2 天出现的关键相变。**觉醒期确认**作为过滤器，允许有效记忆（蓝线）冲破重放阈值，而未确认的噪音（绿线）则被稳态压力抑制。本能（橙线）在无外部输入的情况下保持稳定。

![ONPH Final Plot](ONPH_Final_Validated_Plot.png)

*(Statistical Analysis: One-way ANOVA & Tukey HSD confirmed significant divergence with p < 0.001)*
*(统计分析：单因素方差分析与 Tukey HSD 检验确认了显著差异，p < 0.001)*

---

## 💾 Data Availability / 数据获取

The full raw dataset containing **30,000 individual neural circuit trajectories** is included in this repository for replication:
本仓库包含 **30,000 个独立神经回路轨迹** 的全量原始数据集，以供复现：

* 📄 **`ONPH_Raw_Data_Full.csv`**

---
