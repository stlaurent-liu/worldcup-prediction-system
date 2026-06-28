# World Cup 2026 Prediction — Agent Skill

**FIFA World Cup 2026 决策型预测 Skill**：面向 AI Agent（Grok / Cursor / Codex / Hermes），覆盖赛前/赛中分析、**中国体彩竞彩**六种玩法 EV、串关优化与量化引擎。

> 与 [Monte Carlo 网页模拟器](https://github.com/targetFuseLab/worldcup-2026-prediction-simulator) 不同：本项目不是可视化网站，而是给 **LLM Agent 用的可执行技能包**——含方法论（`SKILL.md`）、Python 脚本、回测参数和体彩规则库。

---

## Features

### 决策框架（怎么想）

- 小组赛 **出线动机** 优先于纯实力（必赢 / 平局够 / 已出线轮换 / 同组并发）
- 球队目标 vs 彩票目标分离（强队控分 ≠ 你的「胜」票）
- 气候适应（2026 北美：高温、湿度、海拔）
- 教练风格、轮换意图（`protective_rotation` vs `competitive_rotation`）
- 赛中触发器、消费护栏、Cashout 决策标签

### 量化引擎（怎么算）

| 模块 | 说明 |
|------|------|
| Elo → 胜平负 | 分差自适应平局修正 |
| Poisson λ 反推 | 比分分布 + Newton 迭代 |
| GBM 平局过滤器 | 5,058 场国际赛训练 |
| 三源融合 v6.0 | 小组赛偏市场 50%，淘汰赛偏 Elo 40% |
| 体彩去水 EV | Sporttery + Titan007 + Bet365 聚合 |
| Markowitz 配仓 | 均值-方差优化 + **2元/注票面量化** |
| 蒙特卡洛 | 5 万次出线模拟 |

### 体彩竞彩专用（中国）

- **六种玩法必扫**：HAD / HHAD / HAFU / CRS / TTG / 混合过关
- 外盘亚盘、大小球 **仅作概率参考**，出票必须映射回体彩玩法
- `singleList` 场次开放制（单关 vs 仅过关）
- 票据截图 → EV 分析 → 优化建议流水线

### 赛后数据管道

- `wc2026_results_sync.py`：ESPN 赛果 → 动机标签 → **加权 Elo** 更新
- 本机 cron（12:00 / 23:00 BJT），**2026-07-20 自动卸载**

---

## Backtest (v6.0, 5 World Cups, 384 matches)

| Metric | Value |
|--------|------:|
| Accuracy | 55.2% |
| Brier Score | 0.1925 |
| High-confidence (≥60%) accuracy | 72.7% |
| EV (+5% overround) | +3.20% |

---

## Quick Start

### 1. Clone & env

```bash
git clone git@github.com:stlaurent-liu/worldcup-prediction-system.git
cd worldcup-prediction-system
cp .env.example .env    # 可选：填入 THE_ODDS_API_KEY（外盘对比用）
```

### 2. 作为 Agent Skill 安装

将本目录链接或复制到 Agent 的 skills 路径，例如：

```bash
ln -s "$(pwd)" ~/.grok/skills/world-cup-prediction
# 或 Cursor / Codex / Hermes 对应 skills 目录
```

Agent 加载 **`SKILL.md`** 即获得完整工作流。用户发送竞彩截图、问「这场怎么买」时自动触发。

### 3. 拉取赛果 & 更新 Elo（本地）

```bash
python3 scripts/wc2026_results_sync.py --from 20260611   # 全量回溯
python3 scripts/wc2026_results_sync.py                 # 增量（最近 3 天）
```

数据库自动创建在 `data/football_database.sqlite`（不进 git）。

### 4. 可选：本机 cron

```bash
bash scripts/setup_wc2026_cron.sh --install   # 赛果 12:00/23:00 + 赔率每 2h
bash scripts/setup_wc2026_cron.sh --status
bash scripts/setup_wc2026_cron.sh --remove     # 手动卸载
```

---

## Key Scripts

| Script | Purpose |
|--------|---------|
| `wc2026_results_sync.py` | ESPN 赛果同步 + 动机标签 + Elo |
| `kelly_engine.py` | Kelly / EV + `quantize_stake`（2元/注） |
| `odds_ev_analysis.py` | 六种玩法 EV 扫描 |
| `multi_bookmaker_engine.py` | 多庄家去水聚合 |
| `monte-carlo-tournament.py` | 出线蒙特卡洛 |
| `wc2026_backtest.py` | 五届世界杯回测 |
| `odds_snapshot_cron.py` | 体彩赔率定时快照 |
| `setup_wc2026_cron.sh` | 本机 crontab 安装/卸载 |

---

## Project Structure

```
world-cup-prediction/
├── SKILL.md              # Agent 主技能文件（决策流程 + 量化引擎入口）
├── README.md             # 本文件（给人看）
├── modules/              # 分模块文档（模型、数据、投注策略…）
├── references/           # 规则手册、回测、体彩对照、赛程、Elo 校准…
├── scripts/              # 可执行 Python 引擎
├── config/               # calibrated-model.json
└── sample_data/          # 匿名样本库 + schema
```

**给 Agent 读**：`SKILL.md` → `references/sporttery-vs-overseas-rules.md`（体彩出票前必读）

**给人读**：本 README + `references/complete-betting-rules.md`

---

## Model (short)

```
PreMatchScore =
  motivation×25% + coach×15% + strength×15% + environment×15%
  + market×10% + style×8% + locker_room×7% + referee×5%

Fusion (group stage):  odds 50% + elo 20% + xg 15% + form 10% + fifa 5%
Fusion (knockout):     elo 40% + odds 30% + xg 15% + form 10% + fifa 5%
```

小组赛 Elo 更新带 **动机权重**（已出线轮换 ×0.2，必赢 ×1.0），避免控分场次污染实力估计。

---

## Data Sources

| Source | Use |
|--------|-----|
| ESPN API | 赛果、积分榜 |
| Sporttery API | 体彩赔率、singleList |
| Titan007 | 93–187 家亚盘去水 |
| worldcupwiki.com | 比分备用 |
| The Odds API | 外盘参考（需 `.env` key） |

---

## vs Web Simulators

| | 本项目 (Agent Skill) | 典型 Web 模拟器 |
|--|---------------------|----------------|
| 形态 | `SKILL.md` + Python + SQLite | Next.js 网页 + Worker |
| 用户 | AI Agent 对话 / 票据分析 | 浏览器交互 Dashboard |
| 体彩 | **六种玩法、2元/注、串关规则** | 通常无 |
| 动机模型 | 出线控分、轮换、同组依赖 | 较少 |
| 输出 | 决策标签 + EV + 可出票方案 | 冠军概率、 bracket 可视化 |

两者可互补：用模拟器看宏观 bracket，用本 Skill 做**单场体彩决策**。

---

## Origin

合并自两套系统（2026-06-26）：

1. **Hermes 决策框架** — 动机、教练、气候、护栏  
2. **[feibang191/worldcup-prediction-system](https://github.com/feibang191/worldcup-prediction-system)** — Elo/Poisson、回测、体彩引擎  

详见 `references/merge-history-20260626.md`。

---

## Disclaimer

本项目仅供体育数据分析与学习，不构成投注建议。竞彩有本金损失风险，请理性娱乐。

---

## License

[MIT](LICENSE)