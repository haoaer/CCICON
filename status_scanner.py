"""读取 JSONL 状态文件，聚合返回当前状态"""

import json
import time

from paths import CCICON_DIR, STATUS_FILE

# 超时阈值：超过 30 分钟未更新的进程视为过期
STALE_TIMEOUT = 60*30
# done 状态超过 3 秒视为 idle
DONE_TIMEOUT = 3

# 优先级: done > error > working > idle
PRIORITY = {"done": 0, "error": 1, "working": 2, "idle": 3}


def ensure_status_dir():
    """确保状态目录存在"""
    CCICON_DIR.mkdir(parents=True, exist_ok=True)


def _read_all() -> list[dict]:
    """读取所有 JSONL 行"""
    ensure_status_dir()
    if not STATUS_FILE.exists():
        return []

    try:
        with open(STATUS_FILE, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except OSError:
        return []

    lines = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            lines.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return lines


def _write_all(lines: list[dict]):
    """覆盖写入所有行（用于清理过期数据）"""
    if not lines:
        STATUS_FILE.write_text("", encoding="utf-8")
        return
    content = "\n".join(json.dumps(l, ensure_ascii=False) for l in lines) + "\n"
    STATUS_FILE.write_text(content, encoding="utf-8")


def _cleanup(lines: list[dict]) -> list[dict]:
    """清理过期行"""
    now = time.time()
    return [l for l in lines if now - l.get("updated_at", 0) <= STALE_TIMEOUT]



def scan() -> str:
    """
    读取 JSONL，按 pid 取最新状态，返回最高优先级。

    done 超过 3 秒自动降级为 idle。

    优先级: done > error > working > idle

    返回:
        "done"    — 任务刚完成（3秒内）→ 绿灯闪烁
        "error"   — 出错/询问 → 红灯闪烁
        "working" — 正在工作 → 黄色常亮
        "idle"    — 空闲或无状态文件 → 灰色常亮
    """
    raw = _read_all()
    lines = _cleanup(raw)

    # 有行被清理时，回写文件
    if len(lines) != len(raw):
        _write_all(lines)

    if not lines:
        return "idle"

    now = time.time()

    # 按 pid 分组，取每组最新一条
    by_pid: dict[int, dict] = {}
    for entry in lines:
        pid = entry.get("pid", 0)
        if pid not in by_pid or entry.get("updated_at", 0) > by_pid[pid].get("updated_at", 0):
            by_pid[pid] = entry

    # 取最高优先级（done 超时则降级为 idle）
    best = "idle"
    for entry in by_pid.values():
        s = entry.get("status", "idle")
        if s == "done" and now - entry.get("updated_at", 0) > DONE_TIMEOUT:
            s = "idle"
        if PRIORITY.get(s, 99) < PRIORITY.get(best, 99):
            best = s
    return best


# def get_details() -> list[dict]:
#     """获取所有活跃进程的状态详情（用于菜单显示）"""
#     lines = _cleanup(_read_all())

#     # 按 pid 取最新
#     by_pid: dict[int, dict] = {}
#     for entry in lines:
#         pid = entry.get("pid", 0)
#         if pid not in by_pid or entry.get("updated_at", 0) > by_pid[pid].get("updated_at", 0):
#             by_pid[pid] = entry

#     return list(by_pid.values())
