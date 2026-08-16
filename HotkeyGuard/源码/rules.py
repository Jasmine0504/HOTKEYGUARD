# -*- coding: utf-8 -*-
"""快捷键规则定义（虚拟键码 + 修饰键条件）"""

# 触发键虚拟键码
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_TAB = 0x09
VK_ESC = 0x1B
VK_F4 = 0x73
VK_SPACE = 0x20
VK_SHIFT = 0x10
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_SNAPSHOT = 0x2C

# 修饰键（用 GetAsyncKeyState 检测是否按住）
MOD_ALT = 0x12
MOD_CTRL = 0x11
MOD_SHIFT = 0x10

# 规则表：
#   vk   : 触发键（按下/抬起时检查）
#   mods : 需要同时按住的修饰键；None 表示无条件拦截
RULES = {
    "win_key": {
        "label": "Windows 键",
        "desc": "Win / Win+D / Win+Tab / Win+Space 等全部 Win 组合",
        "vk": (VK_LWIN, VK_RWIN),
        "mods": None,
        "default": True,
    },
    "alt_tab": {
        "label": "Alt + Tab",
        "desc": "切换窗口",
        "vk": (VK_TAB,),
        "mods": ("alt",),
        "default": True,
    },
    "alt_esc": {
        "label": "Alt + Esc",
        "desc": "快速切换窗口",
        "vk": (VK_ESC,),
        "mods": ("alt",),
        "default": False,
    },
    "alt_f4": {
        "label": "Alt + F4",
        "desc": "关闭当前窗口（慎开）",
        "vk": (VK_F4,),
        "mods": ("alt",),
        "default": False,
    },
    "ctrl_esc": {
        "label": "Ctrl + Esc",
        "desc": "打开开始菜单",
        "vk": (VK_ESC,),
        "mods": ("ctrl",),
        "default": False,
    },
    "ctrl_space": {
        "label": "Ctrl + Space",
        "desc": "中英文输入法切换",
        "vk": (VK_SPACE,),
        "mods": ("ctrl",),
        "default": True,
    },
    "ctrl_shift": {
        "label": "Ctrl + Shift",
        "desc": "输入法循环切换",
        "vk": (VK_SHIFT, VK_LSHIFT, VK_RSHIFT),
        "mods": ("ctrl",),
        "default": False,
    },
    "prtsc": {
        "label": "PrintScreen",
        "desc": "截图（含 Alt+PrintScreen）",
        "vk": (VK_SNAPSHOT,),
        "mods": None,
        "default": True,
    },
}

DEFAULT_BLOCKED = [rid for rid, r in RULES.items() if r["default"]]
