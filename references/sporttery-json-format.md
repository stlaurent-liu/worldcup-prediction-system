# Sporttery 赔率数据格式 & 监控脚本

## JSON格式（sporttery_official_odds.json）

```json
[
  {
    "id": "2026001",
    "date": "2026-06-12",
    "time": "03:00",
    "league": "世界杯",
    "home": "墨西哥",
    "away": "南非",
    "handicap": "-1",
    "spf": [1.26, 4.45, 9.0],
    "rq": [2.0, 3.25, 3.11],
    "status": "已开售"
  }
]
```

**字段说明：**
- `spf`: [主胜H, 平D, 客胜A] — 胜平负赔率
- `rq`: [让球主胜H, 让球平D, 让球负A] — 让球胜平负赔率（空数组=未开售）
- `handicap`: 让球数（负数=主队让球）
- `status`: "已开售" | "未开售" | "已截止"

## 监控脚本

`.\scripts\wc2026_odds_monitor.py`

功能：
1. 读取当前赔率文件
2. 与上次数据对比，检测变化（阈值>5%）
3. 保存到SQLite `odds_snapshots` 表
4. 保存到历史目录 `odds_history/odds_{timestamp}.json`
5. 记录变化日志 `odds_changes.log`

## 抓取方法

### 方法1：Web API直达 ✅（推荐，2026-06-14验证，2026-06-27再次确认）

Sporttery官方API可直接curl：

```
GET https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001
Headers: User-Agent=Mozilla/5.0, Referer=https://www.sporttery.cn/
```

返回JSON，结构：
```json
{
  "value": {
    "matchInfoList": [{
      "businessDate": "2026-06-26",
      "subMatchList": [{
        "homeTeamAllName": "挪威",
        "awayTeamAllName": "法国",
        "matchDate": "2026-06-27",
        "matchTime": "03:00",
        "matchNumStr": "周五061",
        "matchStatus": "Selling",
        "oddsList": [
          {"poolCode": "HAD", "h": "4.35", "d": "4.15", "a": "1.52"},
          {"poolCode": "HHAD", "h": "2.20", "d": "3.30", "a": "2.69", "goalLine": "+1.00"}
        ]
      }]
    }]
  }
}
```

**poolCode 对照表（2026-06-27 实测确认）：**

| poolCode | 玩法 | 字段 | 说明 |
|:--|:--|:--|:--|
| HAD | 胜平负 | h/d/a | 主胜/平/客胜 |
| HHAD | 让球胜平负 | h/d/a + goalLine | goalLine 正=主队受让，负=主队让球 |
| HAFU | 半全场 | (9种组合) | 需展开 oddsList |
| CRS | 比分 | (多组) | 需展开 oddsList |
| TTG | 总进球 | (0-7+) | 需展开 oddsList |

**重要实测发现（2026-06-27）：**
- 并非所有比赛都开售 HAD。部分比赛（如塞内加尔vs伊拉克、新西兰vs比利时）只有 HHAD 在售，HAD 字段为空。
- 遇到 HAD 未开售时，不可直接跳过 — 必须检查 HHAD/HAFU/CRS/TTG 是否有值。
- `businessDate` 是比赛当地日期，不是北京时间日期。03:00 BJT 的比赛 businessDate 归前一天。
- oddsList 中 h/d/a 为空字符串 `""` 表示该玩法未开售，不是 null。
- **`getMatchCalculatorV1.qry` 返回 403，不可用。** 改用 `getFixedBonusV1.qry` 获取 CRS 比分赔率与单关状态（2026-06-27 验证 matchId=2040308）。

### 单场详情 API（getFixedBonusV1.qry）✅

```
GET https://webapi.sporttery.cn/gateway/uniform/football/getFixedBonusV1.qry?clientCode=3001&matchId=2040308
Headers: User-Agent=Mozilla/5.0, Referer=https://www.sporttery.cn/
```

关键字段（`value.oddsHistory`）：

| 字段 | 说明 |
|:--|:--|
| `singleList` | 单关开放状态。`[{"single": 1, "poolCode": "CRS"}, ...]` 表示该玩法可单关 |
| `crsList` | 比分赔率历史。最新一条为当前赔率；键名如 `s00s01`=0:1, `s01s00`=1:0, `s-1sd`=平其它 |
| `ttgList` | 总进球赔率 |
| `hafuList` | 半全场赔率 |

**CRS 单关核实示例（2026-06-27 世界杯 matchId=2040308）：**
```json
"singleList": [
  {"single": 1, "poolCode": "HHAD"},
  {"single": 1, "poolCode": "HAFU"},
  {"single": 1, "poolCode": "CRS"},
  {"single": 1, "poolCode": "TTG"}
]
```

出方案前必须先查 `singleList`：`single:1` = 可单关（浮动奖金），`single:0` = 仅过关（固定奖金）。适用于 **HAD/HHAD/CRS/TTG/HAFU 全部玩法**，勿默认胜平负永远可单关。完整规则见 `sporttery-vs-overseas-rules.md`。

**可靠解析代码模式：**

```python
import json, urllib.request

url = 'https://webapi.sporttery.cn/gateway/uniform/football/getMatchListV1.qry?clientCode=3001'
headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.sporttery.cn/'}
req = urllib.request.Request(url, headers=headers)
data = json.loads(urllib.request.urlopen(req, timeout=15).read().decode('utf-8'))

for m in data['value']['matchInfoList']:
    for sub in m.get('subMatchList', []):
        if sub.get('leagueAbbName') != '世界杯':
            continue
        home = sub['homeTeamAbbName']
        away = sub['awayTeamAbbName']
        for o in sub.get('oddsList', []):
            pool = o.get('poolCode', '')
            h, d, a = o.get('h',''), o.get('d',''), o.get('a','')
            gl = o.get('goalLine', '')
            if h and d and a:  # 非空=在售
                print(f"{sub['matchNumStr']} {home} vs {away} {pool} [{gl}] h:{h} d:{d} a:{a}")
```

### 方法2：浏览器自动化（备用）

如API不可用，回退：
browser_navigate("https://www.sporttery.cn/jsl/jczq/")
browser_vision(question="提取所有世界杯比赛的赔率数据")
```

然后手动整理为JSON格式保存。

## 交叉对比脚本输出（odds_cross_compare.py）

```bash
python3 scripts/odds_cross_compare.py
```

终端与 `数据/odds_cross_compare.json` 均包含：

| 字段 | 说明 |
|:--|:--|
| `had_on_sale` / `hhad_on_sale` | 玩法是否开售 |
| `single_status` | 各 pool 单关(`single`)或仅过关(`parlay_only`) |
| `deviation` | 体彩 HAD 隐含概率 vs 外盘去水偏差（HAD 未开售时为空） |
| `sporttery_mappings` | **外盘信号 → 竞彩可买映射**（玩法、赔率、单关/过关、语义、警示） |

HAD 未开售场次（如巴拿马 vs 英格兰）会输出 HHAD 三项语义说明，避免误写「胜平负客胜」。

## Cron定时监控

Job ID: YOUR_JOB_ID
Schedule: every 2h
