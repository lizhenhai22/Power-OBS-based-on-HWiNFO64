import tkinter as tk
from tkinter import messagebox, filedialog
import winreg
import subprocess
import ctypes
import json
import sys
import os

# 获取程序运行所在目录（兼容 PyInstaller 打包后的 exe 路径）
BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")
TASK_NAME = "StartHWiNFO_Silent"

DEFAULT_CONFIG = {
    "hwinfo_path": r"C:\Program Files\HWiNFO64\HWiNFO64.exe",
    "opacity": 0.80,
    "sensors": {
        "CPU 封装功率": ["CPU 功耗", "#89B4FA"],
        "GT 核心功率":  ["GPU 功耗", "#A6E3A1"],
        "系统总功率":   ["整机功耗", "#F9E2AF"]
    }
}

user32 = ctypes.windll.user32

def load_or_init_config():
    """加载配置文件，若不存在或路径无效则引导用户选择 HWiNFO64.exe"""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except Exception:
            pass

    if not os.path.exists(config["hwinfo_path"]):
        root_tmp = tk.Tk()
        root_tmp.withdraw()
        messagebox.showinfo("首次运行配置", "请选择您电脑上 HWiNFO64.exe 的所在位置。\n（配置将自动保存在 config.json 中）")
        selected = filedialog.askopenfilename(
            title="选择 HWiNFO64.exe",
            filetypes=[("HWiNFO64 Executable", "HWiNFO64.exe"), ("All Executables", "*.exe")]
        )
        root_tmp.destroy()
        if selected and os.path.exists(selected):
            config["hwinfo_path"] = selected
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        else:
            sys.exit(0)
    elif not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

    return config

def is_hwinfo_running():
    output = subprocess.check_output('tasklist /FI "IMAGENAME eq HWiNFO64.exe"', shell=True).decode('gbk', errors='ignore')
    return "HWiNFO64.exe" in output

def ensure_silent_ini(hwinfo_dir):
    ini_path = os.path.join(hwinfo_dir, "HWiNFO64.INI")
    if not os.path.exists(ini_path):
        return
    try:
        with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        target_settings = {
            "SensorsOnly": "1", "SummaryOnly": "0",
            "MinimizeMainWindow": "1", "MinimizeSensors": "1",
            "ShowWelcome": "0", "AutoRun": "1"
        }
        new_lines, found_keys = [], set()
        for line in lines:
            if "=" in line:
                k = line.split("=", 1)[0].strip()
                if k in target_settings:
                    new_lines.append(f"{k}={target_settings[k]}\n")
                    found_keys.add(k)
                    continue
            new_lines.append(line)
        for k, v in target_settings.items():
            if k not in found_keys:
                new_lines.append(f"{k}={v}\n")
        with open(ini_path, "w", encoding="utf-8", errors="ignore") as f:
            f.writelines(new_lines)
    except Exception:
        pass

def start_hwinfo(hwinfo_path):
    hwinfo_dir = os.path.dirname(hwinfo_path)
    ensure_silent_ini(hwinfo_dir)
    ret = subprocess.call(f'schtasks /run /tn "{TASK_NAME}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if ret != 0:
        ctypes.windll.shell32.ShellExecuteW(None, "open", hwinfo_path, None, hwinfo_dir, 1)

def stop_hwinfo():
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_cb(hwnd, lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            if "HWiNFO" in buf.value:
                user32.PostMessageW(hwnd, 0x0010, 0, 0)
        return True
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    subprocess.call(f'schtasks /run /tn "{TASK_NAME}_Kill"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def read_hwinfo_reg(sensors_map):
    data = {}
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\HWiNFO64\VSB")
        i = 0
        while True:
            try:
                label, _ = winreg.QueryValueEx(key, f"Label{i}")
                val, _ = winreg.QueryValueEx(key, f"Value{i}")
                for target_key, (display_name, _) in sensors_map.items():
                    if target_key in label:
                        data[display_name] = val
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except FileNotFoundError:
        pass
    return data

class ModernPowerHUD:
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.sensors_map = config["sensors"]

        if os.path.exists(ICON_PATH):
            try:
                self.root.iconbitmap(ICON_PATH)
            except Exception:
                pass

        if not is_hwinfo_running():
            start_hwinfo(config["hwinfo_path"])

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", config.get("opacity", 0.90))
        self.bg_color = "#181825"
        self.root.config(bg=self.bg_color)
        
        screen_w = self.root.winfo_screenwidth()
        height = 38 + len(self.sensors_map) * 32
        self.root.geometry(f"200x{height}+{screen_w - 230}+40")

        self.root.update_idletasks()
        try:
            hwnd = user32.GetParent(self.root.winfo_id())
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(ctypes.c_int(2)), 4)
        except Exception:
            pass

        header = tk.Frame(root, bg="#1E1E2E", height=26)
        header.pack(fill="x", padx=2, pady=(2, 4))
        
        self.dot = tk.Label(header, text="●", font=("Segoe UI", 9), fg="#A6E3A1", bg="#1E1E2E")
        self.dot.pack(side="left", padx=(10, 4))
        
        title = tk.Label(header, text="POWER MONITOR", font=("Segoe UI", 8, "bold"), fg="#6C7086", bg="#1E1E2E")
        title.pack(side="left")

        close_btn = tk.Label(header, text="×", font=("Segoe UI", 11, "bold"), fg="#6C7086", bg="#1E1E2E", cursor="hand2")
        close_btn.pack(side="right", padx=10)
        close_btn.bind("<Button-1>", self.quit_all)
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#F38BA8"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg="#6C7086"))

        self.val_labels = {}
        for _, (display_name, color) in self.sensors_map.items():
            row = tk.Frame(root, bg=self.bg_color)
            row.pack(fill="x", padx=14, pady=4)
            
            lbl_name = tk.Label(row, text=display_name, font=("Microsoft YaHei UI", 9), fg="#BAC2DE", bg=self.bg_color)
            lbl_name.pack(side="left")
            
            lbl_val = tk.Label(row, text="Wait...", font=("Consolas", 11, "bold"), fg=color, bg=self.bg_color)
            lbl_val.pack(side="right")
            self.val_labels[display_name] = lbl_val

        for widget in (self.root, header, title):
            widget.bind("<ButtonPress-1>", self.start_move)
            widget.bind("<B1-Motion>", self.do_move)
        self.root.bind("<Button-3>", self.quit_all)

        self.pulse = True
        self.update_stats()

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def do_move(self, event):
        x = self.root.winfo_x() + (event.x - self.x)
        y = self.root.winfo_y() + (event.y - self.y)
        self.root.geometry(f"+{x}+{y}")

    def update_stats(self):
        stats = read_hwinfo_reg(self.sensors_map)
        if stats:
            self.dot.config(fg="#A6E3A1" if self.pulse else "#45475A")
            self.pulse = not self.pulse
            for display_name, lbl in self.val_labels.items():
                lbl.config(text=stats.get(display_name, "-- W"))
        else:
            self.dot.config(fg="#F38BA8")
        self.root.after(1000, self.update_stats)

    def quit_all(self, event=None):
        self.root.destroy()
        stop_hwinfo()

if __name__ == "__main__":
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    cfg = load_or_init_config()
    root = tk.Tk()
    app = ModernPowerHUD(root, cfg)
    root.mainloop()

    def quit_all(self, event=None):
        """退出悬浮窗，并自动关闭后台的 HWiNFO64"""
        self.root.destroy()
        if is_hwinfo_running():
            # 使用 runas 提权静默结束 HWiNFO64 进程 (最后参数 0 表示隐藏黑框)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", "taskkill", "/F /IM HWiNFO64.exe", None, 0)