"""Windows 单实例检测，防止重复启动"""

import ctypes
import sys

# Windows API
kernel32 = ctypes.windll.kernel32
_mutex = None

MUTEX_NAME = "Global\\CCICON_SingleInstance"


def ensure_single_instance() -> bool:
    """
    确保只有一个实例运行。

    返回:
        True  — 当前是唯一实例，可以继续运行
        False — 已有实例在运行，应退出
    """
    global _mutex

    _mutex = kernel32.CreateMutexW(None, False, MUTEX_NAME)
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return False
    return True
