import tkinter as tk
import random
from tkinter import font
import json
import os

class WordReminder:
    def __init__(self):
        # 初始化历史记录相关变量（移到最前面）
        self.word_history = []  # 存储显示过的单词历史
        self.current_index = -1  # 当前显示的单词索引
        
        # 读取单词文件
        self.words = {}
        with open('words.txt', 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('=')
                if len(parts) == 4:
                    self.words[parts[0]] = {
                        'meaning': parts[1],
                        'example': parts[2],
                        'translation': parts[3]
                    }
        
        # 创建主窗口
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        
        # 设置为桌面级别窗口
        try:
            import win32gui
            import win32con
            import win32api
            
            # 获取窗口句柄
            hwnd = self.root.winfo_id()
            
            # 设置窗口扩展样式
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            style = style | win32con.WS_EX_NOACTIVATE  # 禁止窗口激活
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
            
            # 获取桌面窗口
            defview = win32gui.FindWindowEx(0, 0, "Progman", None)
            defview = win32gui.FindWindowEx(defview, 0, "SHELLDLL_DefView", None)
            
            # 设置窗口位置在桌面图标之后
            if defview:
                win32gui.SetWindowPos(
                    hwnd,
                    win32gui.GetWindow(defview, win32con.GW_HWNDNEXT),
                    0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE
                )
            
        except ImportError:
            print("请安装 pywin32: pip install pywin32")
        
        self.root.attributes('-alpha', 0.85)  # 调整透明度
        
        # 加载上次窗口位置
        self.load_position()
        
        # 创建半透明磨砂效果的框架
        self.frame = tk.Frame(
            self.root,
            bg='#ffffff',  # 白色背景
        )
        self.frame.pack(expand=True, fill='both')
        
        # 创建标签
        self.word_label = tk.Label(
            self.frame,
            text="",
            font=font.Font(family="Times New Roman", size=16, weight="bold"),
            padx=10,
            pady=5,
            bg='#ffffff',
            fg='#333333'
        )
        self.word_label.pack()
        
        self.meaning_label = tk.Label(
            self.frame,
            text="",
            font=font.Font(family="Microsoft YaHei", size=12),
            padx=10,
            pady=5,
            bg='#ffffff',
            fg='#666666'
        )
        self.meaning_label.pack()
        
        self.example_label = tk.Label(
            self.frame,
            text="",
            font=font.Font(family="Times New Roman", size=12, slant="italic"),
            padx=10,
            pady=5,
            wraplength=280,
            bg='#ffffff',
            fg='#333333'
        )
        self.example_label.pack()
        
        self.translation_label = tk.Label(
            self.frame,
            text="",
            font=font.Font(family="Microsoft YaHei", size=12),
            padx=10,
            pady=5,
            wraplength=280,
            bg='#ffffff',
            fg='#666666'
        )
        self.translation_label.pack()
        
        # 添加磨砂效果
        self.frame.bind('<Map>', self.add_blur)
        
        # 绑定鼠标事件
        self.frame.bind('<Button-1>', self.start_move)
        self.frame.bind('<B1-Motion>', self.on_move)
        self.frame.bind('<ButtonRelease-1>', self.stop_move)
        
        # 添加关闭按钮
        close_btn = tk.Label(
            self.frame,
            text="×",
            font=font.Font(size=12),
            bg='#ffffff',
            fg='#666666'
        )
        close_btn.place(x=270, y=5)
        close_btn.bind('<Button-1>', lambda e: self.root.withdraw())
        
        self.is_moving = False
        self.x = 0
        self.y = 0
        
        # 在创建关闭按钮后添加导航按钮
        # 添加按钮框架
        button_frame = tk.Frame(
            self.frame,
            bg='#ffffff'
        )
        button_frame.pack(pady=5)
        
        # 上一个按钮
        prev_btn = tk.Label(
            button_frame,
            text="◀",
            font=font.Font(size=16),  # 增大字体
            bg='#ffffff',
            fg='#666666',
            padx=15,  # 增加内边距
            pady=5
        )
        prev_btn.pack(side=tk.LEFT, padx=5)  # 增加按钮间距
        prev_btn.bind('<Button-1>', lambda e: self.show_prev_word())
        
        # 下一个按钮
        next_btn = tk.Label(
            button_frame,
            text="▶",
            font=font.Font(size=16),  # 增大字体
            bg='#ffffff',
            fg='#666666',
            padx=15,  # 增加内边距
            pady=5
        )
        next_btn.pack(side=tk.LEFT, padx=5)  # 增加按钮间距
        next_btn.bind('<Button-1>', lambda e: self.show_next_word())
        
        # 添加锁定按钮
        self.lock_btn = tk.Label(
            button_frame,
            text="🔓",  # 未锁定状态
            font=font.Font(size=16),
            bg='#ffffff',
            fg='#666666',
            padx=15,
            pady=5
        )
        self.lock_btn.pack(side=tk.LEFT, padx=5)
        self.lock_btn.bind('<Button-1>', self.toggle_lock)
        
        # 开始显示单词
        self.show_word()
    
    def add_blur(self, event=None):
        # 在Windows上添加磨砂效果
        try:
            from ctypes import windll, c_int, byref
            hwnd = self.root.winfo_id()
            blur_value = 1  # 磨砂程度
            windll.dwmapi.DwmSetWindowAttribute(
                hwnd,
                20,  # DWMWA_BLUR_BEHIND
                byref(c_int(blur_value)),
                4
            )
        except:
            pass
    
    def start_move(self, event):
        # 修改移动方法，增加锁定检查
        if not self.is_locked:
            self.is_moving = True
            self.x = event.x
            self.y = event.y
    
    def on_move(self, event):
        if self.is_moving:
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
    
    def stop_move(self, event):
        self.is_moving = False
        self.save_position()
    
    def save_position(self):
        position = {
            'x': self.root.winfo_x(),
            'y': self.root.winfo_y()
        }
        with open('position.json', 'w') as f:
            json.dump(position, f)
    
    def load_position(self):
        try:
            with open('position.json', 'r') as f:
                position = json.load(f)
                self.root.geometry(f"300x200+{position['x']}+{position['y']}")
        except:
            # 默认位置为屏幕中央
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            x = (screen_width - 300) // 2
            y = (screen_height - 200) // 2
            self.root.geometry(f"300x200+{x}+{y}")
    
    def show_prev_word(self):
        if self.current_index > 0:
            self.current_index -= 1
            word = self.word_history[self.current_index]
            self.update_word_display(word)
    
    def show_next_word(self):
        if self.current_index < len(self.word_history) - 1:
            # 显示历史中的下一个单词
            self.current_index += 1
            word = self.word_history[self.current_index]
        else:
            # 显示新的随机单词
            word = random.choice(list(self.words.keys()))
            self.word_history.append(word)
            self.current_index += 1
        self.update_word_display(word)
    
    def update_word_display(self, word):
        data = self.words[word]
        self.word_label.config(text=word)
        self.meaning_label.config(text=data['meaning'])
        self.example_label.config(text=data['example'])
        self.translation_label.config(text=data['translation'])
    
    def show_word(self):
        self.show_next_word()  # 使用show_next_word来显示新单词
        # 15分钟后再次显示
        self.root.after(900000, self.show_word)
    
    def run(self):
        self.root.mainloop()
    
    # 添加锁定切换方法
    def toggle_lock(self, event=None):
        self.is_locked = not self.is_locked
        if self.is_locked:
            self.lock_btn.config(text="🔒")  # 锁定状态
            # 解绑移动事件
            self.frame.unbind('<Button-1>')
            self.frame.unbind('<B1-Motion>')
            self.frame.unbind('<ButtonRelease-1>')
        else:
            self.lock_btn.config(text="🔓")  # 未锁定状态
            # 重新绑定移动事件
            self.frame.bind('<Button-1>', self.start_move)
            self.frame.bind('<B1-Motion>', self.on_move)
            self.frame.bind('<ButtonRelease-1>', self.stop_move)

if __name__ == '__main__':
    app = WordReminder()
    app.run() 