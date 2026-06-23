# Game Agent POC

这是一个面向游戏 agent 的 Python POC。当前这一版已经完成阶段一目标，作为公开原型保留，后续主要用于方法复用和回看。

核心方向很明确：

- 端侧小模型驱动的游戏 AI Agent
- 走结构化数据 / CLI 路线，不先碰 VLM
- 先做极简 RTS 原型，再决定后续扩展

## 当前状态

- 项目骨架已就位，阶段一 POC 已完成
- `src/main.py` 负责跳转到 POC runner
- `python-poc/` 里已经放了核心游戏骨架、对局 harness 和最小分析工具

## 贡献者

- `KeithWangJunzhe`
- `lhc`

## 目录索引

```text
game-agent-poc/
├── README.md              # 项目入口与索引
├── CONTRIBUTING.md        # 协作约定
├── docs/
│   ├── phase1_plan.md     # 阶段一计划
│   └── tech_stack.md      # 当前技术选型记录
├── python-poc/            # 预留：Python 游戏 POC 实现
│   ├── README.md
│   ├── game_poc.py        # 游戏状态 / 规则 / 引擎
│   ├── runner.py          # demo / 交互入口
│   ├── harness.py         # 自然语言 harness
│   ├── ollama_match.py    # e2b vs baseline
│   └── analysis/          # 单局和批量复盘
├── src/
│   └── main.py            # 启动占位
├── tests/
│   ├── test_smoke.py      # 最小 smoke test
│   └── test_game_poc.py   # 核心规则测试
```

## 推荐环境

- Conda 环境：`ai_use`
- Python：`3.11+`
- 当前只需要标准库，后续再按 POC 需要补游戏库和模型库

## 启动方式

从任何目录都可以直接跑仓库根入口：

```bash
conda activate ai_use
python run_poc.py --interactive --max-turns 30
```

如果你已经在项目目录里，也可以这样：

```bash
cd /path/to/game-agent-poc
conda activate ai_use
python src/main.py
```

也可以直接跑 POC 入口：

```bash
cd /path/to/game-agent-poc
conda activate ai_use
python python-poc/runner.py
```

如果要让本地 Ollama 和 baseline 对打一局：

```bash
conda activate ai_use
python python-poc/ollama_match.py --model gemma4:e2b --max-turns 30
```

如果要看带诊断信息的 debug 版本：

```bash
conda activate ai_use
python python-poc/ollama_match.py --model gemma4:e2b --max-turns 30 --debug
```

如果只想跑纯 baseline：

```bash
conda activate ai_use
python python-poc/baseline_bot.py --demo
```

如果要试最小自然语言 harness：

```bash
conda activate ai_use
python python-poc/harness.py
```

如果想手动输入回复：

```bash
conda activate ai_use
python python-poc/harness.py --agent interactive --max-turns 30
```

如果想看 harness 的 debug 诊断：

```bash
conda activate ai_use
python python-poc/harness.py --agent ollama --model gemma4:e2b --max-turns 30 --debug
```

## 测试

```bash
conda activate ai_use
python -m unittest discover -s tests
```

## 参考背景

- 阶段一计划见 [docs/phase1_plan.md](./docs/phase1_plan.md)
- 阶段一完成后的后续方案见 [docs/post_poc_plan.md](./docs/post_poc_plan.md)
- 公开仓库复现说明见 [docs/reproducibility.md](./docs/reproducibility.md)
- 对局说明见 [python-poc/HOW_TO_PLAY.md](./python-poc/HOW_TO_PLAY.md)
- Agent 规则摘要见 [python-poc/AGENT_PLAYBOOK.md](./python-poc/AGENT_PLAYBOOK.md)
- 游戏 POC 的说明和脚本索引见 [python-poc/README.md](./python-poc/README.md)

## 下一步

如果后续要继续推进更复杂的游戏 agent 项目，可以把这里当成方法验证原型和回退点。
