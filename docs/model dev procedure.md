# The standard procdure of developing quant models in this project
When you try to develop a version of a model, please use **/model_dev** folder. You can place a notebook or notebooks of how this model is developed in corresponding model folder e.g. **/model_dev/baseline**.
```mermaid
flowchart TD
    A[Load the right version of data in /data/processed folder] --> B[Do data analysis]
    B --> C[Data processing (please elaborate your methods in the notebook markdown)]
    C --> D[Model training ]
    D --> E[Model evaluation using the backtest engine in /src/backtest or modify the template in /backtests (don't overwrite the template)]
    E --> F[Choose the best performing result]
    F --> G{Is training/data processing time-consuming?(>15 mins)}
    G -->|YES| H[Save the entire model with weights and params of data preprocessing in /model and name the file properly]
    G -->|NO| I[Never mind]
    I --> J[Ask LLM to generate a written report]
    H --> J
    J --> K[Save the written report in the same folder]
```
## After model development
If the small team completes model development, David, Jeffrey, Simon will reorganize the code and do more tests on the model to perfect our quant project (adding new metrics, finding bugs in the model). All code assets are stored in Github repository. And when the project is close to the end, LLM will read our whole repository to formulate the final written report containing the whole story of our project. 