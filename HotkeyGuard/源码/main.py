# -*- coding: utf-8 -*-
"""HotkeyGuard · 快捷键守卫 — 游戏模式快捷键拦截器"""

import os
import sys
import time

import customtkinter as ctk
import pystray
from PIL import Image as PILImage

import hook
import settings
from rules import RULES, DEFAULT_BLOCKED

ACCENT = "#22d3ee"
BG = "#0b0f16"
CARD = "#121826"
CARD_HOVER = "#1a2233"
TEXT = "#e6edf3"
MUTED = "#8b98a9"
GREEN = "#34d399"
RED = "#f87171"


def resource_path(rel: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def F(size=13, weight="normal"):
    return ctk.CTkFont(family="Microsoft YaHei UI", size=size, weight=weight)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("HotkeyGuard · 快捷键守卫")
        self.geometry("460x660")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        try:
            self.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass

        self.cfg = settings.load()
        hook.state.mode = self.cfg["mode"]
        hook.state.blocked = set(self.cfg["blocked"])

        self.protocol("WM_DELETE_WINDOW", self._on_close_request)
        self._tray = None
        self._hint_shown = False
        self._build()
        self.after(120, self._poll_events)
        hook.start()
        self.after(400, self.lift)
        self._start_tray()

    # ---------------- UI ----------------
    def _build(self):
        # 头部
        header = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14)
        header.pack(fill="x", padx=14, pady=(14, 8))
        self.status_dot = ctk.CTkLabel(header, text="●", font=F(18), width=22)
        self.status_dot.pack(side="left", padx=(16, 4), pady=14)
        ctk.CTkLabel(header, text="HotkeyGuard", font=F(17, "bold"),
                     text_color=TEXT).pack(side="left")
        ctk.CTkLabel(header, text="快捷键守卫", font=F(11), text_color=MUTED).pack(
            side="left", padx=(8, 0), pady=(16, 0))
        self.mode_badge = ctk.CTkLabel(header, text="正常模式",
                                       font=F(12, "bold"), fg_color="#1e293b",
                                       corner_radius=10, width=96)
        self.mode_badge.pack(side="right", padx=12, pady=12)

        # 模式切换
        self.seg = ctk.CTkSegmentedButton(
            self,
            values=["正常模式", "游戏模式"],
            command=self._on_mode_change,
            fg_color=CARD,
            selected_color=ACCENT,
            selected_hover_color="#0ea5e9",
            unselected_color=CARD_HOVER,
            unselected_hover_color="#1f2937",
            text_color=TEXT,
            font=F(14, "bold"),
            height=40,
        )
        self.seg.pack(fill="x", padx=14, pady=8)

        # 内容区
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=14, pady=4)

        self._build_normal_panel()
        self._build_game_panel()
        self._show_panel()

        # 底部
        footer = ctk.CTkFrame(self, fg_color=CARD, corner_radius=14)
        footer.pack(fill="x", padx=14, pady=(8, 14))
        ctk.CTkLabel(footer, text="F8 切换模式 · 关窗口可选后台/退出",
                     font=F(12), text_color=MUTED).pack(side="left", padx=14, pady=10)
        self.topmost_switch = ctk.CTkSwitch(
            footer, text="窗口置顶", font=F(12), text_color=MUTED,
            progress_color=ACCENT, command=self._on_topmost)
        self.topmost_switch.pack(side="right", padx=14)
        if self.cfg["topmost"]:
            self.topmost_switch.select()
            self.attributes("-topmost", True)

    def _build_normal_panel(self):
        self.normal_panel = ctk.CTkFrame(self.content, fg_color="transparent")
        card = ctk.CTkFrame(self.normal_panel, fg_color=CARD, corner_radius=14)
        card.pack(fill="x", padx=2, pady=10)
        ctk.CTkLabel(card, text="✓", font=F(36, "bold"), text_color=GREEN).pack(pady=(26, 2))
        ctk.CTkLabel(card, text="所有快捷键拦截已关闭", font=F(16, "bold"),
                     text_color=TEXT).pack()
        ctk.CTkLabel(card, text="系统行为完全正常，可放心使用",
                     font=F(12), text_color=MUTED).pack(pady=(4, 20))
        self.restore_btn = ctk.CTkButton(
            card, text="恢复默认设置", command=self._on_restore_defaults,
            fg_color="#1e293b", hover_color=CARD_HOVER, text_color=TEXT,
            border_color="#334155", border_width=1, font=F(13, "bold"), height=38)
        self.restore_btn.pack(padx=48, pady=(0, 6))
        self.restore_feedback = ctk.CTkLabel(card, text="", font=F(11), text_color=GREEN)
        self.restore_feedback.pack(pady=(0, 18))

    def _build_game_panel(self):
        self.game_panel = ctk.CTkFrame(self.content, fg_color="transparent")
        self.scroll = ctk.CTkScrollableFrame(
            self.game_panel, fg_color=CARD, corner_radius=14,
            scrollbar_button_color="#334155", scrollbar_button_hover_color="#475569")
        self.scroll.pack(fill="both", expand=True, padx=2, pady=10)

        head = ctk.CTkFrame(self.scroll, fg_color="transparent")
        head.pack(fill="x", padx=6, pady=(8, 2))
        ctk.CTkLabel(head, text="选择要禁用的快捷键", font=F(13, "bold"),
                     text_color=TEXT).pack(side="left", padx=4)
        self.rule_count = ctk.CTkLabel(head, text="", font=F(11), text_color=ACCENT)
        self.rule_count.pack(side="right", padx=4)

        self.switches = {}
        for rid, rule in RULES.items():
            row = ctk.CTkFrame(self.scroll, fg_color="#0f1522", corner_radius=10)
            row.pack(fill="x", padx=6, pady=4)
            txt = ctk.CTkFrame(row, fg_color="transparent")
            txt.pack(side="left", fill="x", expand=True, padx=12, pady=8)
            ctk.CTkLabel(txt, text=rule["label"], font=F(13, "bold"),
                         text_color=TEXT, anchor="w").pack(fill="x")
            ctk.CTkLabel(txt, text=rule["desc"], font=F(11),
                         text_color=MUTED, anchor="w").pack(fill="x")
            sw = ctk.CTkSwitch(row, text="", progress_color=ACCENT,
                               button_color="#f8fafc",
                               command=lambda r=rid: self._on_rule_toggle(r))
            sw.pack(side="right", padx=14)
            if rid in hook.state.blocked:
                sw.select()
            self.switches[rid] = sw

        self.game_status = ctk.CTkLabel(self.scroll, text="", font=F(12), text_color=MUTED)
        self.game_status.pack(fill="x", padx=10, pady=(6, 12))

    # ---------------- 系统托盘 ----------------
    def _start_tray(self):
        try:
            img = PILImage.open(resource_path("icon.png")).convert("RGBA").resize(
                (32, 32), PILImage.LANCZOS)
            menu = pystray.Menu(
                pystray.MenuItem("显示 / 隐藏窗口",
                                 lambda i, it: self._tray_event("show"), default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("游戏模式", lambda i, it: self._tray_event("game"),
                                 checked=lambda item: hook.state.mode == "game"),
                pystray.MenuItem("正常模式", lambda i, it: self._tray_event("normal"),
                                 checked=lambda item: hook.state.mode == "normal"),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", lambda i, it: self._tray_event("quit")),
            )
            self._tray = pystray.Icon("HotkeyGuard", img, "HotkeyGuard · 快捷键守卫", menu)
            self._tray.run_detached()
        except Exception:
            self._tray = None  # 托盘启动失败不阻塞主功能

    def _tray_event(self, what):
        # 托盘回调在独立线程，通过事件队列交给主线程处理
        hook.state.events.put(("tray", what))

    def on_hide(self):
        # 点关闭按钮 → 隐藏到托盘，钩子继续运行
        self.withdraw()
        if not self._hint_shown and self._tray:
            self._hint_shown = True
            try:
                self._tray.notify("已驻留后台运行，右键托盘图标可切换模式或退出", "HotkeyGuard")
            except Exception:
                pass

    def _handle_tray_event(self, what):
        if what == "show":
            if self.state() == "withdrawn":
                self.deiconify()
                self.lift()
            else:
                self.withdraw()
        elif what in ("game", "normal"):
            if hook.state.mode != what:
                hook.state.mode = what
                self.cfg["mode"] = what
                settings.save(self.cfg)
            self._show_panel()
        elif what == "quit":
            self.on_close()

    def _on_close_request(self):
        """点关闭按钮 → 弹选择框：后台运行 / 退出 / 取消"""
        dlg = ctk.CTkToplevel(self)
        dlg.title("HotkeyGuard")
        dlg.geometry("400x230")
        dlg.resizable(False, False)
        dlg.configure(fg_color=BG)
        dlg.transient(self)
        dlg.grab_set()
        dlg.protocol("WM_DELETE_WINDOW", dlg.destroy)
        x = self.winfo_x() + (self.winfo_width() - 400) // 2
        y = self.winfo_y() + (self.winfo_height() - 230) // 3
        dlg.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        try:
            dlg.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass
        dlg.lift()
        dlg.focus_force()

        ctk.CTkLabel(dlg, text="关闭窗口后", font=F(17, "bold"),
                     text_color=TEXT).pack(pady=(24, 2))
        ctk.CTkLabel(dlg, text="选择要执行的操作", font=F(12),
                     text_color=MUTED).pack(pady=(0, 16))

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack()
        ctk.CTkButton(btns, text="后台运行", font=F(13, "bold"), fg_color=ACCENT,
                      hover_color="#0ea5e9", text_color="#04222b", width=104, height=38,
                      command=lambda: self._close_choice("hide", dlg)).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="退出", font=F(13, "bold"), fg_color="#1e293b",
                      hover_color="#b91c1c", text_color=TEXT, width=104, height=38,
                      border_color="#334155", border_width=1,
                      command=lambda: self._close_choice("quit", dlg)).pack(side="left", padx=6)
        ctk.CTkButton(btns, text="取消", font=F(13), fg_color="transparent",
                      hover_color=CARD_HOVER, text_color=MUTED, width=80, height=38,
                      command=dlg.destroy).pack(side="left", padx=6)

    def _close_choice(self, what, dlg):
        dlg.destroy()
        if what == "hide":
            self.on_hide()
        else:
            self.on_close()

    # ---------------- 逻辑 ----------------
    def _show_panel(self):
        mode = hook.state.mode
        self.seg.set("游戏模式" if mode == "game" else "正常模式")
        if mode == "game":
            self.normal_panel.pack_forget()
            self.game_panel.pack(fill="both", expand=True)
            self.mode_badge.configure(text="游戏模式 · 拦截中",
                                      fg_color="#134e4a", text_color="#5eead4")
            self.status_dot.configure(text_color=GREEN)
        else:
            self.game_panel.pack_forget()
            self.normal_panel.pack(fill="both", expand=True)
            self.mode_badge.configure(text="正常模式",
                                      fg_color="#1e293b", text_color="#cbd5e1")
            self.status_dot.configure(text_color=MUTED)
        self._refresh_counts()

    def _refresh_counts(self):
        n = len(hook.state.blocked)
        self.rule_count.configure(text=f"{n} 项已启用")
        if hook.state.mode == "game":
            if n == 0:
                self.game_status.configure(
                    text="未启用任何拦截，Win 键仍可切出游戏", text_color=RED)
            else:
                self.game_status.configure(
                    text=f"● 拦截已启用 · {n} 个快捷键被禁用\n提示：Ctrl+Alt+Del 无法拦截 · 按 F8 随时切回正常模式",
                    text_color=MUTED)
        else:
            self.game_status.configure(text="")

    def _on_mode_change(self, value):
        mode = "game" if value == "游戏模式" else "normal"
        if mode != hook.state.mode:
            hook.state.mode = mode
            self.cfg["mode"] = mode
            settings.save(self.cfg)
        self._show_panel()

    def _on_rule_toggle(self, rid):
        if rid in hook.state.blocked:
            hook.state.blocked.discard(rid)
        else:
            hook.state.blocked.add(rid)
        order = {r: i for i, r in enumerate(RULES)}
        self.cfg["blocked"] = sorted(hook.state.blocked, key=lambda r: order[r])
        settings.save(self.cfg)
        self._refresh_counts()

    def _on_restore_defaults(self):
        hook.state.blocked = set(DEFAULT_BLOCKED)
        self.cfg["blocked"] = list(DEFAULT_BLOCKED)
        settings.save(self.cfg)
        for rid, sw in self.switches.items():
            (sw.select if rid in hook.state.blocked else sw.deselect)()
        self._refresh_counts()
        self.restore_feedback.configure(text="已恢复默认勾选")
        self.after(2500, lambda: self.restore_feedback.configure(text=""))

    def _on_topmost(self):
        on = bool(self.topmost_switch.get())
        self.attributes("-topmost", on)
        self.cfg["topmost"] = on
        settings.save(self.cfg)

    def _poll_events(self):
        try:
            while True:
                ev = hook.state.events.get_nowait()
                if ev[0] == "mode":
                    self._show_panel()
                elif ev[0] == "tray":
                    self._handle_tray_event(ev[1])
        except Exception:
            pass
        self.after(120, self._poll_events)

    def on_close(self):
        hook.stop()
        if self._tray:
            try:
                self._tray.stop()
            except Exception:
                pass
        self.destroy()


# ---------------- 自测 ----------------
def run_selftest():
    import ctypes as _ct
    from ctypes import wintypes as _w

    user32 = hook.user32
    # 注：此环境下 SendInput 报 ERROR_INVALID_PARAMETER(87)，改用 keybd_event 注入
    user32.keybd_event.argtypes = [_w.BYTE, _w.BYTE, _w.DWORD, _ct.c_void_p]
    user32.keybd_event.restype = None

    def send_key(vk, down):
        user32.keybd_event(vk, 0, 0 if down else 2, None)

    results = []
    base_seen = hook.state.stats["seen"]
    base_blocked = hook.state.stats["blocked"]

    def delta_seen():
        return hook.state.stats["seen"] - base_seen

    def delta_blocked():
        return hook.state.stats["blocked"] - base_blocked

    def check(name, cond):
        results.append((name, bool(cond)))
        print(("PASS" if cond else "FAIL"), "-", name)

    # 游戏模式，全部规则开启
    hook.state.mode = "game"
    hook.state.blocked = set(RULES.keys())
    hook.start()
    time.sleep(0.3)
    try:
        err = hook.state.events.get_nowait()
        if err[0] == "error":
            print("HOOK ERROR:", err[1])
            sys.exit(1)
    except Exception:
        pass
    print(f"钩子已安装，初始 stats: {hook.state.stats}")

    # 1. Win 键被吞
    s0, b0 = delta_seen(), delta_blocked()
    send_key(0x5B, True); time.sleep(0.12)
    send_key(0x5B, False); time.sleep(0.1)
    check("Win 键触发拦截", delta_blocked() - b0 >= 1 and delta_seen() - s0 >= 2)

    # 2. Alt+Tab 被吞
    s0, b0 = delta_seen(), delta_blocked()
    send_key(0x12, True); time.sleep(0.06)
    send_key(0x09, True); time.sleep(0.1)
    send_key(0x09, False); send_key(0x12, False); time.sleep(0.1)
    check("Alt+Tab 触发拦截", delta_blocked() - b0 >= 1)

    # 3. F8 全局切换
    s0 = delta_seen()
    send_key(0x77, True); time.sleep(0.06); send_key(0x77, False); time.sleep(0.25)
    check("F8 切回正常模式", hook.state.mode == "normal" and delta_seen() - s0 >= 2)

    # 4. 正常模式不拦截（用 Tab 单键验证，避免误开开始菜单）
    s0, b0 = delta_seen(), delta_blocked()
    send_key(0x09, True); time.sleep(0.1)
    send_key(0x09, False); time.sleep(0.1)
    check("正常模式不拦截", delta_seen() - s0 >= 2 and delta_blocked() == b0)

    # 5. 切回游戏模式，Ctrl+Space 被吞
    hook.state.mode = "game"
    time.sleep(0.05)
    s0, b0 = delta_seen(), delta_blocked()
    send_key(0x11, True); time.sleep(0.06)
    send_key(0x20, True); time.sleep(0.1)
    send_key(0x20, False); send_key(0x11, False); time.sleep(0.1)
    check("Ctrl+Space 触发拦截", delta_blocked() - b0 >= 1)

    hook.stop()
    ok = all(c for _, c in results)
    print(f"最终 stats: {hook.state.stats}")
    print("RESULT:", "ALL PASS" if ok else "SOME FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        run_selftest()
    else:
        ctk.set_appearance_mode("dark")
        App().mainloop()
