# Analysis

这里放最小化的对局复盘分析工具。

原则：

- `trajectory` 继续保留 raw JSON，不在第一版做复杂解析
- 先只统计单局摘要和批量摘要
- 重点保留 agent 决策相关信息，比如 `action_counts`、`source_counts`、`fallback_count`

## 单局

```bash
conda activate ai_use
python python-poc/analysis/single_match.py /path/to/match.json
```

加 `--json` 可直接输出结构化摘要。

## 批量

```bash
conda activate ai_use
python python-poc/analysis/batch_analysis.py /path/to/matches
```

可以传单个文件、多个文件，或一个目录。加 `--json` 可输出聚合结果。

## Debug Trace

```bash
conda activate ai_use
python python-poc/analysis/debug_trace.py /path/to/match.json
```

加 `--full` 可以直接展开完整 prompt / raw output。加 `--json` 可以输出结构化 trace。
