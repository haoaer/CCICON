"""将 CCICON hooks 注册到 ~/.claude/settings.json

流程:
1. 在 hooks 目录下生成 sh 脚本，直接 echo JSONL 追加到状态文件
2. 把 sh 脚本路径写入 ~/.claude/settings.json 的 hooks 配置
"""

import json

from paths import HOOKS_DIR, SETTINGS_FILE, STATUS_FILE, CCICON_DIR


def _to_linux_path(path) -> str:
    """将 Windows 路径转为 Linux/MSYS2 形式：C:\\Users\\... → /c/Users/..."""
    p = str(path).replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        p = "/" + p[0].lower() + p[2:]
    return p

# settings.json 中注册的 hook 类型
HOOK_TYPES = {
    "SessionStart": "done.sh",
    "UserPromptSubmit": "work.sh",
    "PermissionRequest": "error.sh",
    "Stop": "done.sh",
    "SessionEnd": "idle.sh",
    "PermissionDenied":"idle.sh"
}

# sh 脚本内容（路径用 Linux 形式）
_STATUS_LINUX = _to_linux_path(STATUS_FILE)
SH_SCRIPTS = {
    "done.sh": f'''#!/bin/bash
SID=$(cat | grep -o '"session_id":"[^"]*"' | head -1 | sed 's/.*"session_id":"\\([^"]*\\)".*/\\1/')
[ -z "$SID" ] && SID="unknown"
echo "{{\\"pid\\":\\"$SID\\",\\"status\\":\\"done\\",\\"task\\":\\"\\",\\"updated_at\\":$(date +%s)}}">> "{_STATUS_LINUX}"
''',
    "work.sh": f'''#!/bin/bash
SID=$(cat | grep -o '"session_id":"[^"]*"' | head -1 | sed 's/.*"session_id":"\\([^"]*\\)".*/\\1/')
[ -z "$SID" ] && SID="unknown"
echo "{{\\"pid\\":\\"$SID\\",\\"status\\":\\"working\\",\\"task\\":\\"工作中...\\",\\"updated_at\\":$(date +%s)}}">> "{_STATUS_LINUX}"
''',
    "error.sh": f'''#!/bin/bash
SID=$(cat | grep -o '"session_id":"[^"]*"' | head -1 | sed 's/.*"session_id":"\\([^"]*\\)".*/\\1/')
[ -z "$SID" ] && SID="unknown"
echo "{{\\"pid\\":\\"$SID\\",\\"status\\":\\"error\\",\\"task\\":\\"\\",\\"updated_at\\":$(date +%s)}}">> "{_STATUS_LINUX}"
''',
    "idle.sh": f'''#!/bin/bash
SID=$(cat | grep -o '"session_id":"[^"]*"' | head -1 | sed 's/.*"session_id":"\\([^"]*\\)".*/\\1/')
[ -z "$SID" ] && SID="unknown"
echo "{{\\"pid\\":\\"$SID\\",\\"status\\":\\"idle\\",\\"task\\":\\"\\",\\"updated_at\\":$(date +%s)}}">> "{_STATUS_LINUX}"
''',
}


def _write_sh_scripts() -> list[str]:
    """生成 sh 脚本到 hooks 目录"""
    CCICON_DIR.mkdir(parents=True, exist_ok=True)
    HOOKS_DIR.mkdir(parents=True, exist_ok=True)
    written = []

    for sh_name, content in SH_SCRIPTS.items():
        sh_path = CCICON_DIR / "hooks" / sh_name
        sh_path.write_text(content.strip(), encoding="utf-8")
        written.append(str(sh_path))
    return written


def _update_settings() -> list[str]:
    """将 sh 脚本注册到 settings.json，返回新增的 hook 类型"""
    settings = {}
    if SETTINGS_FILE.exists():
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    
    settings["hooks"] = {}

    added = []
    for hook_type, sh_name in HOOK_TYPES.items():
        sh_path = _to_linux_path(CCICON_DIR / "hooks" / sh_name)
        cmd = f"bash {sh_path}"

        existing = settings["hooks"].get(hook_type, [])
        if not any(e.get("command") == cmd for e in existing):
            existing.append({"hooks":[{"command": cmd,"type": "command"}]})
            settings["hooks"][hook_type] = existing
            added.append(hook_type)
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return added


def run_setup() -> str:
    """
    创建状态目录 + 生成 sh 脚本 + 注册到 settings.json。

    返回:
        成功或失败的消息字符串
    """
    try:
        CCICON_DIR.mkdir(parents=True, exist_ok=True)
        _write_sh_scripts()
        added = _update_settings()
    except OSError as e:
        return f"Setup 失败: {e}"

    if added:
        return f"已注册: {', '.join(added)}"
    return "Hooks 已存在，无需重复注册"
