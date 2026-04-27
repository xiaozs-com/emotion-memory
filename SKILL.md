---
name: emotion-memory
version: 2.0.0
description: 情感记忆技能 - 让 AI 具备持续观察、记录和理解用户情感状态的能力。从被动观察升级到主动探测，基于心理学量表实现情感感知型交互。
tags: [情感, 记忆, 心理量表, 依恋, 人格, AI陪伴]
author: QClaw
homepage: https://xiaozs.com
created: 2026-04-15
updated: 2026-04-17

---

# emotion-memory 情感记忆技能

> 让 AI 具备持续观察、记录和理解用户情感状态的能力。
> 从被动记录，到主动探测，最终实现情感感知型交互。

## 技能简介

**emotion-memory** 是一个让 AI Agent 具备"情感记忆"能力的技能系统。它的核心价值是：

- 🧠 **记住用户** — 不是记住所有事情，而是记住用户是一个什么样的人
- 💬 **情感理解** — 在对话中感知用户的情绪状态变化
- 📊 **量化测量** — 基于心理学量表精准评估心理状态
- 🔄 **持续进化** — 越用越懂你，越对话越默契

## 核心能力三层架构

```
┌─────────────────────────────────────────────┐
│  L1 被动观察                                 │
│  对话中观察 → 情感笔记                        │
│  文件：memory/emotion/notes/YYYY-MM-DD.md    │
├─────────────────────────────────────────────┤
│  L2 主动探测                                 │
│  定期量表 → 精准量化心理状态                   │
│  文件：memory/emotion/scales/*.yaml          │
│  平台：xinlishi.qxq.chat                     │
├─────────────────────────────────────────────┤
│  L3 情感智能                                 │
│  洞察趋势 → 画像更新 → 交互策略调整            │
│  文件：memory/emotion/profile.md / insights.md│
└─────────────────────────────────────────────┘
```

### L1 被动观察
每次对话结束后，AI 会自动记录对用户的情感观察。这些观察会积累成"情感画像"。

### L2 主动探测
支持6个核心心理学量表（也可对接xinlishi平台的151个量表），定期主动发起测量。

### L3 情感智能
基于积累的数据，AI 能感知用户的情绪变化趋势，并在对话中做出更懂你的回应。

## 心理学量表支持

| 量表 | 维度 | 题数 | 用途 |
|------|------|------|---------|
| **ECR-R** | 焦虑/回避 | 36 | 成人依恋风格（核心） |
| **BFI-16** | 五大人格 | 16 | 人格特质画像 |
| **PHQ-4** | 抑郁/焦虑 | 4 | 心理健康筛查 |
| **SWLS** | 生活满意度 | 5 | 主观幸福感 |
| **RSE** | 自尊 | 10 | 自我价值感 |
| **情绪温度** | 当前情绪 | 5 | 快速情绪捕捉 |

## 使用场景

### 1. 被动记录（自动）
- 每次主会话结束，AI 自动记录情感观察
- 在 AGENTS.md 中强制执行

### 2. 主动探测（需要时）
```bash
# 情绪温度探测
python emotion_probe.py mood

# 选择量表施测
python emotion_probe.py scale ecr36

# 查看历史结果
python emotion_probe.py results
```

### 3. 对话式交互（推荐）
直接告诉 AI：
- "帮我做情绪温度探测"
- "我想做依恋风格测试"
- "查一下我的量表历史"

### 4. xinlishi 平台对接
在 xinlishi.qxq.chat 完成量表后，把结果发给我，自动解析存储。

## 典型工作流

```
1. 用户对话 ��� AI 观察 → 记录情感笔记
2. 定期/需要时 → 发起量表探测 → 用户回答
3. 存储结果 → 生成洞察 → 更新画像
4. 下次对话 → AI 基于画像调整回应策略
```

## 文件结构

```
skills/emotion-memory/
├── SKILL.md                      # 本文档
├── PROBES.md                    # 主动探测机制说明
└── scripts/
    ├── emotion_note.py         # 被动记录工具
    ├── emotion_probe.py        # 主动探测工具
    ├── emotion_schedule.py   # 定时任务管理
    ├── emotion_insight.py    # 洞察生成器
    └── xinlishi_parser.py    # xinlishi平台对接

memory/emotion/
├── profile.md                  # 用户情感画像
├── insights.md                 # 阶段性洞察
├── notes/                      # 每日情感笔记
│   └── YYYY-MM-DD.md
└── scales/                    # 量表数据（YAML）
    ├── ecr36.yaml
    ├── bfi16.yaml
    ├── phq4.yaml
    └── ...
```

## 隐私说明

- ✅ 所有数据仅存储在本地 `memory/emotion/` 目录
- ✅ 不上传任何外部服务
- ✅ 用户可随时查看、修改、删除个人数据
- ✅ 量表数据为个人心理状态信息，请妥善保管

## 安装方式

### 方式一：文件复制
```bash
# 复制 skill 到 skills 目录
cp -r emotion-memory/ skills/

# 复制空的 memory 目录（可选）
cp -r memory/emotion/ memory/
```

### 方式二：GitHub
```bash
git clone https://github.com/xiaozs-com/emotion-memory-skill.git
```

## 依赖

- Python 3.8+
- pyyaml

```bash
pip install pyyaml
```

## 多 Agent 共享说明

当 skill 放在共享目录（如 `~/.agents/skills/`）时，脚本需要知道数据写入哪个 agent 的 workspace。

**方式一：环境变量（推荐，适用于共享 skill 目录）**
```bash
# Agent 调用时设置 EMOTION_WORKSPACE 指向自己的 workspace 根目录
EMOTION_WORKSPACE=~/.qclaw/workspace-agent-xxx python scripts/emotion_note.py add "内容"
```

**方式二：skill 放在 agent workspace 内（自动检测）**
```bash
# 如果 skill 在 workspace/skills/ 下，脚本自动从路径推断 workspace 根目录
# 无需设置环境变量
workspace-agent-xxx/skills/emotion-memory/scripts/emotion_note.py add "内容"
```

**路径检测优先级：**
1. `EMOTION_WORKSPACE` 环境变量 → 直接使用
2. 脚本路径中 parent 目录名为 `skills` → 上推两级到 workspace 根
3. 以上都不匹配 → 回退到当前工作目录（cwd）

分享给其他 Agent：
1. 打包 `skills/emotion-memory/` 目录
2. 打包 `memory/emotion/` 目录（包含数据）
3. 把两个目录复制到目标 Agent 的工作区
4. 或者放到共享 skill 目录，调用时设 `EMOTION_WORKSPACE`

---

**核心设计理念**：情感陪伴不是做一堆复杂的功能，而是让 AI 在每一次对话中"记住你"。积累足够多的观察后，AI 自然会变成最懂你的伙伴。

---

_让 AI 更懂你，从记住你的情感开始。_