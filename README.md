# ETF-QUANT-LAB
The repository of 2026 CUHK BA group W's ETF quant project.

## Reminder
**Download/Pull the project from main branch!!!** <img width="218" height="45" alt="image" src="https://github.com/user-attachments/assets/874663c0-4d78-4f4b-8ef5-219d74adf160" />

## Installation
Before you run or develop the project please install the packages and dependencies using command in powershell.
```PowerShell
cd your_project_dir_path
python -m pip install -e .
```

## Folders
- **backtests**: keeps the reports of backtest experiments on a set of models for horizontal comparison.
- **docs**: keeps the model blueprints and crucial documents in our project.
- **data**: keeps the ETF data (raw and processed) for training and backtest.
- **model_dev**: keeps the files related to the development of a model e.g. the training notebook, the artifacts etc.
- **reports**: keeps the outputs of a specific model and the reports about the model in e.g. results, data analysis etc.
- **src**: source code of our project. Use "import from QuantLab" in the project folder to call the modules.
- **script**： keeps the scripts of building the data pool or other change on the project.
- **weights**: keeps the weights of a certain model and the parameters of a certain data processing step if its traing is time-consuming.

## Milestones
1. April 21st - The first draft of baseline model.
