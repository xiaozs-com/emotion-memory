# emotion-memory

> 让 AI 具备持续观察、记录和理解用户情感状态的能力。
> 从被动记录，到主动探测，最终实现情感感知型交互。

## 核心架构

```
┌─────────────────────────────────────────────┐
│  L1 被动观察                                 │
│  对话中观察 → 情感笔记                        │
│  memory/emotion/notes/YYYY-MM-DD.md          │
├─────────────────────────────────────────────┤
│  L2 主动探测                                 │
│  定期量表 → 精准量化心理状态                   │
│  memory/emotion/scales/*.yaml                │
├─────────────────────────────────────────────┤
│  L3 情感智能                                 │
│  洞察趋势 → 画像更新 → 交互策略调整            │
│  memory/emotion/profile.md / insights.md     │
└─────────────────────────────────────────────┘
```

### L1 被动观察
每次对话结束后，AI 自动记录对用户的情感观察，积累成"情感画像"。

### L2 主动探测
支持 6 个核心心理学量表，定期主动发起测量；也可对接 xinlishi 心理师平台的 151 个量表。

### L3 情感智能
基于积累的数据，感知用户情绪变化趋势，在对话中做出更懂你的回应。

## 支持的心理学量表

| 量表 | 维度 | 题数 | 用途 |
|------|------|------|------|
| ECR-R | 焦虑/回避 | 36 | 成人依恋风格 |
| BFI-16 | 五大人格 | 16 | 人格特质画像 |
| PHQ-4 | 抑郁/焦虑 | 4 | 心理健康筛查 |
| SWLS | 生活满意度 | 5 | 主观幸福感 |
| RSE | 自尊 | 10 | 自我价值感 |
| 情绪温度 | 当前情绪 | 5 | 快速情绪捕捉 |

## 安装

```bash
# 克隆到 skills 目录
git clone https://github.com/xiaozs-com/emotion-memory.git <你的skills目录>/emotion-memory

# 安装依赖
pip install pyyaml
```

## 使用

### 命令行

```bash
# 添加情感笔记
python scripts/emotion_note.py add "用户今天心情不错"

# 情绪温度探测
python scripts/emotion_probe.py mood

# 选择量表施测
python scripts/emotion_probe.py scale ecr36

# 查看历史结果
python scripts/emotion_probe.py results

# 生成洞察
python scripts/emotion_insight.py latest
```

### 对话式（推荐）

直接告诉 AI：
- "帮我做情绪温度探测"
- "我想做依恋风格测试"
- "查一下我的量表历史"

### xinlishi 心理师平台对接

在 [xinlishi.qxq.chat](https://xinlishi.qxq.chat) 完成量表后，把结果发给 AI，自动解析存储。支持 151 个量表的映射解析。

## 文件结构

```
emotion-memory/
├── SKILL.md                      # 技能说明
├── PROBES.md                    # 主动探测机制说明
├── README.md                    # 本文件
└── scripts/
    ├── emotion_note.py          # 被动记录工具
    ├── emotion_probe.py         # 主动探测工具
    ├── emotion_schedule.py      # 定时任务管理
    ├── emotion_insight.py       # 洞察生成器
    └── xinlishi_parser.py       # 心理师平台对接

# 运行时数据（在 workspace 的 memory/emotion/ 下）
memory/emotion/
├── profile.md                   # 用户情感画像
├── insights.md                  # 阶段性洞察
├── notes/                       # 每日情感笔记
│   └── YYYY-MM-DD.md
└── scales/                      # 量表数据（YAML）
    ├── ecr36.yaml
    ├── phq4.yaml
    └── ...
```

## 多 Agent 支持

当 skill 放在共享目录时，通过环境变量指定数据写入哪个 agent 的 workspace：

```bash
# 方式一：环境变量（推荐，适用于共享 skill 目录）
EMOTION_WORKSPACE=~/.qclaw/workspace-agent-xxx python scripts/emotion_note.py add "内容"

# 方式二：skill 放在 agent workspace 内（自动检测路径）
# 无需设置环境变量
```

路径检测优先级：`EMOTION_WORKSPACE` 环境变量 → 脚本路径推断 → 当前工作目录

## 隐私说明

- ✅ 所有数据仅存储在本地 `memory/emotion/` 目录
- ✅ 不上传任何外部服务
- ✅ 用户可随时查看、修改、删除个人数据

## 系统要求

- Python 3.8+
- pyyaml

## License

MIT

## Links

- 作者：[小助手网](https://xiaozs.com)
- 心理师平台：[xinlishi.qxq.chat](https://xinlishi.qxq.chat)