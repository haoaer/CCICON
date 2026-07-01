"""CCICON — Claude Code 状态托盘指示灯"""

import sys
import time
import threading

import pystray
from pystray import MenuItem

from icon_drawer import create_icon
from status_scanner import scan
from setup import run_setup

# 闪烁间隔（秒）
FLASH_INTERVAL = 0.3
# 状态扫描间隔（秒）
SCAN_INTERVAL = 1.0
# done 闪烁持续时间（秒）
DONE_FLASH_DURATION = 3.0


class TrayApp:
    """系统托盘状态指示灯应用"""

    def __init__(self):
        self.state = "idle"          # idle / working / done / error
        self.icon = None
        self._stop_event = threading.Event()
        self._flash_on = True        # 闪烁亮/灭切换（done 用）
        self._flash_end = 0.0        # 闪烁截止时间（done 用）

        # 预创建所有图标，避免重复绘制
        self._icons = {
            "gray": create_icon("gray"),
            "yellow": create_icon("yellow"),
            "red": create_icon("red"),
            "green": create_icon("green"),
        }

    # ── 图标构建 ──────────────────────────────────────────

    def _build_icon(self) :
        """构建托盘图标"""
        return pystray.Icon(
            name="CCICON",
            icon=self._current_icon(),
            title=self._title_for_state(),
            menu=self._build_menu(),
        )

    def _current_icon(self):
        """根据当前状态和闪烁帧返回预创建的图标"""
        if self.state == "idle":
            return self._icons["gray"]
        elif self.state == "working":
            return self._icons["yellow"]
        elif self.state == "error":
            return self._icons["red"]
        elif self.state == "done":
            return self._icons["green"] if self._flash_on else self._icons["gray"]
        return self._icons["gray"]

    # ── 菜单 ─────────────────────────────────────────────

    def _build_menu(self):
        """构建右键菜单"""
        # details = get_details()

        items = []
        # if details:
        #     for d in details:
        #         status = d.get("status", "unknown")
        #         task = d.get("task", "")
        #         pid = d.get("pid", "?")
        #         label = f"[{status}] {task}" if task else f"[{status}] pid:{pid}"
        #         items.append(MenuItem(label, None, enabled=False))
        #     items.append(MenuItem("", None, enabled=False))  # 分隔线

        items.append(MenuItem("Setup", self._setup))
        items.append(MenuItem("退出", self._quit))
        return pystray.Menu(*items)

    # ── 主循环 ────────────────────────────────────────────

    def _update_loop(self):
        """
        核心循环，两种模式交替：
        - 扫描模式（idle/working/error）：每秒扫描一次，发现 done 则切换到闪烁模式
        - 闪烁模式（done）：每 0.5 秒切换亮灭，不扫描，3 秒后回到扫描模式
        """
        while not self._stop_event.is_set():
            now = time.time()
            if self.state == "done":
                # ── 闪烁模式 ──
                self._flash_on = not self._flash_on
                self._refresh_icon()
                self._stop_event.wait(FLASH_INTERVAL)

                if now >= self._flash_end:
                    self.state = scan()
            else:
                # ── 扫描模式 ──
                self._flash_on = True
                self.state = scan()

                if self.state == "done":
                    self._flash_end = now + DONE_FLASH_DURATION

                self._refresh_icon()
                self._stop_event.wait(SCAN_INTERVAL)

    # ── 刷新 ─────────────────────────────────────────────

    def _refresh_icon(self):
        """刷新图标和菜单"""
        if self.icon:
            self.icon.icon = self._current_icon()
            self.icon.title = self._title_for_state()
            self.icon.menu = self._build_menu()

    def _title_for_state(self) -> str:
        """根据状态返回提示文字"""
        return {
            "idle": "Claude Code: 空闲",
            "working": "Claude Code: 工作中...",
            "done": "Claude Code: 完成!",
            "error": "Claude Code: 出错/询问!",
        }.get(self.state, "Claude Code")

    # ── 菜单操作 ──────────────────────────────────────────

    def _setup(self, *_):
        """注册 hooks 到 ~/.claude/settings.json"""
        msg = run_setup()
        if self.icon:
            self.icon.notify(msg, "CCICON Setup")

    def _quit(self, *_):
        """退出应用"""
        self._stop_event.set()
        if self.icon:
            self.icon.stop()

    def run(self):
        """启动托盘应用"""
        self.icon = self._build_icon()

        # 在后台线程中启动状态轮询
        thread = threading.Thread(target=self._update_loop, daemon=True)
        thread.start()

        # pystray 的主循环（阻塞）
        self.icon.run()


if __name__ == "__main__":
    from single_instance import ensure_single_instance

    if not ensure_single_instance():
        sys.exit(0)

    app = TrayApp()
    app.run()
