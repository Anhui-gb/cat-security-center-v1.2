# 小猫安全中心 v1.2
import os
import shutil
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import random
import subprocess
import datetime
import webbrowser
import sys

# ================= 存档配置 =================
SHORTCUTS_FILE = "shortcuts.txt"
ERROR_LOG_FILE = "error_log.txt"
CACHE_FILE = "cache_paths.txt"
VERSION = "1.2"

TARGET_DIRS = [
    os.environ.get('TEMP', ''),
    os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp'),
    os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp'),
]

DEFAULT_CACHE_PATHS = [
    ("用户临时文件夹", os.environ.get('TEMP', '')),
    ("系统临时文件夹", os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Temp')),
    ("本地临时文件夹", os.environ.get('LOCALAPPDATA', '') + '\\Temp'),
    ("预读取缓存", os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'Prefetch')),
    ("回收站", os.path.join(os.environ.get('SystemDrive', 'C:'), '$Recycle.Bin')),
]

# ================= 存档读写 =================
def load_shortcuts():
    shortcuts = []
    if os.path.exists(SHORTCUTS_FILE):
        try:
            with open(SHORTCUTS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    parts = line.split("|", 1)
                    if len(parts) == 2:
                        shortcuts.append({"name": parts[0], "path": parts[1]})
        except: pass
    return shortcuts

def save_shortcuts(shortcuts):
    with open(SHORTCUTS_FILE, "w", encoding="utf-8") as f:
        for s in shortcuts:
            f.write(f"{s['name']}|{s['path']}\n")

def load_error_logs():
    logs = []
    if os.path.exists(ERROR_LOG_FILE):
        try:
            with open(ERROR_LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line: logs.append(line)
        except: pass
    return logs

def save_error_logs(logs):
    with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
        for p in logs:
            f.write(p + "\n")

def load_cache_paths():
    paths = []
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    parts = line.split("|", 1)
                    if len(parts) == 2:
                        paths.append((parts[0], parts[1]))
        except: pass
    if not paths:
        paths = DEFAULT_CACHE_PATHS.copy()
    return paths

def save_cache_paths(paths):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        for name, path in paths:
            f.write(f"{name}|{path}\n")

# ================= 清理逻辑 =================
def get_size(path):
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
    except: pass
    return total

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def clean_dir(path):
    deleted = 0
    freed = 0
    errors = []
    if not path or not os.path.exists(path):
        return deleted, freed, errors
    try:
        items = os.listdir(path)
    except PermissionError:
        return deleted, freed, errors
    for item in items:
        item_path = os.path.join(path, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                size = os.path.getsize(item_path)
                os.remove(item_path)
                deleted += 1
                freed += size
            elif os.path.isdir(item_path):
                size = get_size(item_path)
                shutil.rmtree(item_path, ignore_errors=True)
                deleted += 1
                freed += size
        except Exception:
            errors.append(item_path)
    return deleted, freed, errors

def open_folder(path):
    try:
        path = os.path.normpath(path.strip())
        if not os.path.exists(path):
            messagebox.showwarning("找不到该文件夹", f"找不到该文件夹：\n{path}")
            return
        if os.path.isfile(path):
            subprocess.Popen(f'explorer /select,"{path}"', shell=True)
        else:
            os.startfile(path)
    except Exception as e:
        messagebox.showerror("打开失败", str(e))

# ================= 启动动画 =================
class SplashScreen:
    def __init__(self, root):
        self.root = root
        self.root.title(f"小猫安全中心 v{VERSION}")
        self.root.geometry("400x340")
        self.root.resizable(False, False)

        today = datetime.date.today()
        self.is_national_day = (today.month == 10 and today.day == 1)

        if self.is_national_day:
            self.bg_color = "#DE2910"
            self.star_color = "#FFDE00"
        else:
            self.bg_color = "#ff8800"
            self.star_color = "#ffffff"

        self.root.configure(bg=self.bg_color)
        self.center_window(400, 340)

        if self.is_national_day:
            tk.Label(root, text="金秋十月山河秀", font=("微软雅黑", 15, "bold"),
                     bg=self.bg_color, fg=self.star_color).pack(pady=(12, 0))
            tk.Label(root, text="盛世中华日月新", font=("微软雅黑", 15, "bold"),
                     bg=self.bg_color, fg=self.star_color).pack(pady=(0, 4))
            tk.Label(root, text=f"🇨🇳 小猫安全中心 v{VERSION} 🇨🇳", font=("微软雅黑", 13, "bold"),
                     bg=self.bg_color, fg="#ffffff").pack(pady=(3, 3))
        else:
            tk.Label(root, text=f"🐱 小猫安全中心 v{VERSION}", font=("微软雅黑", 22, "bold"),
                     bg=self.bg_color, fg="white").pack(pady=15)

        self.canvas = tk.Canvas(root, width=300, height=200, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack()

        self.base_x = 150
        self.base_y = 100

        if self.is_national_day:
            self.canvas.create_text(45, 45, text="★", font=("Arial", 28, "bold"), fill="#FFDE00")
            for sx, sy in [(85, 25), (100, 45), (95, 70), (75, 85)]:
                self.canvas.create_text(sx, sy, text="★", font=("Arial", 14, "bold"), fill="#FFDE00")

        self.face = self.canvas.create_oval(self.base_x-40, self.base_y-40,
                                            self.base_x+40, self.base_y+40,
                                            fill="#ffffff", outline="#333", width=3)
        self.ear_l = self.canvas.create_polygon(self.base_x-40, self.base_y-30,
                                                self.base_x-20, self.base_y-60,
                                                self.base_x, self.base_y-30,
                                                fill="#ffffff", outline="#333", width=3)
        self.ear_r = self.canvas.create_polygon(self.base_x, self.base_y-30,
                                                self.base_x+20, self.base_y-60,
                                                self.base_x+40, self.base_y-30,
                                                fill="#ffffff", outline="#333", width=3)
        self.eye_l = self.canvas.create_oval(self.base_x-20, self.base_y-15,
                                             self.base_x-8, self.base_y-3, fill="#333")
        self.eye_r = self.canvas.create_oval(self.base_x+8, self.base_y-15,
                                             self.base_x+20, self.base_y-3, fill="#333")
        self.mouth = self.canvas.create_arc(self.base_x-15, self.base_y+5,
                                            self.base_x+15, self.base_y+25,
                                            start=0, extent=180, style="arc", outline="#333", width=2)

        self.animating = True
        self.flash_state = False
        self.animate()
        self.root.after(5000, self.finish)

    def center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def animate(self):
        if not self.animating: return
        dx = random.randint(-6, 6)
        dy = random.randint(-6, 6)
        for item in [self.face, self.ear_l, self.ear_r, self.eye_l, self.eye_r, self.mouth]:
            self.canvas.move(item, dx, dy)
        self.flash_state = not self.flash_state
        if self.is_national_day:
            face_color = "#ffffff" if self.flash_state else "#FFDE00"
        else:
            face_color = "#ff8800" if self.flash_state else "#ffcc66"
        self.canvas.itemconfig(self.face, fill=face_color)
        self.canvas.itemconfig(self.ear_l, fill=face_color)
        self.canvas.itemconfig(self.ear_r, fill=face_color)
        self.root.after(50, self.animate)

    def finish(self):
        self.animating = False
        self.root.destroy()
        main_root = tk.Tk()
        app = CatCleanerApp(main_root)
        main_root.mainloop()

# ================= 主程序 =================
class CatCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"小猫安全中心 v{VERSION}")
        self.root.geometry("820x620")
        self.root.configure(bg="#ff8800")
        self.root.resizable(False, False)
        self.center_window(820, 620)

        self.shortcuts = load_shortcuts()
        self.error_logs = load_error_logs()
        self.cache_paths = load_cache_paths()

        tk.Label(root, text=f"🐱 小猫安全中心 v{VERSION}", font=("微软雅黑", 20, "bold"),
                 bg="#ff8800", fg="white").pack(pady=8)

        self.tab_frame = tk.Frame(root, bg="#ff8800")
        self.tab_frame.pack(fill="x", padx=20)

        for text, cmd in [
            ("清理垃圾", self.show_clean_tab),
            ("错误日志", self.show_error_tab),
            ("通用缓存路径", self.show_cache_tab),
            ("快捷文件夹", self.show_shortcut_tab),
            ("实用软件", self.show_tools_tab),
            ("装机工具", self.show_install_tab),
            ("CMD命令", self.show_cmd_tab),
        ]:
            tk.Button(self.tab_frame, text=text, font=("微软雅黑", 10, "bold"),
                      bg="#ffaa33", fg="white", relief="flat", padx=10, pady=5,
                      command=cmd).pack(side="left", padx=3)

        self.content_frame = tk.Frame(root, bg="#ff8800")
        self.content_frame.pack(fill="both", expand=True, padx=20, pady=8)

        self.status_label = tk.Label(root, text="准备就绪", font=("微软雅黑", 10),
                                     bg="#ff8800", fg="white")
        self.status_label.pack(side="bottom", pady=4)

        self.show_clean_tab()

    def center_window(self, w, h):
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def make_tree_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Cache.Treeview",
                        background="#000000", foreground="#00ff00",
                        fieldbackground="#000000", font=("Consolas", 9))
        style.map("Cache.Treeview",
                  background=[("selected", "#006600")],
                  foreground=[("selected", "#ffffff")])

    # ============ 清理垃圾 ============
    def show_clean_tab(self):
        self.clear_content()
        self.status_label.config(text="清理垃圾")

        self.size_label = tk.Label(self.content_frame, text="正在扫描垃圾...",
                                   font=("微软雅黑", 14, "bold"), bg="#ff8800", fg="white")
        self.size_label.pack(pady=10)

        self.log_text = tk.Text(self.content_frame, height=10, width=90,
                                font=("Consolas", 9), bg="#000000", fg="#00ff00")
        self.log_text.pack(pady=10)

        self.clean_btn = tk.Button(self.content_frame, text="🧹 一键清理", font=("微软雅黑", 14, "bold"),
                                   bg="#4CAF50", fg="white", padx=30, pady=10,
                                   command=self.start_clean)
        self.clean_btn.pack(pady=10)

        self.scan_size()

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.root.update()

    def scan_size(self):
        def task():
            total = 0
            for d in TARGET_DIRS:
                if d and os.path.exists(d):
                    total += get_size(d)
            self.size_label.config(text=f"可清理垃圾：{format_size(total)}")
        threading.Thread(target=task, daemon=True).start()

    def start_clean(self):
        self.clean_btn.config(state="disabled")
        self.status_label.config(text="正在清理...")
        threading.Thread(target=self.clean_task, daemon=True).start()

    def clean_task(self):
        total_deleted = 0
        total_freed = 0
        all_errors = []

        for d in TARGET_DIRS:
            if not d or not os.path.exists(d): continue
            self.log(f"📂 正在清理：{d}")
            deleted, freed, errors = clean_dir(d)
            total_deleted += deleted
            total_freed += freed
            all_errors.extend(errors)

        if all_errors:
            for e in all_errors:
                if e not in self.error_logs:
                    self.error_logs.append(e)
            save_error_logs(self.error_logs)

        self.clean_btn.config(state="normal")
        self.status_label.config(text="清理完成")

        self.log("=" * 40)
        self.log(f"🎉 清理完成！")
        self.log(f"📦 删除文件/文件夹：{total_deleted} 个")
        self.log(f"💾 释放空间：{format_size(total_freed)}")

        if all_errors:
            self.log(f"⚠️ 有 {len(all_errors)} 个文件清理失败，已记录到错误日志")
        else:
            messagebox.showinfo("小猫安全中心", f"清理完成！\n释放空间：{format_size(total_freed)}\n删除项目：{total_deleted} 个")

        self.scan_size()

    # ============ 错误日志 ============
    def show_error_tab(self):
        self.clear_content()
        self.status_label.config(text="错误日志")

        tk.Label(self.content_frame, text="清理失败的文件路径",
                 font=("微软雅黑", 14, "bold"), bg="#ff8800", fg="white").pack(pady=10)

        frame = tk.Frame(self.content_frame, bg="#ff8800")
        frame.pack(fill="both", expand=True)

        columns = ("path",)
        self.error_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12,
                                       style="Cache.Treeview")
        self.error_tree.heading("path", text="失败路径")
        self.error_tree.column("path", width=740, anchor="w")
        self.error_tree.pack(side="left", fill="both", expand=True)

        self.make_tree_style()
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.error_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.error_tree.config(yscrollcommand=scrollbar.set)

        for p in self.error_logs:
            self.error_tree.insert("", "end", values=(p,))

        btn_frame = tk.Frame(self.content_frame, bg="#ff8800")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="打开选中路径", font=("微软雅黑", 11, "bold"),
                  bg="#4CAF50", fg="white", padx=15, pady=6,
                  command=self.open_selected_error).pack(side="left", padx=5)

        tk.Button(btn_frame, text="清空日志", font=("微软雅黑", 11, "bold"),
                  bg="#e74c3c", fg="white", padx=15, pady=6,
                  command=self.clear_error_log).pack(side="left", padx=5)

    def open_selected_error(self):
        sel = self.error_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一条路径")
            return
        path = self.error_tree.item(sel[0])["values"][0]
        open_folder(path)

    def clear_error_log(self):
        msg = ("错误日志是用来记录清理失败的缓存文件，\n"
               "而错误日志本身也算是一个缓存文件，可以放心清除。\n\n"
               "确定清空错误日志吗？")
        if messagebox.askyesno("清空错误日志", msg):
            self.error_logs = []
            save_error_logs(self.error_logs)
            self.show_error_tab()

    # ============ 通用缓存路径 ============
    def show_cache_tab(self):
        self.clear_content()
        self.status_label.config(text="通用缓存路径")

        tk.Label(self.content_frame, text="常用缓存路径", font=("微软雅黑", 14, "bold"),
                 bg="#ff8800", fg="white").pack(pady=10)

        frame = tk.Frame(self.content_frame, bg="#ff8800")
        frame.pack(fill="both", expand=True)

        columns = ("name", "path", "action")
        self.cache_tree = ttk.Treeview(frame, columns=columns, show="headings", height=10,
                                       style="Cache.Treeview")
        self.cache_tree.heading("name", text="名称")
        self.cache_tree.heading("path", text="路径")
        self.cache_tree.heading("action", text="操作")
        self.cache_tree.column("name", width=150, anchor="w")
        self.cache_tree.column("path", width=520, anchor="w")
        self.cache_tree.column("action", width=80, anchor="center")
        self.cache_tree.pack(side="left", fill="both", expand=True)

        self.make_tree_style()
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.cache_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.cache_tree.config(yscrollcommand=scrollbar.set)

        for name, path in self.cache_paths:
            self.cache_tree.insert("", "end", values=(name, path, "双击打开"))

        self.cache_tree.bind("<Double-Button-1>", self.on_cache_double_click)

        tk.Label(self.content_frame, text="双击任意一行即可打开该路径",
                 font=("微软雅黑", 10), bg="#ff8800", fg="#ffe0b3").pack(pady=10)

    def on_cache_double_click(self, event):
        sel = self.cache_tree.selection()
        if not sel: return
        path = self.cache_tree.item(sel[0])["values"][1]
        if not os.path.exists(path):
            messagebox.showwarning("找不到该文件夹", f"找不到该文件夹：\n{path}")
            return
        open_folder(path)

    # ============ 快捷文件夹 ============
    def show_shortcut_tab(self):
        self.clear_content()
        self.status_label.config(text="快捷文件夹")

        tk.Label(self.content_frame, text="我的快捷文件夹", font=("微软雅黑", 14, "bold"),
                 bg="#ff8800", fg="white").pack(pady=10)

        frame = tk.Frame(self.content_frame, bg="#ff8800")
        frame.pack(fill="both", expand=True)

        self.shortcut_list = tk.Listbox(frame, font=("微软雅黑", 11), height=12,
                                        bg="#000000", fg="#00ff00", selectbackground="#006600")
        self.shortcut_list.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.shortcut_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.shortcut_list.config(yscrollcommand=scrollbar.set)

        self.refresh_shortcut_list()
        self.shortcut_list.bind("<Double-Button-1>", lambda e: self.open_selected_shortcut())

        btn_frame = tk.Frame(self.content_frame, bg="#ff8800")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="打开", font=("微软雅黑", 11, "bold"),
                  bg="#4CAF50", fg="white", padx=15, pady=6,
                  command=self.open_selected_shortcut).pack(side="left", padx=5)

        tk.Button(btn_frame, text="删除", font=("微软雅黑", 11, "bold"),
                  bg="#e74c3c", fg="white", padx=15, pady=6,
                  command=self.delete_shortcut).pack(side="left", padx=5)

        tk.Button(btn_frame, text="+ 添加自定义快捷方式", font=("微软雅黑", 11, "bold"),
                  bg="#2196F3", fg="white", padx=20, pady=6,
                  command=self.add_shortcut).pack(side="left", padx=5)

    def refresh_shortcut_list(self):
        self.shortcut_list.delete(0, tk.END)
        for s in self.shortcuts:
            self.shortcut_list.insert(tk.END, f"{s['name']}  |  {s['path']}")

    def open_selected_shortcut(self):
        sel = self.shortcut_list.curselection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个快捷方式")
            return
        idx = sel[0]
        open_folder(self.shortcuts[idx]["path"])

    def delete_shortcut(self):
        sel = self.shortcut_list.curselection()
        if not sel: return
        idx = sel[0]
        if messagebox.askyesno("确认", f"删除「{self.shortcuts[idx]['name']}」？"):
            del self.shortcuts[idx]
            save_shortcuts(self.shortcuts)
            self.refresh_shortcut_list()

    def add_shortcut(self):
        win = tk.Toplevel(self.root)
        win.title("添加快捷方式")
        win.geometry("500x220")
        win.configure(bg="#ff8800")
        win.resizable(False, False)

        tk.Label(win, text="名称：", font=("微软雅黑", 11), bg="#ff8800", fg="white").place(x=20, y=30)
        name_entry = tk.Entry(win, font=("微软雅黑", 11), width=30)
        name_entry.place(x=100, y=30)

        tk.Label(win, text="路径：", font=("微软雅黑", 11), bg="#ff8800", fg="white").place(x=20, y=80)
        path_entry = tk.Entry(win, font=("微软雅黑", 11), width=30)
        path_entry.place(x=100, y=80)

        def browse():
            p = filedialog.askdirectory(title="选择文件夹")
            if p:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, p)

        tk.Button(win, text="浏览", font=("微软雅黑", 10, "bold"),
                  bg="#2196F3", fg="white", padx=10, pady=3,
                  command=browse).place(x=380, y=78)

        def confirm():
            name = name_entry.get().strip()
            path = path_entry.get().strip()
            if not name:
                messagebox.showwarning("错误", "请输入名称")
                return
            if not path:
                messagebox.showwarning("错误", "请输入路径")
                return
            if not os.path.exists(path):
                messagebox.showwarning("找不到该文件夹", f"找不到该文件夹：\n{path}")
                return
            self.shortcuts.append({"name": name, "path": path})
            save_shortcuts(self.shortcuts)
            self.refresh_shortcut_list()
            win.destroy()

        tk.Button(win, text="确定", font=("微软雅黑", 11, "bold"),
                  bg="#4CAF50", fg="white", padx=20, pady=5,
                  command=confirm).place(x=150, y=150)

        tk.Button(win, text="取消", font=("微软雅黑", 11, "bold"),
                  bg="#e74c3c", fg="white", padx=20, pady=5,
                  command=win.destroy).place(x=280, y=150)

    # ============ 实用软件 ============
    def show_tools_tab(self):
        self.clear_content()
        self.status_label.config(text="实用软件")

        tk.Label(self.content_frame, text="常用软件官网", font=("微软雅黑", 14, "bold"),
                 bg="#ff8800", fg="white").pack(pady=10)

        tools = [
            ("Geek Uninstaller", "https://geekuninstaller.com/", False),
            ("ShareX", "https://getsharex.com/", False),
            ("Blender", "https://www.blender.org/", False),
            ("7-Zip", "https://www.7-zip.org/", False),
            ("VLC 播放器", "https://www.videolan.org/vlc/", False),
            ("Everything", "https://www.voidtools.com/", False),
            ("Notepad++", "https://notepad-plus-plus.org/", False),
            ("OBS Studio", "https://obsproject.com/", False),
            ("Git", "https://git-scm.com/", False),
            ("Scratch", "https://scratch.mit.edu/", True),
            ("GitHub", "https://github.com/", True),
            ("Visual Studio Code", "https://code.visualstudio.com/", False),
            ("Python", "https://www.python.org/", False),
            ("Node.js", "https://nodejs.org/", False),
        ]

        frame = tk.Frame(self.content_frame, bg="#ff8800")
        frame.pack(fill="both", expand=True)

        columns = ("name", "url", "tip")
        self.tools_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12,
                                       style="Cache.Treeview")
        self.tools_tree.heading("name", text="软件名称")
        self.tools_tree.heading("url", text="官网链接")
        self.tools_tree.heading("tip", text="提示")
        self.tools_tree.column("name", width=180, anchor="w")
        self.tools_tree.column("url", width=380, anchor="w")
        self.tools_tree.column("tip", width=160, anchor="center")
        self.tools_tree.pack(side="left", fill="both", expand=True)

        self.make_tree_style()
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.tools_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tools_tree.config(yscrollcommand=scrollbar.set)

        for name, url, need_vpn in tools:
            tip = "⚠ 需加速器" if need_vpn else ""
            self.tools_tree.insert("", "end", values=(name, url, tip))

        self.tools_tree.bind("<Double-Button-1>", lambda e: self.open_selected_tool())

        tk.Button(self.content_frame, text="打开选中官网", font=("微软雅黑", 11, "bold"),
                  bg="#4CAF50", fg="white", padx=15, pady=6,
                  command=self.open_selected_tool).pack(pady=8)

    def open_selected_tool(self):
        sel = self.tools_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个软件")
            return
        values = self.tools_tree.item(sel[0])["values"]
        name, url, tip = values[0], values[1], values[2]
        if tip and "需加速" in tip:
            msg = (f"「{name}」的官网在国内可能无法直接访问。\n\n"
                   f"建议使用加速器（如 Watt Toolkit）\n\n"
                   f"是否仍然尝试打开官网？")
            if not messagebox.askyesno("需要加速器", msg):
                return
        webbrowser.open(url)

    # ============ 装机工具 ============
    def show_install_tab(self):
        self.clear_content()
        self.status_label.config(text="装机工具")

        tk.Label(self.content_frame, text="系统镜像下载", font=("微软雅黑", 14, "bold"),
                 bg="#ff8800", fg="white").pack(pady=10)

        installs = [
            ("Windows 11 官方下载", "https://www.microsoft.com/zh-cn/software-download/windows11"),
            ("Windows 10 官方下载", "https://www.microsoft.com/zh-cn/software-download/windows10"),
            ("Windows 10 更新助手", "https://www.microsoft.com/zh-cn/software-download/windows10"),
            ("Windows 11 安装助手", "https://www.microsoft.com/zh-cn/software-download/windows11"),
            ("Media Creation Tool", "https://www.microsoft.com/zh-cn/software-download/windows10"),
            ("Windows 11 企业版", "https://www.microsoft.com/zh-cn/evalcenter/download-windows-11-enterprise"),
            ("Windows Server 2022", "https://www.microsoft.com/zh-cn/evalcenter/download-windows-server-2022"),
            ("Visual Studio 社区版", "https://visualstudio.microsoft.com/zh-hans/downloads/"),
        ]

        frame = tk.Frame(self.content_frame, bg="#ff8800")
        frame.pack(fill="both", expand=True)

        columns = ("name", "url")
        self.install_tree = ttk.Treeview(frame, columns=columns, show="headings", height=12,
                                         style="Cache.Treeview")
        self.install_tree.heading("name", text="工具名称")
        self.install_tree.heading("url", text="下载页面（双击打开）")
        self.install_tree.column("name", width=240, anchor="w")
        self.install_tree.column("url", width=480, anchor="w")
        self.install_tree.pack(side="left", fill="both", expand=True)

        self.make_tree_style()
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.install_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.install_tree.config(yscrollcommand=scrollbar.set)

        for name, url in installs:
            self.install_tree.insert("", "end", values=(name, url))

        self.install_tree.bind("<Double-Button-1>", lambda e: self.open_selected_install())

        tk.Button(self.content_frame, text="打开选中下载页", font=("微软雅黑", 11, "bold"),
                  bg="#4CAF50", fg="white", padx=15, pady=6,
                  command=self.open_selected_install).pack(pady=8)

    def open_selected_install(self):
        sel = self.install_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一个工具")
            return
        url = self.install_tree.item(sel[0])["values"][1]
        webbrowser.open(url)

    # ============ CMD命令 ============
    def show_cmd_tab(self):
        self.clear_content()
        self.status_label.config(text="CMD命令")

        tk.Label(self.content_frame, text="实用 / 好玩的 CMD 命令",
                 font=("微软雅黑", 14, "bold"), bg="#ff8800", fg="white").pack(pady=10)

        cmds = [
            ("实用", "sfc /scannow", "扫描并修复系统文件", True),
            ("实用", "chkdsk C: /f /r", "检查并修复 C 盘磁盘错误", True),
            ("实用", "DISM /Online /Cleanup-Image /RestoreHealth", "修复系统映像", True),
            ("实用", "ipconfig /flushdns", "刷新 DNS 缓存", False),
            ("实用", "ipconfig /all", "查看完整网络配置", False),
            ("实用", "netstat -ano", "查看所有网络连接和端口", False),
            ("实用", "tasklist", "列出所有运行中的进程", False),
            ("实用", "powercfg /batteryreport", "生成电池使用报告", False),
            ("好玩", "color 0a", "黑底绿字（黑客风）", False),
            ("好玩", "color 4f", "红底白字", False),
            ("好玩", "tree", "以树状图显示当前目录结构", False),
            ("好玩", "dir C:\\ /s", "列出整个 C 盘所有文件", False),
            ("好玩", "telnet towel.blinkenlights.nl", "星球大战 ASCII 动画", False),
            ("好玩", "curl ascii.live/forrest", "阿甘正传跑步", False),
            ("好玩", "curl parrot.live", "跳舞鹦鹉", False),
            ("好玩", "curl wttr.in", "在终端查天气", False),
        ]

        frame = tk.Frame(self.content_frame, bg="#ff8800")
        frame.pack(fill="both", expand=True)

        columns = ("type", "cmd", "desc", "admin")
        self.cmd_tree = ttk.Treeview(frame, columns=columns, show="headings", height=14,
                                     style="Cache.Treeview")
        self.cmd_tree.heading("type", text="分类")
        self.cmd_tree.heading("cmd", text="命令")
        self.cmd_tree.heading("desc", text="说明")
        self.cmd_tree.heading("admin", text="权限")
        self.cmd_tree.column("type", width=60, anchor="center")
        self.cmd_tree.column("cmd", width=340, anchor="w")
        self.cmd_tree.column("desc", width=260, anchor="w")
        self.cmd_tree.column("admin", width=110, anchor="center")
        self.cmd_tree.pack(side="left", fill="both", expand=True)

        self.make_tree_style()
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.cmd_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.cmd_tree.config(yscrollcommand=scrollbar.set)

        for t, c, d, need_admin in cmds:
            self.cmd_tree.insert("", "end",
                                 values=(t, c, d, "⚠ 需要管理员" if need_admin else "普通"))

        self.cmd_tree.bind("<Double-Button-1>", self.copy_cmd)

        tk.Button(self.content_frame, text="复制选中命令", font=("微软雅黑", 11, "bold"),
                  bg="#2196F3", fg="white", padx=15, pady=6,
                  command=self.copy_cmd).pack(pady=8)

    def copy_cmd(self, event=None):
        sel = self.cmd_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选择一条命令")
            return
        cmd = self.cmd_tree.item(sel[0])["values"][1]
        self.root.clipboard_clear()
        self.root.clipboard_append(cmd)
        messagebox.showinfo("已复制", f"命令已复制到剪贴板：\n{cmd}")

# ================= 启动 =================
if __name__ == "__main__":

    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()

        def print_green(msg):
            print(f"\033[92m{msg}\033[0m")

        def print_red(msg):
            print(f"\033[91m{msg}\033[0m")

        if cmd == "clean":
            print_green(f"🐱 小猫安全中心 v{VERSION} - 命令行清理模式")
            print("-" * 40)
            total_deleted = 0
            total_freed = 0
            all_errors = []
            for d in TARGET_DIRS:
                if not d or not os.path.exists(d):
                    continue
                print(f"📂 正在清理：{d}")
                try:
                    deleted, freed, errors = clean_dir(d)
                    total_deleted += deleted
                    total_freed += freed
                    all_errors.extend(errors)
                    print_green(f"   已删除 {deleted} 个文件")
                except Exception as e:
                    print_red(f"   清理失败：{e}")
            if all_errors:
                existing = load_error_logs()
                for e in all_errors:
                    if e not in existing:
                        existing.append(e)
                save_error_logs(existing)
                print_red(f"\n⚠️ 有 {len(all_errors)} 个文件清理失败，已记录到 error_log.txt")
            print("-" * 40)
            print_green(f"✅ 清理完成！")
            print(f"📦 删除项目：{total_deleted} 个")
            print(f"💾 释放空间：{format_size(total_freed)}")
            input("按回车退出...")
            sys.exit(0)

        elif cmd == "create":
            if len(sys.argv) < 4:
                print_red("用法：小猫安全中心.exe create [名称] [路径]")
                sys.exit(1)
            name = sys.argv[2]
            path = sys.argv[3]
            if not os.path.exists(path):
                print_red(f"❌ 找不到该文件夹：{path}")
                sys.exit(1)
            shortcuts = load_shortcuts()
            for s in shortcuts:
                if s["name"] == name:
                    print_red(f"⚠️ 快捷方式「{name}」已存在")
                    sys.exit(1)
            shortcuts.append({"name": name, "path": path})
            save_shortcuts(shortcuts)
            print_green(f"✅ 已创建快捷方式：{name}")
            print(f"   路径：{path}")
            sys.exit(0)

        elif cmd == "open":
            shortcuts = load_shortcuts()
            if len(sys.argv) < 3:
                if not shortcuts:
                    print("暂无快捷方式")
                else:
                    print("当前快捷方式：")
                    for i, s in enumerate(shortcuts, 1):
                        print(f"  {i}. {s['name']}  |  {s['path']}")
                sys.exit(0)
            name = sys.argv[2]
            matches = [s for s in shortcuts if s["name"] == name]
            if not matches:
                print_red(f"❌ 找不到快捷方式：{name}")
                sys.exit(1)
            if len(matches) == 1:
                path = matches[0]["path"]
                print_green(f"✅ 正在打开：{path}")
                os.startfile(path)
                sys.exit(0)
            print_red(f"⚠️ 发现 {len(matches)} 个重名的快捷方式：")
            for i, s in enumerate(matches, 1):
                print(f"  {i}. {s['path']}")
            print("请输入编号选择：")
            try:
                choice = input().strip()
                idx = int(choice) - 1
                if idx < 0 or idx >= len(matches):
                    print_red("❌ 无效编号")
                    sys.exit(1)
                path = matches[idx]["path"]
                print_green(f"✅ 正在打开：{path}")
                os.startfile(path)
            except ValueError:
                print_red("❌ 请输入数字")
                sys.exit(1)
            sys.exit(0)

        elif cmd == "list":
            shortcuts = load_shortcuts()
            if not shortcuts:
                print("暂无快捷方式")
            else:
                print("当前快捷方式：")
                for i, s in enumerate(shortcuts, 1):
                    print(f"  {i}. {s['name']}  |  {s['path']}")
            sys.exit(0)

        elif cmd == "remove":
            if len(sys.argv) < 3:
                print_red("用法：小猫安全中心.exe remove [名称]")
                sys.exit(1)
            name = sys.argv[2]
            shortcuts = load_shortcuts()
            new_shortcuts = [s for s in shortcuts if s["name"] != name]
            if len(new_shortcuts) == len(shortcuts):
                print_red(f"❌ 找不到快捷方式：{name}")
            else:
                save_shortcuts(new_shortcuts)
                print_green(f"✅ 已删除快捷方式：{name}")
            sys.exit(0)

        elif cmd == "help":
            print(f"小猫安全中心 v{VERSION} - 命令行用法：")
            print("  小猫安全中心.exe                     启动图形界面")
            print("  小猫安全中心.exe clean               清理缓存")
            print("  小猫安全中心.exe create [名称] [路径]  创建快捷方式")
            print("  小猫安全中心.exe open [名称]         打开快捷方式")
            print("  小猫安全中心.exe list                列出所有快捷方式")
            print("  小猫安全中心.exe remove [名称]       删除快捷方式")
            print("  小猫安全中心.exe help                显示帮助")
            print("  小猫安全中心.exe about               显示版本")
            sys.exit(0)

        elif cmd == "about":
            print(f"小猫安全中心 v{VERSION}")
            print("一个安静、免费、有猫的系统工具")
            print("GitHub: https://github.com/Anhui-gb")
            sys.exit(0)

        else:
            print(f"未知命令：{cmd}")
            print("输入 小猫安全中心.exe help 查看帮助")
            sys.exit(1)

    # ===== 图形界面模式 =====
    notice = tk.Tk()
    notice.title("公告 - 1.2 版本")
    notice.geometry("440x250")
    notice.configure(bg="#ff8800")
    notice.resizable(False, False)
    notice.update_idletasks()
    sw = notice.winfo_screenwidth()
    sh = notice.winfo_screenheight()
    x = (sw - 440) // 2
    y = (sh - 250) // 2
    notice.geometry(f"440x250+{x}+{y}")

    tk.Label(notice, text="🎉 小猫安全中心 v1.2 更新", font=("微软雅黑", 14, "bold"),
             bg="#ff8800", fg="white").pack(pady=10)
    tk.Label(notice,
             text="本次更新：\n"
                  "CMD 模式无需打开界面即可执行\n"
                  "支持命令：clean / create / open / list / remove\n"
                  "open 支持重名选择\n\n"
                  "输入 小猫安全中心.exe help 查看用法",
             font=("微软雅黑", 10), bg="#ff8800", fg="white", justify="left").pack(pady=5)
    tk.Button(notice, text="知道了", font=("微软雅黑", 11, "bold"),
              bg="#4CAF50", fg="white", padx=20, pady=5,
              command=notice.destroy).pack(pady=10)
    notice.mainloop()

    root = tk.Tk()
    splash = SplashScreen(root)
    root.mainloop()