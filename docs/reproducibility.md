# Reproducibility

这份说明面向外部复现者，目标是让别人 clone 下来后能尽量少猜。

## 需要的东西

- Git
- Conda
- Python `3.11+`

## 获取代码

```bash
git clone https://github.com/KeithWangJunzhe/game-agent-poc.git
cd game-agent-poc
```

## 环境

项目默认使用 `conda env ai_use`。

如果你本机已经有这个环境：

```bash
conda activate ai_use
```

如果没有，可以新建一个同名环境，再安装你习惯的 Python 版本。

## 运行

```bash
python run_poc.py --interactive --max-turns 30
```

或者运行示例对局：

```bash
python python-poc/ollama_match.py --model gemma4:e2b --max-turns 30 --debug
```

## 测试

```bash
python -m unittest discover -s tests
```

## 说明

- 这个 POC 当前不依赖第三方 Python 包，主要用标准库
- `ollama` 只用于可选的本地模型对局
- 如果本机没有 `ollama`，仍然可以跑 baseline 和交互模式
- 报告和 debug trace 都会写到 `python-poc/matches/`

