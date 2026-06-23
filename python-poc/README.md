# Python POC

这里专门预留给游戏部分 Python POC 实现。当前这一版已经完成阶段一目标，后续以维护和复用为主。

当前第一版已经落地并可复现：

- `game_poc.py`：游戏状态、单位、资源、引擎
- `runner.py`：demo 和交互式命令入口
- `harness.py`：最小自然语言 harness 骨架
- `baseline_bot.py`：当前最弱可复用 baseline
- `analysis/`：单局和批量复盘摘要
- `analysis/debug_trace.py`：按 turn 展示 prompt / output / decision note
- [How To Play](./HOW_TO_PLAY.md)：给人看的对局说明
- [Agent Playbook](./AGENT_PLAYBOOK.md)：给 agent 看的规则摘要
- `matches/`：自动生成的对局复盘 JSON

## 约定

- 环境使用 `conda env ai_use`
- 先写最小可运行版本，再逐步加能力
- 这里只放 POC 代码，不把端侧模型相关内容先推进进来
- 推荐从仓库根目录入口 [`run_poc.py`](../run_poc.py) 启动，这样不依赖当前工作目录
- 测试自然语言 harness 时优先用 [`harness.py`](./harness.py)，默认会调用本地 `ollama run gemma4:e2b`
- 最小复盘摘要可以直接用 [`analysis/single_match.py`](./analysis/single_match.py) 和 [`analysis/batch_analysis.py`](./analysis/batch_analysis.py)
- `run_poc.py --interactive --max-turns 30` 会把手动对局限制到 30 turns
- `harness.py --agent ollama --max-turns 30 --debug` 会带上 Ollama 诊断信息
- `ollama_match.py --model gemma4:e2b --max-turns 30 --debug` 是 e2b vs baseline 的诊断版本
- 需要公开复现说明时请看 [docs/reproducibility.md](../docs/reproducibility.md)

## 计划放置的内容

- 游戏状态模型
- 命令循环
- 最小 RTS / 回合循环
- 状态序列化与 CLI 输入输出
- 对局记录和 after-match stats
