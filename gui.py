import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import queue
import logging

from config import load_config, save_config
from searcher import SearchEngine

logger = logging.getLogger(__name__)

# Цветовая схема
BG_COLOR = "#1e1e1e"
SURFACE_COLOR = "#2d2d2d"
FG_COLOR = "#e0e0e0"
ACCENT_COLOR = "#007acc"
ACCENT_HOVER = "#1a8cff"
ENTRY_BG = "#3c3c3c"
ENTRY_FG = "#ffffff"
LISTBOX_BG = "#252525"
LISTBOX_FG = "#e0e0e0"
BUTTON_BG = "#333333"
BUTTON_FG = "#ffffff"
BUTTON_ACTIVE_BG = ACCENT_COLOR
BUTTON_ACTIVE_FG = "#ffffff"
DISABLED_BG = "#555555"
TREE_BG = "#252525"
TREE_FG = "#e0e0e0"
TREE_SELECTED = "#094771"
HEADER_BG = "#2d2d2d"
HEADER_FG = "#ffffff"
LIQUID_COLOR = "#ffd700"  # золотой для ликвидных

class RoundedButton(tk.Canvas):
    """
    Кастомная кнопка с скругленными углами и плавной анимацией при наведении.
    """
    def __init__(self, parent, text, command=None, width=140, height=50,
                 corner_radius=15, bg=BUTTON_BG, fg=BUTTON_FG,
                 active_bg=BUTTON_ACTIVE_BG, active_fg=BUTTON_ACTIVE_FG,
                 font=('Segoe UI', 11, 'bold'), *args, **kwargs):
        super().__init__(parent, width=width, height=height, bg=BG_COLOR,
                         highlightthickness=0, *args, **kwargs)
        self.text = text
        self.command = command
        self.corner_radius = corner_radius
        self.bg = bg
        self.fg = fg
        self.active_bg = active_bg
        self.active_fg = active_fg
        self.font = font
        self.width = width
        self.height = height

        self.scale = 1.0
        self.target_scale = 1.0
        self.hovered = False
        self.enabled = True

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self._draw()

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            self.hovered = False
            self.target_scale = 1.0
            self.scale = 1.0
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.width * self.scale
        h = self.height * self.scale
        x0 = (self.width - w) / 2
        y0 = (self.height - h) / 2
        x1 = x0 + w
        y1 = y0 + h

        if not self.enabled:
            bg = DISABLED_BG
            fg = "#888888"
        else:
            bg = self.active_bg if self.hovered else self.bg
            fg = self.active_fg if self.hovered else self.fg

        r = self.corner_radius * self.scale
        self._create_round_rect(x0, y0, x1, y1, r, fill=bg, outline=bg)
        font_size = int(self.font[1] * self.scale)
        font = (self.font[0], font_size) + tuple(self.font[2:])
        self.create_text(self.width/2, self.height/2, text=self.text,
                         fill=fg, font=font)

    def _create_round_rect(self, x0, y0, x1, y1, r, **kwargs):
        points = [
            x0+r, y0,
            x1-r, y0,
            x1, y0,
            x1, y0+r,
            x1, y1-r,
            x1, y1,
            x1-r, y1,
            x0+r, y1,
            x0, y1,
            x0, y1-r,
            x0, y0+r,
            x0, y0
        ]
        self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, event):
        if self.enabled:
            self.hovered = True
            self.target_scale = 1.08
            self._animate()

    def on_leave(self, event):
        self.hovered = False
        self.target_scale = 1.0
        self._animate()

    def on_click(self, event):
        if self.enabled and self.command:
            self.command()

    def _animate(self):
        diff = self.target_scale - self.scale
        if abs(diff) < 0.001:
            self.scale = self.target_scale
            self._draw()
            return
        step = 0.015 if diff > 0 else -0.015
        self.scale += step
        self._draw()
        self.after(10, self._animate)


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Telegram Username Finder")
        self.root.geometry("1000x650")
        self.root.configure(bg=BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.queue = queue.Queue()

        self.api_id_var = tk.StringVar()
        self.api_hash_var = tk.StringVar()
        self.length_var = tk.IntVar(value=8)
        self.allow_digits_var = tk.BooleanVar(value=False)
        self.allow_uppercase_var = tk.BooleanVar(value=False)

        self.free_list = []
        self.deleted_list = []
        self.liquid_free_list = []  # список ликвидных свободных

        self.search_thread = None

        self._setup_styles()
        self._create_widgets()
        self._load_config_to_ui()

        self.root.after(100, self._process_queue)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('.', background=BG_COLOR, foreground=FG_COLOR,
                        fieldbackground=ENTRY_BG, bordercolor="#555555",
                        lightcolor=BG_COLOR, darkcolor=BG_COLOR)
        style.configure('TFrame', background=BG_COLOR)
        style.configure('TLabel', background=BG_COLOR, foreground=FG_COLOR, font=('Segoe UI', 10))
        style.configure('TLabelframe', background=BG_COLOR, foreground=FG_COLOR,
                        bordercolor="#555555", relief=tk.FLAT)
        style.configure('TLabelframe.Label', background=BG_COLOR, foreground=FG_COLOR,
                        font=('Segoe UI', 10, 'bold'))
        style.configure('TEntry', fieldbackground=ENTRY_BG, foreground=ENTRY_FG,
                        insertcolor=FG_COLOR, bordercolor="#555555")
        style.configure('TCheckbutton', background=BG_COLOR, foreground=FG_COLOR,
                        font=('Segoe UI', 10))
        style.map('TCheckbutton',
                  background=[('active', BG_COLOR)],
                  foreground=[('active', FG_COLOR)])
        style.configure('Horizontal.TScale', background=BG_COLOR, troughcolor=ENTRY_BG,
                        bordercolor=BG_COLOR, lightcolor=ACCENT_COLOR, darkcolor=ACCENT_COLOR)

        style.configure('Treeview', background=TREE_BG, fieldbackground=TREE_BG,
                        foreground=TREE_FG, bordercolor="#555555", rowheight=25)
        style.map('Treeview', background=[('selected', TREE_SELECTED)])
        style.configure('Treeview.Heading', background=HEADER_BG, foreground=HEADER_FG,
                        font=('Segoe UI', 10, 'bold'))

    def _create_widgets(self):
        # Верхняя панель с заголовком
        header_frame = tk.Frame(self.root, bg=BG_COLOR)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(header_frame, text="Telegram Username Finder", font=('Segoe UI', 16, 'bold'),
                 bg=BG_COLOR, fg=ACCENT_COLOR).pack(side=tk.LEFT)

        # Основной контейнер
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Левая панель: настройки
        settings_frame = ttk.Frame(main_paned, width=280)
        main_paned.add(settings_frame, weight=0)

        ttk.Label(settings_frame, text="Настройки", font=('Segoe UI', 12, 'bold')).pack(pady=(5, 10))

        ttk.Label(settings_frame, text="API ID:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        ttk.Entry(settings_frame, textvariable=self.api_id_var).pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(settings_frame, text="API Hash:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        ttk.Entry(settings_frame, textvariable=self.api_hash_var).pack(fill=tk.X, padx=5, pady=(0, 5))

        ttk.Label(settings_frame, text="Длина username:").pack(anchor=tk.W, padx=5, pady=(5, 0))
        length_frame = ttk.Frame(settings_frame)
        length_frame.pack(fill=tk.X, padx=5, pady=5)
        length_scale = ttk.Scale(length_frame, from_=5, to=32, orient=tk.HORIZONTAL,
                                 variable=self.length_var, command=self._on_scale_change)
        length_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.length_value_label = ttk.Label(length_frame, text=str(self.length_var.get()), width=3)
        self.length_value_label.pack(side=tk.RIGHT, padx=(5, 0))

        ttk.Checkbutton(settings_frame, text="Разрешить цифры",
                        variable=self.allow_digits_var).pack(anchor=tk.W, padx=5, pady=5)
        ttk.Checkbutton(settings_frame, text="Разрешить заглавные буквы",
                        variable=self.allow_uppercase_var).pack(anchor=tk.W, padx=5, pady=5)

        buttons_frame = ttk.Frame(settings_frame)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)

        self.start_button = RoundedButton(buttons_frame, text="Старт", command=self.start_search,
                                          width=140, height=50, corner_radius=15,
                                          bg=ACCENT_COLOR, fg=BUTTON_FG,
                                          active_bg=ACCENT_HOVER, active_fg=BUTTON_FG,
                                          font=('Segoe UI', 12, 'bold'))
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        self.stop_button = RoundedButton(buttons_frame, text="Стоп", command=self.stop_search,
                                         width=140, height=50, corner_radius=15,
                                         bg=BUTTON_BG, fg=BUTTON_FG,
                                         active_bg="#666666", active_fg=BUTTON_FG,
                                         font=('Segoe UI', 12, 'bold'))
        self.stop_button.pack(side=tk.LEFT)

        self.save_button = RoundedButton(settings_frame, text="Сохранить свободные",
                                         command=self.save_results,
                                         width=220, height=50, corner_radius=15,
                                         bg=BUTTON_BG, fg=BUTTON_FG,
                                         active_bg="#666666", active_fg=BUTTON_FG,
                                         font=('Segoe UI', 11, 'bold'))
        self.save_button.pack(fill=tk.X, pady=10)

        self.status_short_var = tk.StringVar(value="Готов")
        tk.Label(settings_frame, textvariable=self.status_short_var,
                 bg=BG_COLOR, fg="#aaaaaa", font=('Segoe UI', 9)).pack(anchor=tk.W, padx=5, pady=5)

        # Правая панель: результаты в виде таблицы
        results_frame = ttk.Frame(main_paned)
        main_paned.add(results_frame, weight=1)

        ttk.Label(results_frame, text="Результаты", font=('Segoe UI', 12, 'bold')).pack(pady=(0, 5))

        table_frame = ttk.Frame(results_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('username', 'status', 'liquid')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', selectmode='browse')
        self.tree.heading('username', text='Username')
        self.tree.heading('status', text='Status')
        self.tree.heading('liquid', text='Ликвидный')
        self.tree.column('username', width=180, anchor=tk.W)
        self.tree.column('status', width=150, anchor=tk.W)
        self.tree.column('liquid', width=90, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        counters_frame = ttk.Frame(results_frame)
        counters_frame.pack(fill=tk.X, pady=5)
        self.free_count_var = tk.StringVar(value="Свободных: 0")
        self.deleted_count_var = tk.StringVar(value="Удалённых: 0")
        self.liquid_count_var = tk.StringVar(value="Ликвидных свободных: 0")
        ttk.Label(counters_frame, textvariable=self.free_count_var,
                  foreground="#4caf50").pack(side=tk.LEFT, padx=5)
        ttk.Label(counters_frame, textvariable=self.deleted_count_var,
                  foreground="#ff9800").pack(side=tk.LEFT, padx=5)
        ttk.Label(counters_frame, textvariable=self.liquid_count_var,
                  foreground=LIQUID_COLOR).pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bg=SURFACE_COLOR,
                              fg=FG_COLOR, anchor=tk.W, padx=10, pady=5, font=('Segoe UI', 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _on_scale_change(self, value):
        self.length_value_label.config(text=str(int(float(value))))

    def _load_config_to_ui(self):
        config = load_config()
        if config:
            self.api_id_var.set(str(config.get('api_id', '')))
            self.api_hash_var.set(config.get('api_hash', ''))
            self.length_var.set(config.get('default_length', 8))
            self.allow_digits_var.set(config.get('allow_digits', False))
            self.allow_uppercase_var.set(config.get('allow_uppercase', False))

    def _save_current_config(self):
        config = {
            'api_id': int(self.api_id_var.get()) if self.api_id_var.get().isdigit() else 0,
            'api_hash': self.api_hash_var.get(),
            'default_length': self.length_var.get(),
            'allow_digits': self.allow_digits_var.get(),
            'allow_uppercase': self.allow_uppercase_var.get()
        }
        save_config(config)

    def _validate_inputs(self):
        api_id = self.api_id_var.get().strip()
        api_hash = self.api_hash_var.get().strip()
        if not api_id.isdigit():
            messagebox.showerror("Ошибка", "API ID должен быть числом")
            return False
        if not api_hash:
            messagebox.showerror("Ошибка", "Введите API Hash")
            return False
        return True

    def start_search(self):
        if self.search_thread and self.search_thread.is_alive():
            messagebox.showwarning("Поиск уже идёт", "Дождитесь завершения текущего поиска или остановите его.")
            return
        if not self._validate_inputs():
            return

        self._save_current_config()

        params = {
            'length': self.length_var.get(),
            'allow_digits': self.allow_digits_var.get(),
            'allow_uppercase': self.allow_uppercase_var.get()
        }
        api_id = int(self.api_id_var.get())
        api_hash = self.api_hash_var.get()

        for item in self.tree.get_children():
            self.tree.delete(item)
        self.free_list.clear()
        self.deleted_list.clear()
        self.liquid_free_list.clear()
        self.free_count_var.set("Свободных: 0")
        self.deleted_count_var.set("Удалённых: 0")
        self.liquid_count_var.set("Ликвидных свободных: 0")

        self.start_button.set_enabled(False)
        self.stop_button.set_enabled(True)
        self.status_var.set("Подключение...")
        self.status_short_var.set("Подключение...")

        self.search_thread = SearchEngine(
            api_id=api_id,
            api_hash=api_hash,
            params=params,
            on_result=self._on_result,
            on_status=self._on_status,
            on_error=self._on_error
        )
        self.search_thread.start()

    def stop_search(self):
        if self.search_thread and self.search_thread.is_alive():
            self.search_thread.stop()
            self.status_var.set("Остановка...")
            self.status_short_var.set("Остановка...")
        self.start_button.set_enabled(True)
        self.stop_button.set_enabled(False)

    def _on_result(self, username, status, is_liquid):
        self.queue.put(('result', username, status, is_liquid))

    def _on_status(self, message):
        self.queue.put(('status', message))

    def _on_error(self, message):
        self.queue.put(('error', message))

    def _process_queue(self):
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == 'result':
                    _, username, status, is_liquid = msg
                    if status == 'free':
                        liquid_text = "Да" if is_liquid else "Нет"
                        # Вставляем с тегом для подсветки ликвидных
                        tags = ('liquid',) if is_liquid else ()
                        self.tree.insert('', tk.END, values=(username, 'Свободен', liquid_text), tags=tags)
                        self.free_list.append(username)
                        if is_liquid:
                            self.liquid_free_list.append(username)
                        self.free_count_var.set(f"Свободных: {len(self.free_list)}")
                        self.liquid_count_var.set(f"Ликвидных свободных: {len(self.liquid_free_list)}")
                    elif status == 'deleted':
                        liquid_text = "Да" if is_liquid else "Нет"
                        self.tree.insert('', tk.END, values=(username, 'Удалённый аккаунт', liquid_text))
                        self.deleted_list.append(username)
                        self.deleted_count_var.set(f"Удалённых: {len(self.deleted_list)}")
                    self.tree.see(self.tree.get_children()[-1])
                elif msg[0] == 'status':
                    self.status_var.set(msg[1])
                    self.status_short_var.set(msg[1])
                elif msg[0] == 'error':
                    messagebox.showerror("Ошибка поиска", msg[1])
                    self.stop_search()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._process_queue)

        # Настройка тега для подсветки ликвидных строк
        self.tree.tag_configure('liquid', background='#3a3a00')  # тёмно-жёлтый фон

    def save_results(self):
        if not self.free_list:
            messagebox.showinfo("Нет данных", "Нет свободных username для сохранения.")
            return
        filename = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv")])
        if not filename:
            return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for username in self.free_list:
                    f.write(username + '\n')
            messagebox.showinfo("Успех", f"Сохранено {len(self.free_list)} username в {filename}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    def on_closing(self):
        if self.search_thread and self.search_thread.is_alive():
            if messagebox.askokcancel("Выход", "Поиск ещё выполняется. Остановить и выйти?"):
                self.search_thread.stop()
                self.root.destroy()
        else:
            self.root.destroy()
