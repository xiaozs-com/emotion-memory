#!/usr/bin/env python3
"""
情感笔记管理工具

用法:
    python emotion_note.py add "笔记内容"
    python emotion_note.py view
    python emotion_note.py search "关键词"
    python emotion_note.py insight "洞察内容"
    python emotion_note.py summary
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 情感记忆根目录（优先环境变量，回退动态检测）
# 1. 优先使用 EMOTION_WORKSPACE 环境变量（适用于共享 skill 目录）
# 2. 回退到脚本位置推断（适用于 skill 在 workspace/skills/ 下的情况）
_env_ws = os.environ.get('EMOTION_WORKSPACE')
if _env_ws:
    WORKSPACE = Path(_env_ws)
else:
    _SKILL_DIR = Path(__file__).resolve().parent.parent  # scripts/ → emotion-memory/
    _PARENT = _SKILL_DIR.parent  # skills/ or emotion-memory/'s parent
    # 如果 parent 是 skills/，说明 skill 在 workspace/skills/ 下
    if _PARENT.name == 'skills':
        WORKSPACE = _PARENT.parent  # workspace root
    else:
        # 共享目录（如 ~/.agents/skills/），回退到 cwd
        WORKSPACE = Path.cwd()
EMOTION_DIR = WORKSPACE / 'memory' / 'emotion'
PROFILE_FILE = EMOTION_DIR / 'profile.md'
INSIGHTS_FILE = EMOTION_DIR / 'insights.md'
NOTES_DIR = EMOTION_DIR / 'notes'

def ensure_dirs():
    """确保目录存在"""
    PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)
    # 初始化空文件
    if not PROFILE_FILE.exists():
        PROFILE_FILE.write_text("# 用户情感画像\n\n", encoding='utf-8')
    if not INSIGHTS_FILE.exists():
        INSIGHTS_FILE.write_text("# 阶段性洞察\n\n", encoding='utf-8')

def add_note(content: str, tag: str = ""):
    """添加情感笔记"""
    ensure_dirs()
    today = datetime.now().strftime('%Y-%m-%d')
    note_file = NOTES_DIR / f'{today}.md'
    
    timestamp = datetime.now().strftime('%H:%M')
    tag_str = f" [{tag}]" if tag else ""
    
    entry = f"""## {timestamp}{tag_str}

### 观察
- {content}

### 推测
-

### 下次注意
-

---
"""
    
    # 追加到今日笔记
    with open(note_file, 'a', encoding='utf-8') as f:
        f.write(entry + '\n')
    
    print(f"✅ 情感笔记已添加（{today} {timestamp}）")
    print(f"   文件: {note_file}")

def view_profile():
    """查看用户情感画像"""
    ensure_dirs()
    print("=" * 60)
    print("用户情感画像")
    print("=" * 60)
    if PROFILE_FILE.exists():
        print(PROFILE_FILE.read_text(encoding='utf-8'))
    else:
        print("（暂无画像，从今天开始记录）")
    
    print()
    print("=" * 60)
    print("阶段性洞察")
    print("=" * 60)
    if INSIGHTS_FILE.exists():
        print(INSIGHTS_FILE.read_text(encoding='utf-8'))
    else:
        print("（暂无洞察）")

def view_notes(days: int = 7):
    """查看最近 N 天的情感笔记"""
    ensure_dirs()
    print("=" * 60)
    print(f"最近 {days} 天情感笔记")
    print("=" * 60)
    
    today = datetime.now()
    notes_found = False
    
    for i in range(days):
        date = today - timedelta(days=i)
        note_file = NOTES_DIR / f'{date.strftime("%Y-%m-%d")}.md'
        if note_file.exists():
            notes_found = True
            print(f"\n### {date.strftime('%Y-%m-%d')}")
            print("-" * 40)
            print(note_file.read_text(encoding='utf-8'))
    
    if not notes_found:
        print("（暂无笔记）")

def search_notes(keyword: str):
    """搜索笔记内容"""
    ensure_dirs()
    print("=" * 60)
    print(f"搜索: {keyword}")
    print("=" * 60)
    
    found = False
    for note_file in sorted(NOTES_DIR.glob('*.md'), reverse=True):
        content = note_file.read_text(encoding='utf-8')
        if keyword.lower() in content.lower():
            found = True
            print(f"\n### {note_file.stem}")
            print("-" * 40)
            # 找到关键词所在行及上下文
            for line in content.split('\n'):
                if keyword.lower() in line.lower():
                    print(f"  {line.strip()}")
    
    if not found:
        print(f"未找到包含「{keyword}」的笔记")

def add_insight(content: str):
    """添加阶段性洞察"""
    ensure_dirs()
    today = datetime.now().strftime('%Y-%m-%d')
    entry = f"\n### {today}\n\n{content}\n"
    
    with open(INSIGHTS_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)
    
    print(f"✅ 洞察已添加（{today}）")

def add_profile(topic: str, content: str):
    """更新情感画像"""
    ensure_dirs()
    today = datetime.now().strftime('%Y-%m-%d')
    entry = f"\n### {topic} [{today}]\n\n{content}\n"
    
    with open(PROFILE_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)
    
    print(f"✅ 画像已更新")

def summary():
    """输出完整情感档案摘要"""
    ensure_dirs()
    print("=" * 60)
    print("情感档案摘要")
    print("=" * 60)
    
    # 画像
    if PROFILE_FILE.exists():
        content = PROFILE_FILE.read_text(encoding='utf-8')
        # 只显示最后更新的部分
        sections = content.split('### ')
        if len(sections) > 1:
            print("\n【情感画像】")
            for section in sections[-3:]:
                if section.strip():
                    print(f"  {section.strip()[:200]}")
    
    # 最新笔记
    print("\n【最近笔记】")
    recent = sorted(NOTES_DIR.glob('*.md'), reverse=True)[:3]
    for note_file in recent:
        print(f"  {note_file.stem}:")
        content = note_file.read_text(encoding='utf-8')
        for line in content.split('\n'):
            if line.strip().startswith('- ') and len(line.strip()) > 5:
                print(f"    {line.strip()[:100]}")
    
    # 统计
    total_notes = len(list(NOTES_DIR.glob('*.md')))
    print(f"\n【统计】已记录 {total_notes} 天的情感笔记")

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'add':
        if len(sys.argv) < 3:
            print("用法: python emotion_note.py add \"笔记内容\"")
            sys.exit(1)
        content = ' '.join(sys.argv[2:])
        tag = ""
        if '::' in content:
            content, tag = content.split('::', 1)
            tag = tag.strip()
        add_note(content.strip(), tag.strip())
    
    elif cmd == 'view':
        view_profile()
    
    elif cmd == 'notes':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        view_notes(days)
    
    elif cmd == 'search':
        if len(sys.argv) < 3:
            print("用法: python emotion_note.py search \"关键词\"")
            sys.exit(1)
        search_notes(sys.argv[2])
    
    elif cmd == 'insight':
        if len(sys.argv) < 3:
            print("用法: python emotion_note.py insight \"洞察内容\"")
            sys.exit(1)
        add_insight(' '.join(sys.argv[2:]))
    
    elif cmd == 'profile':
        if len(sys.argv) < 4:
            print("用法: python emotion_note.py profile \"话题\" \"内容\"")
            sys.exit(1)
        add_profile(sys.argv[2], ' '.join(sys.argv[3:]))
    
    elif cmd == 'summary':
        summary()
    
    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
