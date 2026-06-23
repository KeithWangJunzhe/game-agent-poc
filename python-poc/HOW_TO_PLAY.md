# How To Play

这是给人看的对局说明。这个 POC 先走 `CLI`，不做可视化。

## 怎么开始

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/run_poc.py
```

如果想手动下命令，可以直接进入交互模式：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/run_poc.py --interactive
```

也可以先看 demo：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/run_poc.py --demo
```

## 你能看到什么

- 当前回合
- 当前行动玩家
- 战场 ASCII 图
- 双方还差多少金才能获胜
- 当前行动方可用的合法动作提示
- 双方单位的位置、血量、当前可移动方向
- 资源点、事件日志
- 对局结束后的复盘 stats 和 JSON 记录

## 对局怎么开始

默认会自动创建一局新对局，不需要手工建房。
在对战 harness 里，模型可能会随机拿到 `p1` 或 `p2` 身份，并随机决定先后手；手动 `interactive` 只随机起手顺序。

初始局面：

- 地图大小：`10x10`
- 玩家：`p1` 和 `p2`
- 单位：每边一个 `base`、一个 `worker`、一个 `warrior`
- 资源点：地图中间有一个金矿

## 你能做什么

### 移动单位

```json
{"type": "move_unit", "unit_id": "p1_worker", "direction": "east"}
```

方向支持：

- `north`
- `south`
- `west`
- `east`

### 采集资源

```json
{"type": "gather", "unit_id": "p1_worker"}
```

规则：

- 只有 `worker` 能采集
- worker 必须站在资源点上
- 每次采集会让资源点减少 `1`

采集在这个 POC 里先作为一个最小经济动作保留，作用是让后续可以自然接上：

- 资源积累
- 造兵或升级
- 让 agent 在行动选择里需要考虑“抢资源”而不是只会打架

### 攻击

```json
{"type": "attack", "attacker_id": "p1_warrior", "target_id": "p2_base"}
```

规则：

- 只有非 `base` 单位能攻击
- 目标必须是敌方单位
- 必须相邻才能攻击

### 结束回合

```json
{"type": "end_turn"}
```

如果你这回合不想动，也可以直接结束回合。

## 胜利条件

- 当一方先累计到 `10 gold` 时，对局结束
- 当一方的 `base` 被打掉时，对局结束
- 只要满足其中一个条件即可获胜

## 其他规则

- 只有当前行动玩家可以下命令
- 不能走出地图边界
- 不能走到别的单位身上
- 一条命令通常会推进一回合
- `status` 可以随时查看完整战局
- 对局会自动记录到 `python-poc/matches/`

## 对局记录

每局结束后会生成一份 JSON 复盘文件，里面包含：

- 初始状态
- 每条命令
- 每条命令的结果
- 最终状态
- 简单 stats
