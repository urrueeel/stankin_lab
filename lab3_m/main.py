"""Графический интерфейс игры «Судоку»."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from sudoku import LEVELS, conflicts, generate, load_game, save_game


class SudokuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Судоку — лабораторная работа 3")
        self.root.geometry("720x780")
        self.root.minsize(580, 680)
        self.root.report_callback_exception = self.callback_error
        self.level = "Легкая"
        self.level_var = tk.StringVar(value=self.level)
        self.status = tk.StringVar(
            value="Выберите клетку и введите цифру 1–9."
        )
        self.selected = (0, 0)
        self.errors = set()
        self.dirty = False
        self.completed = False
        self.puzzle, self.answer = generate(self.level)
        self.board = [row[:] for row in self.puzzle]
        self.make_menu()
        self.make_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        for key, action in (("n", self.new_game), ("s", self.save),
                            ("o", self.open_game)):
            self.root.bind(f"<Control-{key}>", lambda e, fn=action: fn())
        self.canvas.focus_set()

    def make_menu(self):
        menu = tk.Menu(self.root)
        game = tk.Menu(menu, tearoff=False)
        game.add_command(label="Новая игра", accelerator="Ctrl+N",
                         command=self.new_game)
        game.add_command(label="Открыть…", accelerator="Ctrl+O",
                         command=self.open_game)
        game.add_command(label="Сохранить…", accelerator="Ctrl+S",
                         command=self.save)
        game.add_command(label="Сбросить ввод", command=self.reset)
        game.add_separator()
        game.add_command(label="Выход", command=self.close)
        menu.add_cascade(label="Игра", menu=game)
        view = tk.Menu(menu, tearoff=False)
        for label, size in (("Компактное", "580x680"),
                            ("Обычное", "720x780"),
                            ("Большое", "900x940")):
            view.add_command(label=label,
                             command=lambda value=size: self.resize(value))
        menu.add_cascade(label="Вид", menu=view)
        help_menu = tk.Menu(menu, tearoff=False)
        help_menu.add_command(label="Правила", command=self.rules)
        help_menu.add_command(
            label="О программе",
            command=lambda: messagebox.showinfo(
                "О программе", "Судоку\nЛабораторная работа № 3\nВариант 17",
                parent=self.root,
            ),
        )
        menu.add_cascade(label="Справка", menu=help_menu)
        self.root.config(menu=menu)

    def make_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        toolbar = ttk.Frame(self.root, padding=12)
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Label(toolbar, text="Сложность:").pack(side="left")
        levels = ttk.Combobox(toolbar, textvariable=self.level_var,
                              values=list(LEVELS), state="readonly", width=11)
        levels.pack(side="left", padx=8)
        levels.bind("<<ComboboxSelected>>", lambda e: self.new_game())
        ttk.Button(toolbar, text="Новая игра", command=self.new_game).pack(
            side="right"
        )
        self.canvas = tk.Canvas(self.root, background="#f2f4f7",
                                highlightthickness=0, takefocus=True)
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=12)
        self.canvas.bind("<Configure>", lambda e: self.draw())
        self.canvas.bind("<Button-1>", self.select_cell)
        self.canvas.bind("<Key>", self.key_pressed)
        actions = ttk.Frame(self.root, padding=12)
        actions.grid(row=2, column=0)
        for title, command in (("Проверить", self.check),
                               ("Подсказка", self.hint),
                               ("Очистить клетку", lambda: self.enter(0))):
            ttk.Button(actions, text=title, command=command).pack(
                side="left", padx=4
            )
        ttk.Label(self.root, textvariable=self.status, wraplength=540,
                  anchor="center", padding=(12, 0, 12, 12)).grid(
            row=3, column=0, sticky="ew"
        )

    def geometry(self):
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        size = max(9, min(width, height) - 16)
        return (width - size) / 2, (height - size) / 2, size / 9

    def draw(self):
        self.canvas.delete("all")
        x0, y0, step = self.geometry()
        for r in range(9):
            for c in range(9):
                x, y = x0 + c * step, y0 + r * step
                color = "#ffffff" if not self.puzzle[r][c] else "#edf0f4"
                if (r, c) == self.selected:
                    color = "#cfe3ff"
                if (r, c) in self.errors:
                    color = "#ffd5d5"
                self.canvas.create_rectangle(
                    x, y, x + step, y + step, fill=color, outline=""
                )
                value = self.board[r][c]
                if value:
                    self.canvas.create_text(
                        x + step / 2, y + step / 2, text=str(value),
                        font=("Segoe UI", max(12, int(step * 0.43)),
                              "bold" if self.puzzle[r][c] else "normal"),
                        fill="#202938" if self.puzzle[r][c] else "#1558a6",
                    )
        for i in range(10):
            width = 3 if i % 3 == 0 else 1
            self.canvas.create_line(
                x0 + i * step, y0, x0 + i * step, y0 + 9 * step,
                width=width, fill="#344054",
            )
            self.canvas.create_line(
                x0, y0 + i * step, x0 + 9 * step, y0 + i * step,
                width=width, fill="#344054",
            )

    def select_cell(self, event):
        x0, y0, step = self.geometry()
        r, c = int((event.y - y0) // step), int((event.x - x0) // step)
        if 0 <= r < 9 and 0 <= c < 9:
            self.selected = (r, c)
            self.canvas.focus_set()
            self.draw()

    def key_pressed(self, event):
        if event.state & 4:  # Сочетания Ctrl обрабатывает главное окно.
            return
        moves = {"Up": (-1, 0), "Down": (1, 0),
                 "Left": (0, -1), "Right": (0, 1)}
        if event.keysym in moves:
            r, c = self.selected
            dr, dc = moves[event.keysym]
            self.selected = (max(0, min(8, r + dr)), max(0, min(8, c + dc)))
            self.draw()
        elif event.keysym in ("BackSpace", "Delete"):
            self.enter(0)
        elif event.char and event.char in "123456789":
            self.enter(int(event.char))
        elif event.char and event.char.isprintable():
            self.status.set("Допустимы цифры 1–9. Для очистки — Delete.")

    def enter(self, value):
        r, c = self.selected
        if self.puzzle[r][c]:
            self.status.set("Исходное число менять нельзя.")
        elif self.board[r][c] != value:
            self.board[r][c] = value
            self.dirty = True
            self.errors.clear()
            self.completed = False
            self.status.set("Число введено." if value else "Клетка очищена.")
            if all(all(row) for row in self.board):
                self.check()
        self.draw()
        self.canvas.focus_set()

    def check(self):
        self.errors = conflicts(self.board)
        empty = sum(row.count(0) for row in self.board)
        if self.errors:
            self.status.set(f"Клеток с повторениями: {len(self.errors)}.")
        elif empty:
            self.status.set(f"Повторений нет. Пустых клеток: {empty}.")
        else:
            self.status.set("Судоку решено!")
            if not self.completed:
                self.completed = True
                messagebox.showinfo("Готово", "Судоку решено правильно!",
                                    parent=self.root)
        self.draw()

    def hint(self):
        r, c = self.selected
        if self.puzzle[r][c]:
            self.status.set(
                "Для подсказки выберите клетку без исходного числа."
            )
        elif self.board[r][c] == self.answer[r][c]:
            self.status.set("В выбранной клетке уже правильное число.")
        else:
            self.enter(self.answer[r][c])
            if not self.completed:
                self.status.set("В выбранную клетку добавлена подсказка.")

    def allow_replace(self):
        return not self.dirty or messagebox.askyesno(
            "Несохраненные изменения",
            "Продолжить без сохранения текущих изменений?",
            parent=self.root,
        )

    def new_game(self):
        if not self.allow_replace():
            self.level_var.set(self.level)
            return
        level = self.level_var.get()
        self.root.config(cursor="watch")
        self.root.update_idletasks()
        try:
            puzzle, answer = generate(level)
        finally:
            self.root.config(cursor="")
        self.puzzle, self.answer = puzzle, answer
        self.board = [row[:] for row in puzzle]
        self.level = level
        self.after_load("Новая игра. Выберите клетку и введите цифру.")

    def after_load(self, text):
        self.errors.clear()
        self.selected = (0, 0)
        self.dirty = False
        self.completed = False
        self.status.set(text)
        self.level_var.set(self.level)
        self.draw()
        self.canvas.focus_set()

    def reset(self):
        if messagebox.askyesno("Сброс", "Удалить все введенные числа?",
                               parent=self.root):
            changed = self.board != self.puzzle
            self.board = [row[:] for row in self.puzzle]
            was_dirty = self.dirty
            self.after_load("Введенные числа удалены.")
            self.dirty = was_dirty or changed

    def save(self):
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Сохранить игру", defaultextension=".json",
            filetypes=[("Сохранение судоку", "*.json")],
        )
        if not path:
            return
        try:
            save_game(path, self.puzzle, self.board, self.level)
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка сохранения", str(error),
                                 parent=self.root)
        else:
            self.dirty = False
            self.status.set("Игра сохранена.")

    def open_game(self):
        if not self.allow_replace():
            return
        path = filedialog.askopenfilename(
            parent=self.root, title="Открыть игру",
            filetypes=[("Сохранение судоку", "*.json"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            puzzle, board, level, answer = load_game(path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка открытия", str(error),
                                 parent=self.root)
            return
        self.puzzle, self.board = puzzle, board
        self.level, self.answer = level, answer
        self.after_load("Игра открыта.")

    def resize(self, size):
        self.root.geometry(size)

    def rules(self):
        messagebox.showinfo(
            "Правила судоку",
            "Заполните поле цифрами от 1 до 9 без повторов в строках, "
            "столбцах и квадратах 3×3.\n\n"
            "Серые клетки — исходные числа, синие — ваш ввод. "
            "Красным отмечаются повторения после проверки.\n\n"
            "Стрелки — выбор клетки; Delete или Backspace — очистка. "
            "Подсказка заполняет выбранную клетку.\n\n"
            "Отсутствие повторов в незаполненном поле еще не означает, "
            "что все введенные цифры правильные.", parent=self.root,
        )

    def close(self):
        if self.allow_replace():
            self.root.destroy()

    def callback_error(self, kind, error, traceback):
        # Последняя защита для ошибок обработчиков Tkinter.
        messagebox.showerror(
            "Ошибка", f"Не удалось выполнить действие: {error}",
            parent=self.root,
        )


if __name__ == "__main__":
    window = tk.Tk()
    SudokuApp(window)
    window.mainloop()
