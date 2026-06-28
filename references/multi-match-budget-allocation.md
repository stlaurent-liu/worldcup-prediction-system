# 多场预算分配工作流 (2026-06-27 验证)

## 适用场景

用户提供固定预算（如200元），要求对某个比赛日的多场比赛进行投注分配。

## 工作流

### Step 1: 验证比赛清单和赔率

```python
# 1. Sporttery API 拉取所有在售世界杯比赛
# GET https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001
# 筛选 leagueAbbName == '世界杯'，按 matchDate 过滤目标日期

# 2. 解析 oddsList，提取 HAD 和 HHAD 赔率
# 注意：部分比赛只有 HHAD 在售，HAD 为空
```

### Step 2: 验证小组积分和出线形势

**MANDATORY: 不可假设任何球队的出线状态。必须实测。**

方法A — ESPN 积分榜（2026-06-27 验证可靠）：
```python
# browser_navigate 到 https://www.espn.com/soccer/standings/_/league/fifa.world
# browser_console 执行 JS 提取积分榜文本
# 返回所有12组的小组排名 + GP/W/D/L/F/A/GD/P 数据
```

方法B — AgentKey Surf/search-web 搜索（备用）：
```
搜索 "World Cup 2026 Group X standings after matchday 2"
交叉验证 Yahoo Sports / CBS Sports / ESPN 多源
```

**注意：AgentKey MCP 可能在运行中断连。浏览器搜索 Google 会被 CAPTCHA 拦截，Bing 搜索结果质量差。ESPN 直连是最可靠路径。**

### Step 3: 对每场比赛运行量化模型

对每场比赛执行：
1. Elo → Win/Draw/Loss 概率（使用校准表，缺失队用估值并标注 inferred）
2. Poisson λ 反推 → 比分分布
3. 市场赔率去水 → 真实概率
4. 三源融合: Poisson 50% + Market 40% + Elo 10%
5. EV 计算: `ev = fused_prob * odds - 1`
6. HHAD 让球分析: 根据让球数调整概率

### Step 4: 出线动机分析

对每场比赛，基于已验证的积分：
- 哪些队已出线？→ 可能轮换/保守
- 哪些队必须赢？→ 进攻意图强
- 哪些队平即出线？→ professional_control 模式
- 同组并发比赛是否影响出线？→ live_objective_shift

### Step 5: 正 EV 机会排序

将所有可选投注按 EV 排序，过滤：
- EV > 0 的方向
- 动机明确（非荣誉战）
- 赔率不太低（>1.40，否则性价比差）

### Step 6: Markowitz 均值-方差分配

```
Maximize: L = Σ b_i·edge_i - (λ/2)·Σ b_i²·σ_i²
Constraint: Σ b_i = B (budget), b_i ≥ 0
```

Lambda 选择：
| 场景 | λ | 
|:--|:--:|
| 默认 | 2.0 |
| 高信心 | 1.5 |
| 低信心/多 inferred 数据 | 3.0 |
| 全负 EV | 5.0 (最小化损失) |

### Step 6b: 体彩票面量化（mandatory）

Markowitz 输出连续理想金额；**体彩只能按 2元/注 下单**。外盘金额不可直接出票。

```python
from kelly_engine import quantize_budget

# allocations: { '周五072-阿根廷HHAD客胜': 73.5, ... }
# ticket_counts: 复式时传入注数，单式默认 1
ticket = quantize_budget(allocations, budget=200, ticket_counts={})
```

公式：`票面金额 = 注数 × 2元 × 倍数`

- 单式：优先 `1注 × N倍`
- 复式：先算注数（组合爆炸），再乘倍数
- 预算余数 &lt; 2元 → `unallocated_yuan`，并入最高 EV 或放弃

### Step 7: 输出格式

每场推荐包含：
- 场次编号 + 队名 + 玩法
- 赔率 + **注数 + 倍数 + 票面金额**（禁止只写理想金额）
- 可选：`理想金额`（Markowitz 参考值）+ `rounding_delta`
- 预期回报（按票面 × 赔率，非理想金额）
- 理由（动机 + EV + 模型概率）
- 风险说明

总预算分配汇总：
- 总票面（= Σ 注数×2×倍数，须为 2 的整数倍）
- 未分配余数（如有）
- 最优回报
- 最差情况（全输）
- 保本条件

### Step 8: 消费护栏

- 确认预算为娱乐支出，全输不影响生活
- 检测追损行为
- 提醒阵容未确认风险（T-90m 窗口）

## Pitfalls

1. **HAD 未开售陷阱**: 2026-06-27 实测，塞内加尔vs伊拉克和新西兰vs比利时只有 HHAD 在售。如果只查 HAD 会漏掉比赛。
2. **HAD/HHAD 仅过关陷阱**: 2026-06-27 实测，阿尔及利亚vs奥地利、刚果金vs乌兹别克的 HAD/HHAD 均为 `single:0`，胜平负/让球不能单关，须 2串1+。见 `sporttery-vs-overseas-rules.md`。
3. **单场详情 API 403**: `getMatchCalculatorV1.qry?matchId=XXX` 返回 403。改用 `getFixedBonusV1.qry` 查 `singleList`/CRS 赔率。
4. **Google CAPTCHA**: 从 Hermes 浏览器搜索 Google 会被 CAPTCHA 拦截。用 ESPN 直连或 AgentKey Surf/search-web 代替。
5. **AgentKey MCP 断连**: Surf/search-web 可能在会话中途断连。关键数据应在断连前获取，或用浏览器直连 ESPN 作为备用。
6. **Elo 估值偏差**: 比利时/乌拉圭 Elo 估值偏高（前2轮0进球），融合模型应加大市场权重、降低 Elo 权重。
7. **小组第3轮并发依赖**: 同组两场比赛同时进行，出线形势互相影响。必须同时分析两场，不能孤立看单场。
8. **让球方向**: Sporttery `goalLine` **正数=主队受让**（如 +2=主队受让2球），**负数=主队让球**（如 -1=主队让1球）。HHAD 为整数让球，不等于外盘亚盘小数盘。
9. **2元/注量化陷阱**: Markowitz 输出 `73.5元` 不能直接出票。必须 `quantize_stake` → `1注×2元×37倍=74元`。外盘连续金额套用到竞彩是常见失误。
