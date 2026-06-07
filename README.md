# ETF-QUANT-LAB
The repository of 2026 CUHK BA group W's ETF quant project.

# **WARNING**
**DouBao is prohibited in development**
**请不要在任何开发环节使用豆包**

## Reminder
**Download/Pull the project from main branch!!!** <img width="218" height="45" alt="image" src="https://github.com/user-attachments/assets/874663c0-4d78-4f4b-8ef5-219d74adf160" />

## Installation
First generate your python venv and activate it (ask your agent to do so).
Before you run or develop the project please install the packages and dependencies using command in powershell.
```PowerShell
cd your_project_dir_path
python -m pip install -e .
```
Whenever run your code, remember only in venv.

## Folders

- **research**: **the group member's playground** — keeps experiments, pilot tests, and personal notes. Name your folder like `YYYYMMDD_OWNER_Topic` (e.g. `20260426_Simon_ML-Infra`). Save all personal documents and model weights here.

---
**The folders below are changed only for official purposes approved by a touchpoint meeting.**

- **src**: source code (`QuantLab` package). Use `from QuantLab.xxx import yyy` to call modules.
- **backtests**: backtest run outputs, organised by strategy type and cost regime.
- **docs**: design documents, architecture specs, and research roadmap.
- **data**: ETF raw and processed data (`data/processed/data.csv` is the main input).
- **scripts**: data pipeline scripts (e.g. `dataset_builder.ipynb`).
- **debrief**: periodic team reports (`YYYYMMDD/report.md` + `report.html`).

## Reminders
- **All pilot tests and personal documents must go in `/research/XXX`.**
- **Do not create folders or files outside `/research` without Simon's approval.**

## Database
- run **.\scripts\dataset_builder.ipynb** to build the sqlite database

## Milestones
1. April 21st — First draft of baseline model.
2. April 26th — Alpha test and ML model architecture drafts.
3. May 3rd — Structured database (`datapool.db`).
4. May 8th — ML signal pilot test.
5. May 9th — Backtest engine ready.
6. May 11th — Data infrastructure and backtest engine completed.
7. May 13th — Signal optimization Step 1 + Baseline L/S screening completed (IS + OOS).
8. May 14th — Design 01 (Dual-Signal L/S) completed: IS + OOS grid + transaction cost validation.
9. May 15th — Signal blend experiments (Step 2 LP/SP + Step 3 joint) completed: all negative; `l57_s23` confirmed as production signal configuration (OOS Sharpe 2.152).
10. May 26th — **Look-forward evaluation structure + daily data random forest feature consolidation structure**
