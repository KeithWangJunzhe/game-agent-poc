# Game Agent POC

端侧小模型驱动的游戏 AI Agent，用于游戏陪玩/陪练。

## 核心差异化

**不是 VLM（视觉语言模型）方案，而是基于数据接口/CLI 的结构化数据方案。**

## 项目目标

开发一个端侧小模型驱动的游戏 AI Agent，核心特点：
- 基于数据接口/CLI 的结构化数据方案
- 端侧模型快速决策 + 云端模型深度思考
- 极简 RTS 原型验证可行性

## 技术栈

- **端侧模型**: Qwen3.5-4B / Phi-4 / Llama-3.2-3B
- **游戏引擎**: Pygame (快速原型)
- **模型部署**: Ollama / llama.cpp
- **云端模型**: Claude / Qwen3-235B

## 项目结构

```
game-agent-poc/
├── docs/               # 文档
│   ├── tech_stack.md   # 技术选型报告
│   └── benchmark.md    # 模型延迟基准测试
├── src/                # 源代码
│   ├── game/           # 游戏核心
│   ├── agent/          # Agent 决策
│   └── cli/            # CLI 接口
├── tests/              # 测试
├── README.md           # 本文件
└── LICENSE             # 开源协议
```

## 快速开始

```bash
# 克隆项目
git clone https://github.com/KeithWangJunzhe/game-agent-poc.git
cd game-agent-poc

# 安装依赖
pip install -r requirements.txt

# 运行游戏
python src/main.py
```

## 贡献者

- Keith - 项目发起人
- lhc - 核心开发者

## 许可证

MIT
