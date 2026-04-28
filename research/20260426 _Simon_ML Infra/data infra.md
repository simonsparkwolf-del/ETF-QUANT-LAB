# Data Infra
## Workflow
```mermaid
flowchart TB
    A[Google Drive Data Pool] --> B[Task Notebook given in Touch Point]
    B --> C[Data Auto downloaded in the same desktop folder of the Notebook]
```
## Data Framework
```mermaid
flowchart TB
    A[datapool.csv] --- bar[weekly_bars]
    bar --- bar1[etf1.csv]
    bar --- bar2[etf2.csv]
    bar --- bar3[PYS.csv]
    A --- dbar[daily_bars]
    dbar --- dbar1[etf1.csv]
    dbar --- dbar2[etf2.csv]
    dbar --- dbar3[PYS.csv]
    A --- alpha[weekly_alphas]
    alpha --- alpha1[etf1.csv]
    alpha --- alpha2[etf2.csv]
    A --- score[weekly_FRS]
    score --- score1[etf1.csv]
    score --- score2[etf2.csv]
    alphasuper[alphas.csv] --- alpha
    frssuperp[frs.csv] --- score
```
### ETF Name ENCODE
|TARGET_NAME|CODE|
|---|---|
|XLB US Equity PX|000001|

auto increment or SHA256

### FRS
Time Window Next 4 WED close prices
- FRS1 - Total Return: $(P_{wk4}-P_{wk0})/P_{wk0}$
- FRS2 - Sharp Ratio: $(avg(r_{wk1},...,r_{wk4})/std(r_{wk1},...,r_{wk4}))$
- FRS3 - Valotility Penalty Return Total: $Return - beta * std(r_{wk1},...,r_{wk4})$
