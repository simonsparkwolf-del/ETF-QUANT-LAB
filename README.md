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

- **research**: **the group member's playground** *keeps the experiments, the pilot tests. Name your folder porperly like "YYYYMMDD_OWNER_RESEARCH NAME" "20260426_Simon_ML Infra"- . **And save your documents including markdowns,model weights only in this private folder**.*

---
**The folder below are supposed to be changed only for official purpose approved by touchpoint meeting.**
- **backtests**: keeps the reports of backtest experiments on a set of models for horizontal comparison.
- **docs**: keeps the model blueprints and crucial documents in our project.
- **data**: keeps the ETF data (raw and processed) for training and backtest.
- **model_dev**: keeps the files related to the development of a model e.g. the training notebook, the artifacts etc.
- **reports**: keeps the outputs of a specific model and the reports about the model in e.g. results, data analysis etc.
- **src**: source code of our project. Use "import from QuantLab" in the project folder to call the modules.
- **script**： keeps the scripts of building the data pool or other change on the project.
- **weights**: keeps the weights of a certain model and the parameters of a certain data processing step if its traing is time-consuming.

## Reminders
- **All pilot tests including the documents should be placed in /research/XXX folder.**
- **Don't create any folder or any file outside /research folder unless Simon approves.**

## Milestones
1. April 21st - The first draft of baseline model.
2. April 26th - Alpha test and ML model architect drafts.
3. May 3rd - Structured database.
4. May 8th - ML signal source pilot test.
5. May 9th - Back test engine is ready.
6. May 11st - Datainfra and backtest engine are completed.
