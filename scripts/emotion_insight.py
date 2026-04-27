#!/usr/bin/env python3
"""
emotion_insight.py — 情感洞察生成器

读取量表历史数据，自动分析趋势变化，生成洞察记录。

用法：
  python emotion_insight.py latest      # 基于最新数据生成洞察
  python emotion_insight.py trend       # 分析趋势变化
  python emotion_insight.py full        # 完整分析
  python emotion_insight.py profile      # 生成/更新 profile.md
"""

import os, sys, yaml
from datetime import datetime, timedelta
from collections import defaultdict

# 优先环境变量，回退动态检测
_env_ws = os.environ.get('EMOTION_WORKSPACE')
if _env_ws:
    WORKSPACE = _env_ws
else:
    _SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scripts/ → emotion-memory/
    _PARENT = os.path.dirname(_SKILL_DIR)  # skills/ or emotion-memory/'s parent
    _PARENT_NAME = os.path.basename(_PARENT)
    if _PARENT_NAME == 'skills':
        WORKSPACE = os.path.dirname(_PARENT)  # workspace root
    else:
        WORKSPACE = os.getcwd()  # 共享目录回退到 cwd
SCALES_DIR = os.path.join(WORKSPACE, "memory", "emotion", "scales")
INSIGHTS_FILE = os.path.join(WORKSPACE, "memory", "emotion", "insights.md")
PROFILE_FILE = os.path.join(WORKSPACE, "memory", "emotion", "profile.md")
os.makedirs(os.path.dirname(INSIGHTS_FILE), exist_ok=True)


# ─── 量表元数据 ────────────────────────────────────────────────
SCALE_META = {
    "ecr36": {
        "name": "ECR-R 亲密关系量表",
        "dims": ["anxiety", "avoidance"],
        "high_is": {"anxiety": "bad", "avoidance": "bad"},
        "labels": {
            "anxiety": {
                "low": "低焦虑",
                "medium": "中等焦虑",
                "high": "高焦虑",
            },
            "avoidance": {
                "low": "低回避",
                "medium": "中等回避",
                "high": "高回避",
            },
        },
        "interpretation": {
            ("low", "low"): "安全型依恋：既能亲密又能保持独立，关系模式健康",
            ("low", "high"): "回避型依恋：倾向保持情感距离，较少依赖他人",
            ("high", "low"): "焦虑型依恋：对关系缺乏安全感，容易患得患失",
            ("high", "high"): "混乱型依恋：既焦虑又回避，关系中容易矛盾纠结",
            ("medium", "low"): "偏向安全型依恋",
            ("low", "medium"): "偏向安全型依恋",
            ("medium", "medium"): "中等依恋类型，关系模式有一定弹性",
            ("medium", "high"): "偏向回避型依恋",
            ("high", "medium"): "偏向焦虑型依恋",
        },
    },
    "bfi16": {
        "name": "BFI-16 大五人格",
        "dims": ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"],
        "high_is": {
            "openness": "good",
            "conscientiousness": "good",
            "extraversion": "good",
            "agreeableness": "good",
            "neuroticism": "bad",
        },
        "labels": {
            "openness": {"low": "务实", "medium": "中等开放", "high": "高开放"},
            "conscientiousness": {"low": "灵活", "medium": "中等尽责", "high": "高尽责"},
            "extraversion": {"low": "内倾", "medium": "平衡", "high": "外倾"},
            "agreeableness": {"low": "挑战型", "medium": "合作型", "high": "高宜人"},
            "neuroticism": {"low": "情绪稳定", "medium": "中等情绪", "high": "高敏感"},
        },
        "interpretation": {
            "summary_template": "{openness}/{conscientiousness}/{extraversion}/{agreeableness}/{neuroticism}",
        },
    },
    "phq4": {
        "name": "PHQ-4 心理症状筛查",
        "dims": ["total"],
        "high_is": {"total": "bad"},
        "labels": {
            "total": {"normal": "无明显症状", "mild": "轻度困扰", "moderate": "中度困扰"},
        },
    },
    "swls": {
        "name": "SWLS 生活满意度",
        "dims": ["total"],
        "high_is": {"total": "good"},
        "labels": {
            "total": {"low": "低满意度", "medium": "中等满意度", "high": "高满意度"},
        },
    },
    "rse": {
        "name": "RSE 自尊量表",
        "dims": ["total"],
        "high_is": {"total": "good"},
        "labels": {
            "total": {"low": "低自尊", "medium": "中等自尊", "high": "高自尊"},
        },
    },
}


# ─── 辅助函数 ──────────────────────────────────────────────────
def load_yaml(fname):
    path = os.path.join(SCALES_DIR, fname)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def score_level(scale_id, dim, score):
    """把分数转成等级标签（low/medium/high）"""
    meta = SCALE_META.get(scale_id, {})
    ranges = {
        "ecr36": {"low": (1, 33), "medium": (34, 54), "high": (55, 84)},
        "bfi16": {"low": (1, 24), "medium": (25, 34), "high": (35, 48)},
        "phq4": {"normal": (0, 5), "mild": (6, 8), "moderate": (9, 12)},
        "swls": {"low": (5, 14), "medium": (15, 24), "high": (25, 35)},
        "rse": {"low": (10, 20), "medium": (21, 29), "high": (30, 40)},
    }
    r = ranges.get(scale_id, {})
    for label, (lo, hi) in r.items():
        if lo <= score <= hi:
            return label
    return "unknown"


def interpret_combined(scale_id, scores):
    """综合多个维度给出整体解读"""
    meta = SCALE_META.get(scale_id)
    if not meta:
        return None

    if scale_id == "ecr36":
        anx = scores.get("anxiety", 0)
        avd = scores.get("avoidance", 0)
        anx_level = score_level(scale_id, "anxiety", anx)
        avd_level = score_level(scale_id, "avoidance", avd)
        key = (anx_level, avd_level)
        interp = meta["interpretation"].get(key, "待分析")
        return {
            "style": meta["interpretation"].get(key, "待分析"),
            "anxiety": anx,
            "avoidance": avd,
            "anxiety_label": meta["labels"]["anxiety"].get(anx_level, anx_level),
            "avoidance_label": meta["labels"]["avoidance"].get(avd_level, avd_level),
        }

    return None


def detect_trend(history, dim):
    """检测趋势：上升、下降、持平"""
    if len(history) < 2:
        return None
    recent = history[-1].get("scores", {}).get(dim)
    older = history[-2].get("scores", {}).get(dim)
    if recent is None or older is None:
        return None
    diff = recent - older
    if abs(diff) <= 3:
        return "持平"
    return "↑ 上升" if diff > 0 else "↓ 下降"


# ─── 命令 ──────────────────────────────────────────────────────
def cmd_latest():
    """基于最新量表数据生成洞察"""
    results = {}
    for fname in os.listdir(SCALES_DIR):
        if not fname.endswith(".yaml") or fname == "mood_diary.yaml":
            continue
        scale_id = fname.replace(".yaml", "")
        data = load_yaml(fname)
        latest = data.get("latest", {})
        if not latest:
            continue
        results[scale_id] = latest.get("scores", {})

    if not results:
        print("暂无量表数据，请先进行测量。")
        return results

    lines = []
    lines.append("## 最新量表洞察\n")

    for scale_id, scores in results.items():
        meta = SCALE_META.get(scale_id, {})
        name = meta.get("name", scale_id)
        lines.append(f"### {name}\n")

        if scale_id == "ecr36":
            interp = interpret_combined(scale_id, scores)
            if interp:
                lines.append(f"- 依恋风格：**{interp['style']}**")
                lines.append(f"- 焦虑维度：{interp['anxiety_label']}（{interp['anxiety']}分）")
                lines.append(f"- 回避维度：{interp['avoidance_label']}（{interp['avoidance']}分）")

        elif scale_id == "bfi16":
            lines.append(f"- 五大人格得分：")
            for dim in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
                score = scores.get(dim, 0)
                level = score_level(scale_id, dim, score)
                label = meta["labels"].get(dim, {}).get(level, level)
                lines.append(f"  - {dim}：{score}分 → {label}")

        elif scale_id in ("phq4", "swls", "rse"):
            total = scores.get("total", 0)
            level = score_level(scale_id, "total", total)
            label = meta["labels"]["total"].get(level, level)
            lines.append(f"- 得分：{total} → {label}")

        lines.append("")

    insight_text = "\n".join(lines)
    print(insight_text)
    return results


def cmd_trend():
    """分析量表趋势变化"""
    print("## 情感状态趋势分析\n")

    for fname in sorted(os.listdir(SCALES_DIR)):
        if not fname.endswith(".yaml") or fname == "mood_diary.yaml":
            continue
        scale_id = fname.replace(".yaml", "")
        data = load_yaml(fname)
        history = data.get("history", [])
        if len(history) < 2:
            continue

        meta = SCALE_META.get(scale_id, {})
        name = meta.get("name", scale_id)
        print(f"### {name}（{len(history)}次测量）\n")

        # 列出每次测量
        for i, entry in enumerate(history[-3:]):  # 最近3次
            date = entry.get("date", "?")
            scores = entry.get("scores", {})
            score_str = " / ".join(f"{k}={v}" for k, v in scores.items())
            marker = "◀ 最新" if i == len(history[-3:]) - 1 else ""
            print(f"  {date}  {score_str}  {marker}")

        # 趋势
        dims = meta.get("dims", ["total"])
        for dim in dims:
            trend = detect_trend(history, dim)
            if trend:
                latest_score = history[-1].get("scores", {}).get(dim, "?")
                print(f"  {dim} 趋势：{trend}（最新：{latest_score}）")

        print()


def cmd_profile():
    """生成/更新 profile.md"""
    results = {}
    for fname in os.listdir(SCALES_DIR):
        if not fname.endswith(".yaml") or fname == "mood_diary.yaml":
            continue
        scale_id = fname.replace(".yaml", "")
        data = load_yaml(fname)
        latest = data.get("latest", {})
        if latest:
            results[scale_id] = latest

    sections = []
    sections.append("## 量表测量结果\n")

    if "ecr36" in results:
        scores = results["ecr36"].get("scores", {})
        interp = interpret_combined("ecr36", scores)
        if interp:
            sections.append(f"- **依恋风格**：{interp['style']}")
            sections.append(f"  - 焦虑：{interp['anxiety_label']}（{interp['anxiety']}）")
            sections.append(f"  - 回避：{interp['avoidance_label']}（{interp['avoidance']}）")
            sections.append(f"  - 更新：{results['ecr36'].get('date', '')}\n")

    if "bfi16" in results:
        scores = results["bfi16"].get("scores", {})
        meta = SCALE_META["bfi16"]
        lines = ["- **五大人格**：" + " / ".join(
            f"{dim}={scores.get(dim, '?')}"
            for dim in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
        )]
        lines.append(f"  - 更新：{results['bfi16'].get('date', '')}\n")
        sections.append("\n".join(lines))

    for sid in ["phq4", "swls", "rse"]:
        if sid in results:
            scores = results[sid].get("scores", {})
            total = scores.get("total", 0)
            level = score_level(sid, "total", total)
            label = SCALE_META[sid]["labels"]["total"].get(level, level)
            meta = SCALE_META[sid]
            sections.append(f"- **{meta['name']}**：{label}（{total}分）")
            sections.append(f"  - 更新：{results[sid].get('date', '')}\n")

    text = "\n".join(sections)

    # 追加到 profile.md
    if not os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            f.write("# 用户情感画像\n\n")
            f.write("> 由 emotion_insight.py 自动生成，基于量表数据。\n")
            f.write("> 最后更新：\n\n")

    # 在文件末尾追加或更新
    with open(PROFILE_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    # 查找 ## 量表测量结果 部分
    marker = "## 量表测量结果"
    if marker in content:
        # 替换旧内容
        start = content.index(marker)
        # 找到下一个 ## 标题或文件末尾
        rest = content[start:]
        next_header = rest.index("##", 2) if rest.count("##") > 1 else -1
        if next_header > 0:
            content = content[:start] + text + "\n" + rest[next_header:]
        else:
            content = content[:start] + text
    else:
        content += "\n" + text

    # 更新最后更新时间
    content = content.replace(
        "> 最后更新：", f"> 最后更新：{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ profile.md 已更新")


def cmd_full():
    """完整分析"""
    print("═" * 40)
    print("  情感洞察完整报告")
    print("═" * 40)
    cmd_latest()
    print()
    cmd_trend()
    cmd_profile()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "latest":
        cmd_latest()
    elif cmd == "trend":
        cmd_trend()
    elif cmd == "profile":
        cmd_profile()
    elif cmd == "full":
        cmd_full()
    else:
        print(f"未知命令：{cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
