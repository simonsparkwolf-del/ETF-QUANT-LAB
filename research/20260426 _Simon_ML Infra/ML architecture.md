# ML based architecture
author: Simon

# **WARNING**
**DouBao is prohibited in development**
**请不要在任何开发环节使用豆包**


### A.The reason ML is introduced
1. **Faster and more powerful to select influential factors among large amount of factors.**
- No need to waste too much time on thinking how to compose new reasonable indexes.
- Don't have to try every combination of the indexes manually with a lot of scripts and lines of code.

2. It looks fancy to Sophiane and it's out of his knowledge scope.
- ML is the cutting edge topic in the field.
- ML is black box, instead of economic rationale, we focus on the performance.

3. It really learns something from the training dataset.
- Unsupervised method like baseline learns nothing from training dataset, which makes out-sample results outruns in-sample results.
- Unsupervised method like baseline needs a lot of tries to optimize the entire parameters to get a reasonable and sub-optimal outcome.

4. The project is more structured and easy to manage.
- We only need to iterate the weights and models to drive our strategy.

5. **Less code work**
- Compared to baseline model's heavy code. Several lines of code can train a powerful model.

### B.Architecture
#### **Requirement**
1. Good design on the whole pipeline - Once the model is developed, a small revision is required to upgrade the strategy.
2. Less redundant work for any group member.
3. A systematic infrastructure.

#### Illustration of the project and coworking
```mermaid
flowchart TB
    A[Data Pool: Bars + Alpha Pool + Additional Data] -->|taken by| B[ML model module]
    B -->|Generates | C[WIS - Worth Investing Scores]
    C -->|Rank the ETF and Analyzed by| D[Trading module]
    D -->|Trades in| E[Back Test Engine]
    A ---|Built by| Group1[Data + Infra Team]
    E ---|Built by| Group1
    B ---|Iterated and finetuned by| Group2[Model Dev Team]
    C ---|The criteria of ranking and the relevant mechanism is managed by| Group1
    D ---|Upgrade and adjusted by| Group3[Trade Control Team]
```

#### 1. Data Pool - Input of the model 
1. The data (training and testing) is prepared by Data Infra Team. All the alphas and necessary indexes are computed in the dataset. The model team don't have to compose the alphas. 
2. It's on weekly basis and exactly cooresponding to our weekly strategy.

#### 2. Worth Investing Score (WIS) - Target Value(mask) of the model
**The model has to fit the score**
1. The ETF is scored every week according to their performance in the future.
2. Data Infra Team is working on how to compose the index.
3. There will be a lot versions of WIS.

#### 3. ML model module
1. Learn from the traning data pool.
2. Generate the WIS as accurate as possible.

#### 4. Trading  module
**The Data Infra Team will extract the parameters out for optimizing**
1. Rank the ETFs according to WIS.
2. Decide how to trade.
3. Avoid risks.
4. Reduce voltality.

### C.Potential Risk
1. The model may be stupid and not competent.
