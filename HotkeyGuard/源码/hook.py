# -*- coding: utf-8 -*-
"""全局低级键盘钩子（WH_KEYBOARD_LL）：在按键到达任何程序之前拦截"""

import ctypes
import queue
import threading
import time
import winsound
from ctypes import wintypes

from rules import RULES, MOD_ALT, MOD_CTRL, MOD_SHIFT

WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_QUIT = 0x0012

VK_F8 = 0x77  # 全局切换热键

MOD_VK = {"alt": MOD_ALT, "ctrl": MOD_CTRL, "shift": MOD_SHIFT}

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]
user32.SetWindowsHookExW.restype = wintypes.HHOOK
user32.CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_long
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
user32.PostThreadMessageW.restype = wintypes.BOOL
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = wintypes.SHORT
user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
user32.UnhookWindowsHookEx.restype = wintypes.BOOL


class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class State:
    """钩子线程与 UI 共享的状态"""

    def __init__(self):
        self.mode = "normal"  # "normal" | "game"
        self.blocked = set()  # 启用的规则 id 集合
        self.events = queue.Queue()  # 钩子线程 -> UI 的通知
        self.stats = {"seen": 0, "blocked": 0}  # 调试/自测用


state = State()

_hook_handle = None
_hook_proc = None
_thread = None
_last_toggle = [0.0]


class HookError(Exception):
    pass


def _mod_is_down(name: str) -> bool:
    return bool(user32.GetAsyncKeyState(MOD_VK[name]) & 0x8000)


def should_block(vk: int, is_down: bool) -> bool:
    """判断某个按键事件是否应被拦截"""
    if state.mode != "game":
        return False
    for rid in state.blocked:
        rule = RULES.get(rid)
        if not rule:
            continue
        if vk not in rule["vk"]:
            continue
        mods = rule["mods"]
        if mods is None or all(_mod_is_down(m) for m in mods):
            return True
    return False


def _toggle_from_hook():
    state.mode = "game" if state.mode == "normal" else "normal"
    try:
        winsound.Beep(1200 if state.mode == "game" else 500, 80)
    except Exception:
        pass
    state.events.put(("mode", state.mode))


def _callback(nCode: int, wParam: int, lParam: int) -> int:
    if nCode >= 0:
        kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
        vk = int(kb.vkCode)
        is_down = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)
        state.stats["seen"] += 1

        # 全局切换热键 F8：不受模式与规则影响，始终生效
        if vk == VK_F8 and is_down:
            now = time.monotonic()
            if now - _last_toggle[0] > 0.25:
                _last_toggle[0] = now
                _toggle_from_hook()

        if should_block(vk, is_down):
            state.stats["blocked"] += 1
            return 1  # 吞掉按键，系统和其他程序都收不到

    return user32.CallNextHookEx(_hook_handle, nCode, wParam, lParam)


def start():
    """启动钩子：钩子线程自行安装并泵消息（回调由系统投递到安装线程的消息队列）"""
    global _thread
    if _thread and _thread.is_alive():
        return
    _thread = threading.Thread(target=_run, name="hook-loop", daemon=True)
    _thread.start()


def _run():
    global _hook_handle, _hook_proc
    try:
        _hook_proc = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)(_callback)
        # 低级钩子（WH_KEYBOARD_LL）回调在安装线程内执行，hMod 传 NULL 即可；
        # 传模块句柄反而会报 ERROR_MOD_NOT_FOUND(126)
        _hook_handle = user32.SetWindowsHookExW(WH_KEYBOARD_LL, _hook_proc, None, 0)
        if not _hook_handle:
            raise ctypes.WinError(ctypes.get_last_error())
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    except Exception as e:  # noqa: BLE001
        state.events.put(("error", str(e)))
    finally:
        if _hook_handle:
            user32.UnhookWindowsHookEx(_hook_handle)
            _hook_handle = None


def stop():
    global _hook_handle, _thread
    if _thread and _thread.ident:
        user32.PostThreadMessageW(_thread.ident, WM_QUIT, 0, 0)
        _thread = None
