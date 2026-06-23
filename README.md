# Game Agent POC

这是 `codex` 工区里的子项目，目标是做一个先跑通游戏部分的 POC。

核心方向很明确：

- 端侧小模型驱动的游戏 AI Agent
- 走结构化数据 / CLI 路线，不先碰 VLM
- 先做极简 RTS 原型，再决定后续扩展

## 当前状态

- 项目骨架已就位，第一版 POC 已开始落地
- `src/main.py` 负责跳转到 POC runner
- `python-poc/` 里已经放了核心游戏骨架

## 贡献者

- `KeithWangJunzhe`
- `lhc`

## 目录索引

```text
game-agent-poc/
├── README.md              # 项目入口与索引
├── CONTRIBUTING.md        # 协作约定
├── docs/
│   └── tech_stack.md      # 当前技术选型记录
├── python-poc/            # 预留：Python 游戏 POC 实现
│   ├── README.md
│   ├── game_poc.py        # 游戏状态 / 规则 / 引擎
│   └── runner.py          # demo / 交互入口
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

从任何目录都可以直接跑绝对路径：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/run_poc.py --interactive --max-turns 30
```

如果你已经在项目目录里，也可以这样：

```bash
cd /Users/keith/Desktop/AI/codex/game-agent-poc
conda activate ai_use
python src/main.py
```

也可以直接跑 POC 入口：

```bash
cd /Users/keith/Desktop/AI/codex/game-agent-poc
conda activate ai_use
python python-poc/runner.py
```

如果要让本地 Ollama 和 baseline 对打一局：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/python-poc/ollama_match.py --model gemma4:e2b --max-turns 30
```

如果要看带诊断信息的 debug 版本：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/python-poc/ollama_match.py --model gemma4:e2b --max-turns 30 --debug
```

如果只想跑纯 baseline：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/python-poc/baseline_bot.py --demo
```

如果要试最小自然语言 harness：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/python-poc/harness.py
```

如果想手动输入回复：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/python-poc/harness.py --agent interactive --max-turns 30
```

如果想看 harness 的 debug 诊断：

```bash
conda activate ai_use
python /Users/keith/Desktop/AI/codex/game-agent-poc/python-poc/harness.py --agent ollama --model gemma4:e2b --max-turns 30 --debug
```

## 测试

```bash
conda activate ai_use
python -m unittest discover -s tests
```

## 参考背景

这些是前面已经整理好的上游讨论和决策来源，后面写 POC 时不用重复造轮子：

- [可行性分析](/Users/keith/Desktop/AI/CoPaw/workspaces/default/memory/raw/2026-05-27_game_agent_feasibility_report.md)
- [Roadmap](/Users/keith/Desktop/AI/CoPaw/workspaces/default/memory/raw/2026-05-27_game_agent_roadmap.md)
- [Sprint 0 调整版](/Users/keith/Desktop/AI/CoPaw/workspaces/default/memory/raw/2026-06-02_sprint0_adjusted.md)
- [周报摘要](/Users/keith/Desktop/AI/CoPaw/workspaces/default/memory/curated/weekly_report_2026-06-02_2026-06-06.md)
- [Phase 1 Plan](/Users/keith/Desktop/AI/codex/game-agent-poc/docs/phase1_plan.md)
- [How To Play](/Users/keith/Desktop/AI/codex/game-agent-poc/python-poc/HOW_TO_PLAY.md)
- [Agent Playbook](/Users/keith/Desktop/AI/codex/game-agent-poc/python-poc/AGENT_PLAYBOOK.md)

## 下一步

接下来进入阶段一：先把胜利条件、资源博弈、随机先后手和最小 harness 定住，再继续迭代实现。
