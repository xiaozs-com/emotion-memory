#!/usr/bin/env python3
"""
emotion_schedule.py — 情感探测定时任务管理

用法：
  python emotion_schedule.py setup    # 设置每周定时探测
  python emotion_schedule.py check    # 检查探测状态
  python emotion_schedule.py next      # 查看下次探测时间
"""

import os, sys, json
from datetime import datetime, timedelta

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
STATE_FILE = os.path.join(WORKSPACE, "memory", "emotion", "probe_state.json")
SCALES_DIR = os.path.join(WORKSPACE, "memory", "emotion", "scales")
os.makedirs(SCALES_DIR, exist_ok=True)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "enabled": False,
        "frequency": "weekly",
        "day_of_week": 6,  # 周日
        "hour": 9,
        "minute": 0,
        "last_probe": None,
        "next_probe": None,
        "pending_probe": None,
    }


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_next_probe_time(state):
    """计算下次探测时间"""
    now = datetime.now()
    target_wday = state["day_of_week"]  # 0=周一, 6=周日
    target_hour = state["hour"]
    target_minute = state["minute"]

    # 找到下一个目标星期几
    days_ahead = target_wday - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    next_day = now.date() + timedelta(days=days_ahead)
    next_time = datetime.combine(next_day, datetime.min.time().replace(hour=target_hour, minute=target_minute))
    return next_time


def cmd_setup(args):
    """设置定时探测"""
    state = load_state()
    state["enabled"] = True

    if args:
        if args[0] == "weekly":
            state["frequency"] = "weekly"
        elif args[0] == "daily":
            state["frequency"] = "daily"
            state["day_of_week"] = None

    next_time = get_next_probe_time(state)
    state["next_probe"] = next_time.isoformat()
    save_state(state)

    day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    freq_desc = "每天" if state["frequency"] == "daily" else f"每周{day_names[state['day_of_week']]}"
    print(f"✅ 定时探测已开启：{freq_desc} {state['hour']:02d}:{state['minute']:02d}")
    print(f"   下次探测：{next_time.strftime('%Y-%m-%d %H:%M')}")

    # 同时写入 HEARTBEAT.md 的心跳任务
    heartbeat_file = os.path.join(WORKSPACE, "HEARTBEAT.md")
    marker = "### 情感温度周报"
    marker_found = False
    if os.path.exists(heartbeat_file):
        with open(heartbeat_file, "r", encoding="utf-8") as f:
            content = f.read()
        if marker in content:
            marker_found = True

    if not marker_found:
        probe_task = f"""
### 情感温度周报（每周日 09:00）
定期发起情感温度探测，更新量表数据。

**探测流程：**
1. 调用 `emotion_probe.py mood` — 5题情绪温度
2. 调用 `emotion_probe.py results` — 检查历史记录
3. 如有新量表结果 → 调用 `emotion_probe.py update-profile` 更新画像
"""
        with open(heartbeat_file, "a", encoding="utf-8") as f:
            f.write(probe_task)
        print(f"✅ 已写入 HEARTBEAT.md 心跳任务")


def cmd_check():
    """检查探测状态"""
    state = load_state()
    print("🔍 情感探测定时状态\n")
    print(f"  状态：{'✅ 已开启' if state['enabled'] else '❌ 未开启'}")
    print(f"  频率：{state['frequency']}")
    print(f"  上次：{state['last_probe'] or '暂无记录'}")
    print(f"  下次：{state['next_probe'] or '未设置'}")

    # 检查未完成的探测
    pending = state.get("pending_probe")
    if pending:
        print(f"\n  ⏳ 待完成：{pending['type']}（{pending['date']}发起）")
    else:
        print(f"\n  ✅ 无待完成探测")

    # 列出历史量表
    print("\n📋 已完成的量表测量：")
    if os.path.exists(SCALES_DIR):
        for fname in sorted(os.listdir(SCALES_DIR)):
            if fname.endswith(".yaml"):
                print(f"  ✅ {fname.replace('.yaml', '')}")
    else:
        print("  暂无记录")


def cmd_next():
    """显示下次探测时间"""
    state = load_state()
    if not state["enabled"]:
        print("❌ 定时探测未开启，请先运行 setup")
        return
    next_time = get_next_probe_time(state)
    now = datetime.now()
    delta = next_time - now
    print(f"📅 下次探测：{next_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   距今还有：{delta.days}天 {delta.seconds//3600}小时")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "setup":
        cmd_setup(args)
    elif cmd == "check":
        cmd_check()
    elif cmd == "next":
        cmd_next()
    else:
        print(f"未知命令：{cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
