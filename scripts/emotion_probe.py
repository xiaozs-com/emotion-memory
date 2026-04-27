#!/usr/bin/env python3
"""
emotion_probe.py — 主动情感探测工具

支持三种探测模式：
  python emotion_probe.py mood      # 情绪温度（5题，快速）
  python emotion_probe.py scale     # 选择量表施测
  python emotion_probe.py quick     # 快速情绪（1题）
  python emotion_probe.py results   # 查看历史探测结果
"""

import os, sys, json
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
# 优先环境变量，回退动态检测
_env_ws = os.environ.get('EMOTION_WORKSPACE')
if _env_ws:
    WORKSPACE = _env_ws
else:
    _PARENT = os.path.dirname(SKILL_DIR)  # skills/ or emotion-memory/'s parent
    _PARENT_NAME = os.path.basename(_PARENT)
    if _PARENT_NAME == 'skills':
        WORKSPACE = os.path.dirname(_PARENT)  # workspace root
    else:
        WORKSPACE = os.getcwd()  # 共享目录回退到 cwd
SCALES_DIR = os.path.join(WORKSPACE, "memory", "emotion", "scales")
os.makedirs(SCALES_DIR, exist_ok=True)

SCALES = {
    "ecr36": {
        "name": "ECR-R 亲密关系量表",
        "name_en": "ECR-R",
        "dimensions": ["anxiety", "avoidance"],
        "questions": [
            "我觉得自己很容易亲近别人（反向）",
            "我担心自己会被抛弃",
            "我常常担心与伴侣的关系会出问题",
            "我觉得向伴侣敞开心扉很安全（反向）",
            "我经常担心伴侣不是真的爱我",
            "我觉得很难完全信任伴侣",
            "我担心伴侣会离开我",
            "我觉得和伴侣很亲近（反向）",
            "我觉得在伴侣面前表达情绪很自在（反向）",
            "我常常希望伴侣更亲近一些",
        ],
        "tip": "ECR-R 完整版共36题，这里展示核心10题示意。完整版请在 xinlishi.qxq.chat 完成施测后发送结果。",
        "score_ranges": {
            "anxiety": {"low": (1, 33), "medium": (34, 54), "high": (55, 84)},
            "avoidance": {"low": (1, 33), "medium": (34, 54), "high": (55, 84)},
        },
        "interpretation": {
            "anxiety": {
                "low": "低焦虑型：不容易担心被抛弃，情绪稳定",
                "medium": "中等焦虑型：偶尔会担心关系安全",
                "high": "高焦虑型：经常担心被抛弃，对关系敏感",
            },
            "avoidance": {
                "low": "低回避型：容易亲近，情感表达自在",
                "medium": "中等回避型：有时会保持距离",
                "high": "高回避型：倾向保持情感距离",
            },
        },
    },
    "bfi16": {
        "name": "BFI-16 大五人格简版",
        "name_en": "Big Five Inventory",
        "dimensions": ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"],
        "questions": [
            "我是一个富有想象力的思考者",
            "我是一个可靠的工作者",
            "我是一个开朗、精力充沛的人",
            "我是一个能原谅他人的人",
            "我倾向于比较放松，能够应对压力（反向）",
            "我倾向于比较沉默，对很多事情不感兴趣",
            "我对艺术和美有浓厚的兴趣",
            "我有一套清晰的原则，并坚持遵循",
            "我是一个积极活跃的人",
            "我很有同情心，能理解他人感受",
        ],
        "tip": "BFI-16 完整版共16题，这里展示核心10题。",
        "score_ranges": {
            "openness": {"low": (1, 24), "medium": (25, 34), "high": (35, 48)},
            "conscientiousness": {"low": (1, 24), "medium": (25, 34), "high": (35, 48)},
            "extraversion": {"low": (1, 24), "medium": (25, 34), "high": (35, 48)},
            "agreeableness": {"low": (1, 24), "medium": (25, 34), "high": (35, 48)},
            "neuroticism": {"low": (1, 24), "medium": (25, 34), "high": (35, 48)},
        },
        "interpretation": {
            "openness": {
                "low": "务实型：偏好熟悉和具体的事物",
                "medium": "中等开放：愿意接受新事物但保持理性",
                "high": "高开放型：富有好奇心，创造力强",
            },
            "conscientiousness": {
                "low": "灵活型：不拘泥于规则，做事随性",
                "medium": "中等尽责：有计划但有时也会灵活",
                "high": "高尽责型：有条理、高度自律",
            },
            "extraversion": {
                "low": "内倾型：偏好独处，从内心世界获得能量",
                "medium": "平衡型：内外向平衡",
                "high": "外倾型：社交能量充沛，喜欢与人互动",
            },
            "agreeableness": {
                "low": "挑战型：注重竞争和效率",
                "medium": "合作型：有合作精神但也保持独立",
                "high": "高宜人型：信任他人，乐于合作",
            },
            "neuroticism": {
                "low": "情绪稳定型：抗压能力强，情绪平稳",
                "medium": "中等情绪：偶有波动但可控",
                "high": "高神经质：情绪敏感，容易焦虑",
            },
        },
    },
    "phq4": {
        "name": "PHQ-4 心理症状筛查",
        "name_en": "Patient Health Questionnaire",
        "dimensions": ["depression", "anxiety"],
        "questions": [
            "做事时提不起劲或没有兴趣",
            "感到心情低落、沮丧或绝望",
            "感觉紧张、焦虑或被困扰",
            "感到害怕，似乎有什么可怕的事会发生",
        ],
        "tip": "PHQ-4 是筛查量表，不能替代专业诊断。",
        "scoring": "每个问题0-3分（完全没有=0，几乎每天=3）。总分≥6需关注。",
        "score_ranges": {
            "total": {"normal": (0, 5), "mild": (6, 8), "moderate": (9, 12)},
        },
        "interpretation": {
            "total": {
                "normal": "心理状态良好，无明显抑郁焦虑症状",
                "mild": "轻度心理困扰，建议关注自我状态",
                "moderate": "中等程度困扰，建议考虑专业咨询",
            },
        },
    },
    "swls": {
        "name": "SWLS 生活满意度量表",
        "name_en": "Satisfaction with Life Scale",
        "dimensions": ["life_satisfaction"],
        "questions": [
            "我的生活在大多数方面接近我的理想",
            "我的生活状况很好",
            "我对我的生活感到满意",
            "到目前为止，我已经得到了生活中想要的重要东西",
            "如果我能重新活一次，我几乎不会做任何改变",
        ],
        "tip": "5题均按1-7分评估（强烈反对=1，强烈同意=7），总分5-35。",
        "score_ranges": {
            "total": {"low": (5, 14), "medium": (15, 24), "high": (25, 35)},
        },
        "interpretation": {
            "total": {
                "low": "低生活满意度：可能对当前生活状态不满意",
                "medium": "中等满意度：生活状态一般，有满意也有遗憾",
                "high": "高满意度：对自己的生活感到满意和满足",
            },
        },
    },
    "rse": {
        "name": "RSE 自尊量表",
        "name_en": "Rosenberg Self-Esteem Scale",
        "dimensions": ["self_esteem"],
        "questions": [
            "总体来说，我对自己满意",
            "有时我觉得自己一无是处",
            "我觉得自己有许多优点",
            "我能像大多数人一样把事情做好",
            "有时我怀疑自己做不到事情",
            "我对自己持肯定态度",
            "我整体上对自己的看法消极（反向）",
            "我希望我能更尊重自己（反向）",
            "我确实觉得自己毫无价值",
            "我对自己评价积极（反向）",
        ],
        "tip": "RSE 完整版共10题，这里展示10题。正向和反向计分需按题目编号处理。",
        "score_ranges": {
            "total": {"low": (10, 20), "medium": (21, 29), "high": (30, 40)},
        },
        "interpretation": {
            "total": {
                "low": "低自尊：自我价值感较低，可能需要更多支持",
                "medium": "中等自尊：自我评价稳定但偶有波动",
                "high": "高自尊：自我价值感强，对自己有信心",
            },
        },
    },
}


def get_level(score, ranges):
    """根据分数返回等级标签"""
    for label, (lo, hi) in ranges.items():
        if lo <= score <= hi:
            return label
    return "unknown"


def interpret_scale(scale_id, scores):
    """解释量表得分，返回分析文本"""
    scale = SCALES.get(scale_id)
    if not scale:
        return "未知量表"

    lines = []
    lines.append(f"\n📊 {scale['name']} ({scale['name_en']})")
    lines.append(f"施测时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    if "total" in scores:
        score = scores["total"]
        ranges = scale.get("score_ranges", {}).get("total", {})
        level = get_level(score, ranges)
        interp = scale["interpretation"]["total"].get(level, "")
        lines.append(f"  总分：{score}/{(list(ranges.values())[-1][1]) if ranges else '?'}")
        lines.append(f"  解读：{interp}")
    else:
        for dim, score in scores.items():
            ranges = scale.get("score_ranges", {}).get(dim, {})
            level = get_level(score, ranges)
            interp = scale["interpretation"].get(dim, {}).get(level, "")
            if interp:
                lines.append(f"  {dim}：{score} — {interp}")

    return "\n".join(lines)


def save_result(scale_id, scores, interpretation):
    """保存结果到 YAML 文件"""
    import yaml

    scale_file = os.path.join(SCALES_DIR, f"{scale_id}.yaml")
    data = {}
    if os.path.exists(scale_file):
        with open(scale_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

    if "history" not in data:
        data["history"] = []

    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "scores": scores,
        "interpretation": interpretation,
    }
    data["history"].append(entry)
    data["latest"] = entry
    data["meta"] = {
        "name": SCALES[scale_id]["name"],
        "dimensions": SCALES[scale_id]["dimensions"],
        "updated": datetime.now().isoformat(),
    }

    with open(scale_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    return scale_file


def cmd_mood():
    """情绪温度探测（5题快速）"""
    print("🌡️  情绪温度探测\n")
    print("请回答以下5个问题（1-10分，1=很差，10=很好）：\n")

    questions = [
        "1. 这周整体心情怎么样？",
        "2. 和AI的对话让你感到被理解吗？",
        "3. 这周最有成就感的一件事是什么？",
        "4. 这周最让你焦虑或烦恼的是什么？",
        "5. 你对下周有什么期待？",
    ]

    answers = []
    for q in questions:
        print(q)
        ans = input("  你的回答：").strip()
        answers.append({"question": q, "answer": ans})
        print()

    print("\n📋 回答汇总：")
    for a in answers:
        print(f"  {a['question']}")
        print(f"  → {a['answer']}\n")

    confirm = input("保存这份情绪记录？(y/n)：").strip().lower()
    if confirm == "y":
        import yaml

        mood_file = os.path.join(SCALES_DIR, "mood_diary.yaml")
        data = {}
        if os.path.exists(mood_file):
            with open(mood_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        if "entries" not in data:
            data["entries"] = []

        data["entries"].append(
            {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "answers": answers,
                "summary": f"情绪温度记录 {len(data['entries'])+1} 条",
            }
        )

        with open(mood_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

        print(f"✅ 已保存到 {mood_file}")


def cmd_scale(args):
    """量表施测或结果录入"""
    if not args:
        # 列出所有量表
        print("📋 可用量表：\n")
        for sid, s in SCALES.items():
            print(f"  {sid:12s} {s['name']}")
            print(f"  {'':12s}  维度：{', '.join(s['dimensions'])}")
            print()
        return

    scale_id = args[0]
    if scale_id not in SCALES:
        print(f"未知量表：{scale_id}，可用：{', '.join(SCALES.keys())}")
        return

    scale = SCALES[scale_id]
    print(f"\n📊 {scale['name']}（{scale['name_en']}）\n")
    print(f"测量维度：{', '.join(scale['dimensions'])}\n")

    # 如果用户传入了分数，直接解析
    if len(args) > 1:
        # 假设第二个参数开始是分数
        # 支持两种格式：
        # 1. 纯数字总分: ecr36 38 22  (焦虑分 回避分)
        # 2. JSON: ecr36 '{"anxiety":38,"avoidance":22}'
        if len(args) > 1 and args[1].startswith("{"):
            scores = json.loads(args[1])
        else:
            scores = {}
            for i, dim in enumerate(scale["dimensions"]):
                if i + 1 < len(args):
                    try:
                        scores[dim] = int(args[i + 1])
                    except ValueError:
                        pass

        if scores:
            interpretation = interpret_scale(scale_id, scores)
            print(interpretation)
            save_result(scale_id, scores, interpretation)
            print(f"\n✅ 已保存到 {SCALES_DIR}/{scale_id}.yaml")
            return

    # 交互式施测
    print("请在 xinlishi.qxq.chat 完成施测后，将结果发送给我。")
    print(f"\ntip: {scale['tip']}\n")
    print("量表题目（参考）：")
    for i, q in enumerate(scale["questions"], 1):
        print(f"  {i}. {q}")

    print("\n\n完成后请将结果以以下格式发给我：")
    print(f"  ecr36 38 22  （{scale['dimensions'][0]}分 {scale['dimensions'][1]}分）")
    print(f"  或：ecr36 {{'anxiety':38,'avoidance':22}}")


def cmd_quick():
    """快速情绪探测（1题）"""
    print("🌡️  快速情绪探测\n")
    print("此刻你的心情如何？（1-10分）")
    ans = input("  分数：").strip()
    print("\n谢谢！你的回答是：", ans)
    print("(快速记录功能将在完整版中实现)")


def cmd_results():
    """查看历史结果"""
    import yaml

    print("📋 情感测量历史记录\n")
    files = sorted(os.listdir(SCALES_DIR))
    if not files:
        print("暂无记录。请先进行量表探测。")
        return

    for fname in files:
        fpath = os.path.join(SCALES_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        name = data.get("meta", {}).get("name", fname)
        latest = data.get("latest", {})
        date = latest.get("date", "未知")
        scores = latest.get("scores", {})
        print(f"  {fname.replace('.yaml',''):12s}  {name}")
        print(f"  {'':12s}  最新：{date}  得分：{scores}\n")


def cmd_update_profile():
    """根据最新量表结果更新 profile.md"""
    import yaml

    profile_path = os.path.join(WORKSPACE, "memory", "emotion", "profile.md")
    os.makedirs(os.path.dirname(profile_path), exist_ok=True)

    updates = []
    for fname in os.listdir(SCALES_DIR):
        if not fname.endswith(".yaml") or fname == "mood_diary.yaml":
            continue
        fpath = os.path.join(SCALES_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        latest = data.get("latest", {})
        if not latest:
            continue
        scale_name = data.get("meta", {}).get("name", fname)
        date = latest.get("date", "")
        scores = latest.get("scores", {})
        interpretation = latest.get("interpretation", "")
        updates.append(
            f"- **{scale_name}**（{date}）：{scores}\n  {interpretation}"
        )

    if not updates:
        print("没有可用的量表结果")
        return

    note = "\n### 量表测量结果\n" + "\n".join(updates)

    # 追加到 profile.md
    with open(profile_path, "a", encoding="utf-8") as f:
        f.write(note)

    print(f"✅ 已更新 {profile_path}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "mood":
        cmd_mood()
    elif cmd == "scale":
        cmd_scale(args)
    elif cmd == "quick":
        cmd_quick()
    elif cmd == "results":
        cmd_results()
    elif cmd == "update-profile":
        cmd_update_profile()
    else:
        print(f"未知命令：{cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
