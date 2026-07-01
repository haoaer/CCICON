"""集中管理所有路径变量"""
from pathlib import Path

# 用户目录下的 Claude 配置
CLAUDE_DIR = Path.home() / ".claude"
SETTINGS_FILE = CLAUDE_DIR / "settings.json"

# CCICON 目录和状态文件
CCICON_DIR = CLAUDE_DIR / "ccicon"
HOOKS_DIR = CCICON_DIR / "hooks"
STATUS_FILE = CCICON_DIR / "current.jsonl"
