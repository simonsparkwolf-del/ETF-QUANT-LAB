# Baseline Strategy — 行业ETF多空轮动策略

**作者**: Simon  
**版本**: v0.3  
**更新**: 2026-05-13  
**实现类**: `BaselineStrategy` / `BaselineRisk`

---

## 一、策略概述

每周从信号池中选取一个信号对 11 只行业 ETF 打分排名，做多得分最高的 3 只、做空得分最低的 3 只，构建市场中性（net ~0%）多空对冲组合。

---

## 二、信号层（Signal）

### 2.1 信号池（当前）

信号池目前包含两类信号，均通过 `Signal.analyze()` 输出 `OrderedDict[ticker, score]`：

| 类型 | 实现类 | 当前可用 |
|------|--------|---------|
| ML 模型输出 | `MLBacktestSignal(signal_id)` | signal 1–5 |
| 单 Alpha 因子 | `AlphaBacktestSignal(alpha_id)` | alpha 池中各 ID |

> 正在分别回测 ML 信号和 Alpha 信号，筛选最优信号后填入 § 八参数表。

### 2.2 风控专用 Alpha

以下 alpha 仅用于**风控模块**内部判断，不参与排名信号。

**接口约束**：所有 alpha 数据只能通过 `QuoteTerminal` 的接口获取，不得直接查询数据库。风控模块在 `on_action()` 内调用 `terminal.alphas(alpha_ids=(110,))`，结果按 `terminal.day` 缓存，同一周内多次调用只查一次 DB。

| Alpha | 接口 | 用途 |
|-------|------|------|
| `alpha_110`（12周累积收益率） | `terminal.alphas(alpha_ids=(110,))` | 做空过滤条件 + HEAVY→LIGHT 恢复判断 |

---

## 三、仓位结构

### 3.1 正常状态（全仓）

| 方向 | 标的数 | 单标的权重 | 合计占 NAV |
|------|--------|-----------|-----------|
| 多头 | 3 | +33.3% | +100% |
| 空头 | 3 | -33.3% | -100% |
| **毛敞口** | | | **200%** |
| **净敞口** | | | **~0%** |

### 3.2 各风控状态下的仓位

| 状态 | 多头 | 空头 | 毛敞口 |
|------|------|------|--------|
| NORMAL | +100% | -100% | 200% |
| LIGHT  | +50%  | -50%  | 100% |
| HEAVY  | 0%    | 0%    | 0%（纯现金）|

LIGHT 状态由 `BaselineRisk` 发出 `PositionChange(ratio=0.5)` 实现；HEAVY 状态发出 `EndTrade + NoTrade` 实现全平仓并阻断新建仓。

---

## 四、选标的规则（`BaselineStrategy`）

### 4.1 做多

- 信号排名 **前 `n_long` 名**，无额外过滤

### 4.2 做空

- 信号排名 **后 `n_short` 名**
- **且** `alpha_110` **< 0**（12周累积收益为负，即绝对动量为负）
- 若某个后 `n_short` 名 ETF 的 `alpha_110 ≥ 0`，该空头槽位**空置**，剩余满足条件的空头等权分配

> 做空过滤防止在上升趋势板块上逆势建空。

### 4.3 仓位定量

**新进仓位**按 `nav / n_long`（多头）或 `nav / n_short`（空头）定量买入，使用当日收盘价折算成股数。**存量持仓不重平衡**——已持有的头寸随市价自然漂移，换仓时整体平仓再按新目标重建。

---

## 五、调仓规则（`BaselineStrategy`）

### 5.1 频率

每周执行一次，对应 `weekly_bar` 周期，在 `on_ranking()` 中处理。`on_holding()` 返回空列表（所有仓位管理集中在 `on_ranking()`）。

### 5.2 排名粘性（Stickiness）

避免微小排名变动引起频繁换仓。**多头和空头分别独立判断。**

**粘性边界（绝对排名）：**

| 方向 | 保留条件 |
|------|---------|
| 多头 | 当前排名 ≤ `n_long + stickiness_threshold`（默认 ≤ 5） |
| 空头 | 当前排名 ≥ `n_total - n_short + 1 - stickiness_threshold`（默认 ≥ 7，共 11 只 ETF）|

示例（`n_long=3, stickiness_threshold=2, n_total=11`）：
- 多头持仓 ETF 当前排名 #5 → 5 ≤ 5 → **保留**
- 多头持仓 ETF 当前排名 #6 → 6 > 5 → **换出**
- 空头持仓 ETF 当前排名 #7 → 7 ≥ 7 → **保留**
- 空头持仓 ETF 当前排名 #6 → 6 < 7 → **换出**

**强制平仓（不受粘性保护）：**

- 持仓空头的 `alpha_110` 由负转正 → 立即平仓

**新进逻辑：**

在保留存量持仓后，空余槽位从当前排名头部（多头）或尾部（空头，含动量过滤）依次补充。

---

## 六、风险控制（`BaselineRisk`）

### 6.1 回撤计算

```
drawdown = max(0, (peak_nav - current_nav) / peak_nav)

peak_nav = max(
    历史快照中的最高 total_value,   # account.value_history
    当前 total_value                 # 今日 MTM，snapshot 前
)
初始无历史时以 initial_cash 为 peak_nav
```

### 6.2 状态转换

```
             DD ≥ dd_light          DD ≥ dd_heavy
  NORMAL ──────────────► LIGHT ──────────────► HEAVY
     ▲                      ▲
     │  DD < dd_recovery     │  proposed 多头中 ≥ heavy_recovery_min_pos
     │  连续 recovery_weeks  │  只 alpha_110 > 0，连续 recovery_weeks
     └──────────────────────┘
```

> 若某周 DD 从低于 `dd_light` 直接超过 `dd_heavy`，跨级直接进入 HEAVY。

### 6.3 恢复条件

| 恢复路径 | 条件 | 连续周数 |
|---------|------|---------|
| LIGHT → NORMAL | `drawdown < dd_recovery` | ≥ `recovery_weeks` |
| HEAVY → LIGHT | proposed 多头买入中 ≥ `heavy_recovery_min_pos` 只 `alpha_110 > 0` | ≥ `recovery_weeks` |

- 任意一周条件不满足，计数器**重置为 0**
- HEAVY → LIGHT 后仍需独立满足 LIGHT → NORMAL 的条件才能完全恢复

**关于 HEAVY 恢复的 proposed 多头**：`BaselineStrategy` 无论当前风控状态如何，始终根据信号排名生成完整的多头买入提案。`BaselineRisk.on_action()` 在检查恢复条件时直接读取这批提案中 `direction="long", side="buy"` 的 ticker，以此作为「当前 Top-N 候选」的代理。

---

## 七、边界情况

| 情形 | 处理 |
|------|------|
| 某 ETF 当周 `terminal.quote()` 返回空 | 跳过该 ticker，已持有的市价保持上周末值不变 |
| 满足做空过滤的 ETF 不足 `n_short` 只 | 有几只做几只，按 `nav / n_short` 各自定量，总空头 < 100% |
| 初始启动（无历史快照） | `peak_nav` fallback 为 `account.initial_cash`，状态初始化 NORMAL |
| HEAVY 期间新信号到来 | 策略生成提案但被 `NoTrade` 阻断；`EndTrade` 保证存量持仓全平 |

---

## 八、参数汇总

### `BaselineStrategy`

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `n_long` | 3 | 做多标的数 |
| `n_short` | 3 | 做空标的数 |
| `stickiness_threshold` | 2 | 粘性保留宽度（排名边界外允许偏移的位数） |
| `long_cost` | 0.0 | 多头交易成本率 |
| `base_slippage` | 0.0 | 基础滑点 |

### `BaselineRisk`

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `dd_light` | 0.10 | NORMAL→LIGHT 回撤阈值 |
| `dd_heavy` | 0.15 | LIGHT→HEAVY 回撤阈值（跨级直触 HEAVY） |
| `dd_recovery` | 0.08 | LIGHT→NORMAL 恢复阈值 |
| `recovery_weeks` | 2 | 恢复条件需连续满足的周数 |
| `heavy_recovery_min_pos` | 2 | HEAVY→LIGHT 恢复时 proposed 多头中需正动量标的数 |
| ~~`short_momentum_alpha`~~ | 固定 `alpha_110` | 硬编码，不可通过构造参数修改 |

---

## 九、待确认事项

- [ ] 借券成本 `short_cost_per_day` 的估算
- [ ] 是否需要流动性过滤（最低日均成交额门槛）
- [ ] `stickiness_threshold` 最优值通过参数优化确定