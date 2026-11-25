import calendar
import json
import os
import platform
import tempfile
import tkinter as tk
from datetime import date, datetime, time, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

try:
    import winsound
except ImportError:
    winsound = None


BACKGROUND = "#f4f6f9"
BLUE = "#2878d0"
TEXT = "#263238"
MUTED = "#607d8b"
DEFAULT_CATEGORIES = ["General", "Work", "Personal", "Health"]
RINGTONES = ("System bell", "Chime", "Alert")


def get_data_dir() -> Path:
    operating_system = platform.system()
    if operating_system == "Windows":
        return Path(os.environ.get("APPDATA", Path.home())) / "TaskReminder"
    if operating_system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "TaskReminder"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "task-reminder"


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def parse_time(value: str) -> time:
    parsed = datetime.strptime(value, "%H:%M")
    if parsed.strftime("%H:%M") != value:
        raise ValueError("Time must use 24-hour HH:MM format.")
    return parsed.time()


def task_status(task: dict[str, str], now: datetime | None = None) -> str:
    current = now or datetime.now()
    start = datetime.fromisoformat(task["start_at"])
    end = datetime.fromisoformat(task["end_at"])
    if current < start:
        return "Not yet started"
    if current < end:
        return "Started"
    return "Due"


def task_datetime(value: str) -> datetime:
    return datetime.fromisoformat(value)


class TaskReminderApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Task Reminder")
        self.root.geometry("940x690")
        self.root.minsize(800, 610)
        self.root.configure(bg=BACKGROUND)
        self.data_dir = get_data_dir()
        self.data_path = self.data_dir / "tasks.json"
        self.settings_path = self.data_dir / "settings.json"
        self.tasks: list[dict[str, str]] = []
        self.categories = DEFAULT_CATEGORIES.copy()
        self.profile_name = ""
        self.ringtone = "System bell"
        self.custom_sound = ""
        self.editing_index: int | None = None
        self._icon: tk.PhotoImage | None = None

        self.set_clock_icon()
        self.load_settings()
        self.load_tasks()
        self.setup_ui()
        self.refresh_tasks()
        self.root.after(1000, self.check_reminders)

    def set_clock_icon(self) -> None:
        try:
            icon = tk.PhotoImage(width=16, height=16)
            for y in range(16):
                row = []
                for x in range(16):
                    distance = (x - 7.5) ** 2 + (y - 7.5) ** 2
                    color = BACKGROUND
                    if 2.5**2 <= distance <= 7**2:
                        color = BLUE
                    elif distance < 2.5**2:
                        color = "#ffffff"
                    if (x == 7 and 4 <= y <= 8) or (y == 8 and 7 <= x <= 11):
                        color = "#17365d"
                    row.append(color)
                icon.put("{" + " ".join(row) + "}", to=(0, y))
            self.root.iconphoto(True, icon)
            self._icon = icon
        except tk.TclError as exc:
            messagebox.showwarning("Icon unavailable", str(exc), parent=self.root)

    def setup_ui(self) -> None:
        header = tk.Frame(self.root, bg=BACKGROUND)
        header.pack(fill="x", padx=20, pady=(12, 8))
        title_frame = tk.Frame(header, bg=BACKGROUND)
        title_frame.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_frame,
            text="Task Reminder",
            font=("Segoe UI", 17, "bold"),
            bg=BACKGROUND,
            fg=TEXT,
        ).pack(anchor="w")
        self.greeting_label = tk.Label(
            title_frame, text="", font=("Segoe UI", 9), bg=BACKGROUND, fg=MUTED
        )
        self.greeting_label.pack(anchor="w", pady=(1, 0))
        tk.Button(
            header,
            text="⚙ Settings",
            font=("Segoe UI", 9),
            bg="#e3e8ee",
            fg=TEXT,
            relief="flat",
            padx=10,
            pady=5,
            command=self.open_settings,
        ).pack(side="right", anchor="n")
        self.update_greeting()

        form = tk.LabelFrame(
            self.root,
            text="  Add or update a task  ",
            font=("Segoe UI", 10, "bold"),
            bg=BACKGROUND,
            fg=TEXT,
            padx=12,
            pady=8,
        )
        form.pack(fill="x", padx=20, pady=(0, 10))
        form.columnconfigure(1, weight=1)
        form.columnconfigure(3, weight=1)

        tk.Label(form, text="Task", bg=BACKGROUND, fg=TEXT).grid(
            row=0, column=0, sticky="w", padx=(0, 7), pady=4
        )
        self.task_entry = ttk.Entry(form)
        self.task_entry.grid(row=0, column=1, columnspan=3, sticky="ew", pady=4)
        self.task_entry.bind("<Return>", lambda _event: self.save_task())

        tk.Label(form, text="Category", bg=BACKGROUND, fg=TEXT).grid(
            row=1, column=0, sticky="w", padx=(0, 7), pady=4
        )
        self.category_box = ttk.Combobox(form, state="readonly", width=18)
        self.category_box.configure(values=self.categories)
        self.category_box.grid(row=1, column=1, sticky="ew", padx=(0, 14), pady=4)
        self.category_box.set(self.categories[0])

        tk.Label(form, text="Start", bg=BACKGROUND, fg=TEXT).grid(
            row=1, column=2, sticky="w", padx=(0, 7), pady=4
        )
        self.start_date_var = tk.StringVar(value=date.today().isoformat())
        self.start_time_var = tk.StringVar(value=(datetime.now() + timedelta(minutes=5)).strftime("%H:%M"))
        start_controls = tk.Frame(form, bg=BACKGROUND)
        start_controls.grid(row=1, column=3, sticky="w", pady=4)
        ttk.Entry(start_controls, textvariable=self.start_date_var, width=11, state="readonly").pack(side="left")
        tk.Button(
            start_controls, text="▦", width=2, command=lambda: self.choose_date(self.start_date_var)
        ).pack(side="left", padx=(2, 5))
        ttk.Entry(start_controls, textvariable=self.start_time_var, width=6, state="readonly").pack(side="left")
        tk.Button(
            start_controls, text="◷", width=2, command=lambda: self.choose_time(self.start_time_var)
        ).pack(side="left", padx=(2, 0))

        tk.Label(form, text="Ends", bg=BACKGROUND, fg=TEXT).grid(
            row=2, column=0, sticky="w", padx=(0, 7), pady=4
        )
        self.end_date_var = tk.StringVar(value=date.today().isoformat())
        self.end_time_var = tk.StringVar(
            value=(datetime.now() + timedelta(minutes=65)).strftime("%H:%M")
        )
        end_controls = tk.Frame(form, bg=BACKGROUND)
        end_controls.grid(row=2, column=1, sticky="w", pady=4)
        ttk.Entry(end_controls, textvariable=self.end_date_var, width=11, state="readonly").pack(side="left")
        tk.Button(
            end_controls, text="▦", width=2, command=lambda: self.choose_date(self.end_date_var)
        ).pack(side="left", padx=(2, 5))
        ttk.Entry(end_controls, textvariable=self.end_time_var, width=6, state="readonly").pack(side="left")
        tk.Button(
            end_controls, text="◷", width=2, command=lambda: self.choose_time(self.end_time_var)
        ).pack(side="left", padx=(2, 0))

        button_row = tk.Frame(form, bg=BACKGROUND)
        button_row.grid(row=2, column=2, columnspan=2, sticky="e", pady=4)
        self.save_button = tk.Button(
            button_row,
            text="Add Task",
            font=("Segoe UI", 9, "bold"),
            bg=BLUE,
            fg="white",
            relief="flat",
            padx=13,
            pady=5,
            command=self.save_task,
        )
        self.save_button.pack(side="left", padx=(0, 5))
        self.cancel_button = tk.Button(
            button_row,
            text="Clear",
            font=("Segoe UI", 9),
            bg="#e3e8ee",
            fg=TEXT,
            relief="flat",
            padx=11,
            pady=5,
            command=self.clear_form,
        )
        self.cancel_button.pack(side="left")

        list_panel = tk.Frame(self.root, bg=BACKGROUND)
        list_panel.pack(fill="both", expand=True, padx=20, pady=(0, 12))
        list_header = tk.Frame(list_panel, bg=BACKGROUND)
        list_header.pack(fill="x", pady=(0, 5))
        tk.Label(
            list_header, text="Your tasks", font=("Segoe UI", 11, "bold"), bg=BACKGROUND, fg=TEXT
        ).pack(side="left")
        self.count_label = tk.Label(list_header, text="0 tasks", font=("Segoe UI", 9), bg=BACKGROUND, fg=MUTED)
        self.count_label.pack(side="left", padx=(8, 0))
        self.edit_button = tk.Button(
            list_header,
            text="Edit",
            font=("Segoe UI", 9),
            bg="#e3e8ee",
            fg=TEXT,
            relief="flat",
            padx=12,
            pady=4,
            state="disabled",
            command=self.load_selected_for_edit,
        )
        self.delete_button = tk.Button(
            list_header,
            text="Delete",
            font=("Segoe UI", 9),
            bg="#fde8e7",
            fg="#b3261e",
            relief="flat",
            padx=12,
            pady=4,
            state="disabled",
            command=self.delete_selected,
        )

        tree_frame = tk.Frame(list_panel, bg="white")
        tree_frame.pack(fill="both", expand=True)
        columns = ("task", "category", "starts", "ends", "status")
        self.task_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "task": ("Task", 250),
            "category": ("Category", 110),
            "starts": ("Starts", 175),
            "ends": ("Ends", 175),
            "status": ("Status", 125),
        }
        for column, (heading, width) in headings.items():
            self.task_tree.heading(column, text=heading)
            self.task_tree.column(column, width=width, minwidth=80, anchor="w")
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.task_tree.yview)
        self.task_tree.configure(yscrollcommand=scrollbar.set)
        self.task_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.task_tree.bind("<<TreeviewSelect>>", self.on_task_selected)
        self.task_tree.tag_configure("started", foreground="#2878d0")
        self.task_tree.tag_configure("due", foreground="#b3261e")

        tk.Label(
            list_panel,
            text="A reminder sounds 5 minutes before start and again when the task starts.",
            font=("Segoe UI", 8),
            bg=BACKGROUND,
            fg=MUTED,
        ).pack(anchor="w", pady=(5, 0))

    def load_tasks(self) -> None:
        try:
            with self.data_path.open("r", encoding="utf-8") as data_file:
                stored: Any = json.load(data_file)
        except FileNotFoundError:
            self.tasks = []
            return
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Could not load tasks", f"{self.data_path}\n\n{exc}", parent=self.root)
            self.tasks = []
            return
        if not isinstance(stored, list):
            messagebox.showerror("Invalid task data", "Saved tasks must be a list.", parent=self.root)
            self.tasks = []
            return

        loaded: list[dict[str, str]] = []
        for item in stored:
            if not isinstance(item, dict) or not isinstance(item.get("task"), str):
                continue
            text = item["task"].strip()
            if not text:
                continue
            try:
                if isinstance(item.get("start_at"), str) and isinstance(item.get("end_at"), str):
                    start = task_datetime(item["start_at"])
                    end = task_datetime(item["end_at"])
                    if end <= start:
                        continue
                    category = item.get("category", "General")
                    before = item.get("reminded_before_start", "false")
                    started = item.get("reminded_at_start", "false")
                else:
                    old_time = parse_time(item.get("time", ""))
                    start = datetime.combine(date.today(), old_time)
                    end = start + timedelta(hours=1)
                    category = "General"
                    before = "false"
                    started = "true" if item.get("notified_on") == date.today().isoformat() else "false"
            except (TypeError, ValueError, OverflowError):
                continue
            if not isinstance(category, str):
                category = "General"
            loaded.append(
                {
                    "task": text,
                    "category": category,
                    "start_at": start.isoformat(timespec="minutes"),
                    "end_at": end.isoformat(timespec="minutes"),
                    "reminded_before_start": "true" if before is True or before == "true" else "false",
                    "reminded_at_start": "true" if started is True or started == "true" else "false",
                }
            )
        self.tasks = sorted(loaded, key=lambda task: task["start_at"])
        if len(loaded) != len(stored):
            messagebox.showwarning(
                "Some tasks skipped", "Some saved tasks contained invalid data and were skipped.", parent=self.root
            )

    def load_settings(self) -> None:
        try:
            with self.settings_path.open("r", encoding="utf-8") as settings_file:
                settings: Any = json.load(settings_file)
        except FileNotFoundError:
            return
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Could not load settings", f"{self.settings_path}\n\n{exc}", parent=self.root)
            return
        if not isinstance(settings, dict):
            messagebox.showerror("Invalid settings", "Saved settings must be an object.", parent=self.root)
            return
        profile = settings.get("profile_name", "")
        categories = settings.get("categories", DEFAULT_CATEGORIES)
        ringtone = settings.get("ringtone", "System bell")
        sound_path = settings.get("custom_sound", "")
        if isinstance(profile, str):
            self.profile_name = profile.strip()
        if isinstance(categories, list):
            clean_categories = list(dict.fromkeys(
                item.strip() for item in categories if isinstance(item, str) and item.strip()
            ))
            self.categories = clean_categories or DEFAULT_CATEGORIES.copy()
        if ringtone in (*RINGTONES, "Custom WAV"):
            self.ringtone = ringtone
        if isinstance(sound_path, str):
            self.custom_sound = sound_path

    def persist_json(self, path: Path, value: Any) -> None:
        temporary_path: str | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=path.parent, delete=False
            ) as output:
                temporary_path = output.name
                json.dump(value, output, ensure_ascii=False, indent=2)
                output.write("\n")
            os.replace(temporary_path, path)
        except (OSError, TypeError, ValueError) as exc:
            cleanup_error: OSError | None = None
            if temporary_path is not None:
                try:
                    os.unlink(temporary_path)
                except OSError as cleanup_exc:
                    cleanup_error = cleanup_exc
            detail = f"Could not save {path}: {exc}"
            if cleanup_error:
                detail += f"\nTemporary file cleanup also failed: {cleanup_error}"
            raise OSError(detail) from exc

    def save_tasks(self, tasks: list[dict[str, str]]) -> None:
        self.persist_json(self.data_path, tasks)

    def update_greeting(self) -> None:
        if hasattr(self, "greeting_label"):
            greeting = f"Welcome, {self.profile_name}" if self.profile_name else "Plan your day"
            self.greeting_label.config(text=greeting)

    def choose_date(self, variable: tk.StringVar) -> None:
        try:
            selected = parse_date(variable.get())
        except ValueError:
            selected = date.today()
        popup = tk.Toplevel(self.root)
        popup.title("Select date")
        popup.transient(self.root)
        popup.resizable(False, False)
        popup.configure(bg=BACKGROUND)
        year, month = selected.year, selected.month
        title_var = tk.StringVar()
        title = tk.Frame(popup, bg=BACKGROUND)
        title.pack(fill="x", padx=8, pady=8)
        grid_frame = tk.Frame(popup, bg=BACKGROUND)
        grid_frame.pack(padx=8, pady=(0, 8))

        def display_month() -> None:
            title_var.set(f"{calendar.month_name[month]} {year}")
            for child in grid_frame.winfo_children():
                child.destroy()
            for column, day_name in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
                tk.Label(grid_frame, text=day_name, width=4, bg=BACKGROUND, fg=MUTED).grid(
                    row=0, column=column, pady=(0, 4)
                )
            for row, week in enumerate(calendar.monthcalendar(year, month), start=1):
                for column, day_number in enumerate(week):
                    if day_number == 0:
                        continue
                    day_value = date(year, month, day_number)
                    button = tk.Button(
                        grid_frame,
                        text=str(day_number),
                        width=3,
                        relief="flat",
                        bg=BLUE if day_value == selected else "white",
                        fg="white" if day_value == selected else TEXT,
                        command=lambda chosen=day_value: choose(chosen),
                    )
                    button.grid(row=row, column=column, padx=1, pady=1)

        def shift_month(amount: int) -> None:
            nonlocal year, month
            month += amount
            if month < 1:
                year -= 1
                month = 12
            elif month > 12:
                year += 1
                month = 1
            display_month()

        def choose(chosen: date) -> None:
            variable.set(chosen.isoformat())
            popup.destroy()

        tk.Button(title, text="‹", width=3, command=lambda: shift_month(-1)).pack(side="left")
        tk.Label(title, textvariable=title_var, width=18, bg=BACKGROUND, fg=TEXT).pack(side="left")
        tk.Button(title, text="›", width=3, command=lambda: shift_month(1)).pack(side="right")
        display_month()
        popup.grab_set()
        popup.wait_window()

    def choose_time(self, variable: tk.StringVar) -> None:
        try:
            initial = parse_time(variable.get())
        except ValueError:
            initial = datetime.now().time()
        popup = tk.Toplevel(self.root)
        popup.title("Select time")
        popup.transient(self.root)
        popup.resizable(False, False)
        popup.configure(bg=BACKGROUND)
        content = tk.Frame(popup, bg=BACKGROUND, padx=18, pady=14)
        content.pack()
        tk.Label(content, text="Choose hour and minute", bg=BACKGROUND, fg=TEXT).pack(pady=(0, 8))
        values = tk.Frame(content, bg=BACKGROUND)
        values.pack()
        hours = ttk.Combobox(values, values=[f"{hour:02d}" for hour in range(24)], width=5, state="readonly")
        minutes = ttk.Combobox(values, values=[f"{minute:02d}" for minute in range(60)], width=5, state="readonly")
        hours.set(f"{initial.hour:02d}")
        minutes.set(f"{initial.minute:02d}")
        hours.pack(side="left", padx=3)
        tk.Label(values, text=":", bg=BACKGROUND, fg=TEXT).pack(side="left")
        minutes.pack(side="left", padx=3)

        def use_time() -> None:
            if not hours.get() or not minutes.get():
                messagebox.showwarning("Select a time", "Choose both hour and minute.", parent=popup)
                return
            variable.set(f"{hours.get()}:{minutes.get()}")
            popup.destroy()

        tk.Button(content, text="Use time", bg=BLUE, fg="white", relief="flat", command=use_time).pack(pady=(12, 0))
        popup.grab_set()
        popup.wait_window()

    def validate_form(self) -> tuple[str, str, datetime, datetime] | None:
        task_text = self.task_entry.get().strip()
        category = self.category_box.get().strip()
        if not task_text:
            messagebox.showwarning("Task required", "Enter a task description.", parent=self.root)
            self.task_entry.focus_set()
            return None
        if not category or category not in self.categories:
            messagebox.showwarning("Category required", "Choose a task category in Settings.", parent=self.root)
            return None
        try:
            start = datetime.combine(parse_date(self.start_date_var.get()), parse_time(self.start_time_var.get()))
            end = datetime.combine(parse_date(self.end_date_var.get()), parse_time(self.end_time_var.get()))
        except ValueError:
            messagebox.showwarning(
                "Invalid schedule",
                "Choose valid dates and 24-hour times using the calendar and clock buttons.",
                parent=self.root,
            )
            return None
        if end <= start:
            messagebox.showwarning("Invalid schedule", "The end must be later than the start.", parent=self.root)
            return None
        return task_text, category, start, end

    def save_task(self) -> None:
        form = self.validate_form()
        if form is None:
            return
        task_text, category, start, end = form
        updated = [task.copy() for task in self.tasks]
        task = {
            "task": task_text,
            "category": category,
            "start_at": start.isoformat(timespec="minutes"),
            "end_at": end.isoformat(timespec="minutes"),
            "reminded_before_start": "false",
            "reminded_at_start": "false",
        }
        if self.editing_index is None:
            updated.append(task)
        elif 0 <= self.editing_index < len(updated):
            updated[self.editing_index] = task
        else:
            messagebox.showerror("Update error", "The selected task no longer exists.", parent=self.root)
            self.clear_form()
            return
        updated.sort(key=lambda item: item["start_at"])
        try:
            self.save_tasks(updated)
        except OSError as exc:
            messagebox.showerror("Save error", str(exc), parent=self.root)
            return
        self.tasks = updated
        self.refresh_tasks()
        self.clear_form()

    def selected_index(self) -> int | None:
        selected = self.task_tree.selection()
        if not selected:
            return None
        try:
            index = int(selected[0])
        except ValueError:
            return None
        return index if 0 <= index < len(self.tasks) else None

    def on_task_selected(self, _event: tk.Event | None) -> None:
        if self.selected_index() is None:
            self.edit_button.pack_forget()
            self.delete_button.pack_forget()
            return
        self.edit_button.config(state="normal")
        self.delete_button.config(state="normal")
        if not self.edit_button.winfo_manager():
            self.edit_button.pack(side="right", padx=(5, 0))
        if not self.delete_button.winfo_manager():
            self.delete_button.pack(side="right")

    def load_selected_for_edit(self) -> None:
        index = self.selected_index()
        if index is None:
            messagebox.showinfo("Select a task", "Choose a task to edit.", parent=self.root)
            return
        task = self.tasks[index]
        start, end = task_datetime(task["start_at"]), task_datetime(task["end_at"])
        self.editing_index = index
        self.task_entry.delete(0, tk.END)
        self.task_entry.insert(0, task["task"])
        self.category_box.set(task["category"] if task["category"] in self.categories else self.categories[0])
        self.start_date_var.set(start.date().isoformat())
        self.start_time_var.set(start.strftime("%H:%M"))
        self.end_date_var.set(end.date().isoformat())
        self.end_time_var.set(end.strftime("%H:%M"))
        self.save_button.config(text="Save Update")
        self.task_entry.focus_set()

    def delete_selected(self) -> None:
        index = self.selected_index()
        if index is None:
            messagebox.showinfo("Select a task", "Choose a task to delete.", parent=self.root)
            return
        if not messagebox.askyesno("Delete task", f"Delete “{self.tasks[index]['task']}”?", parent=self.root):
            return
        updated = [task.copy() for task in self.tasks]
        del updated[index]
        try:
            self.save_tasks(updated)
        except OSError as exc:
            messagebox.showerror("Delete error", str(exc), parent=self.root)
            return
        self.tasks = updated
        self.refresh_tasks()
        self.clear_form()

    def clear_form(self) -> None:
        self.editing_index = None
        self.task_entry.delete(0, tk.END)
        self.category_box.set(self.categories[0] if self.categories else "")
        now = datetime.now()
        start = (now + timedelta(minutes=5)).replace(second=0, microsecond=0)
        end = start + timedelta(hours=1)
        self.start_date_var.set(start.date().isoformat())
        self.start_time_var.set(start.strftime("%H:%M"))
        self.end_date_var.set(end.date().isoformat())
        self.end_time_var.set(end.strftime("%H:%M"))
        self.save_button.config(text="Add Task")
        self.task_tree.selection_remove(self.task_tree.selection())
        self.edit_button.config(state="disabled")
        self.delete_button.config(state="disabled")

    def refresh_tasks(self) -> None:
        selected = self.selected_index() if hasattr(self, "task_tree") else None
        if not hasattr(self, "task_tree"):
            return
        for row in self.task_tree.get_children():
            self.task_tree.delete(row)
        now = datetime.now()
        self.tasks.sort(key=lambda item: item["start_at"])
        for index, task in enumerate(self.tasks):
            start, end = task_datetime(task["start_at"]), task_datetime(task["end_at"])
            status = task_status(task, now)
            tag = "started" if status == "Started" else "due" if status == "Due" else ""
            self.task_tree.insert(
                "",
                "end",
                iid=str(index),
                values=(
                    task["task"],
                    task["category"],
                    start.strftime("%Y-%m-%d %H:%M"),
                    end.strftime("%Y-%m-%d %H:%M"),
                    status,
                ),
                tags=(tag,) if tag else (),
            )
        count = len(self.tasks)
        self.count_label.config(text=f"{count} task{'s' if count != 1 else ''}")
        if selected is not None and selected < count:
            self.task_tree.selection_set(str(selected))
        self.on_task_selected(None)

    def open_settings(self) -> None:
        popup = tk.Toplevel(self.root)
        popup.title("Settings")
        popup.geometry("480x500")
        popup.minsize(440, 450)
        popup.transient(self.root)
        popup.configure(bg=BACKGROUND)
        body = tk.Frame(popup, bg=BACKGROUND, padx=16, pady=12)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="Settings", font=("Segoe UI", 15, "bold"), bg=BACKGROUND, fg=TEXT).pack(anchor="w")

        profile_frame = tk.LabelFrame(body, text="Profile", bg=BACKGROUND, fg=TEXT, padx=10, pady=8)
        profile_frame.pack(fill="x", pady=(10, 8))
        tk.Label(profile_frame, text="Display name", bg=BACKGROUND, fg=TEXT).pack(anchor="w")
        profile_var = tk.StringVar(value=self.profile_name)
        ttk.Entry(profile_frame, textvariable=profile_var).pack(fill="x", pady=(4, 0))

        category_frame = tk.LabelFrame(body, text="Task categories", bg=BACKGROUND, fg=TEXT, padx=10, pady=8)
        category_frame.pack(fill="both", expand=True, pady=5)
        category_list = tk.Listbox(category_frame, height=5, activestyle="none")
        category_list.pack(side="left", fill="both", expand=True)
        category_scroll = ttk.Scrollbar(category_frame, orient="vertical", command=category_list.yview)
        category_scroll.pack(side="left", fill="y")
        category_list.configure(yscrollcommand=category_scroll.set)
        for category in self.categories:
            category_list.insert(tk.END, category)
        category_controls = tk.Frame(category_frame, bg=BACKGROUND)
        category_controls.pack(side="left", fill="y", padx=(8, 0))
        category_var = tk.StringVar()
        ttk.Entry(category_controls, textvariable=category_var, width=17).pack(pady=(0, 5))

        def add_category() -> None:
            name = category_var.get().strip()
            if not name:
                messagebox.showwarning("Category required", "Enter a category name.", parent=popup)
                return
            if any(name.casefold() == existing.casefold() for existing in self.categories):
                messagebox.showwarning("Category exists", "That category is already in the list.", parent=popup)
                return
            self.categories.append(name)
            category_list.insert(tk.END, name)
            category_var.set("")

        def remove_category() -> None:
            selection = category_list.curselection()
            if not selection:
                messagebox.showinfo("Select a category", "Choose a category to remove.", parent=popup)
                return
            category = category_list.get(selection[0])
            if category == "General":
                messagebox.showwarning("Cannot remove", "The General category must remain available.", parent=popup)
                return
            if any(task["category"] == category for task in self.tasks):
                messagebox.showwarning(
                    "Category in use",
                    "Reassign tasks in this category before removing it.",
                    parent=popup,
                )
                return
            self.categories.remove(category)
            category_list.delete(selection[0])

        tk.Button(category_controls, text="Add", command=add_category).pack(fill="x", pady=2)
        tk.Button(category_controls, text="Remove", command=remove_category).pack(fill="x", pady=2)

        sound_frame = tk.LabelFrame(body, text="Reminder sound", bg=BACKGROUND, fg=TEXT, padx=10, pady=8)
        sound_frame.pack(fill="x", pady=(8, 4))
        sound_var = tk.StringVar(value=self.ringtone)
        ttk.Combobox(
            sound_frame, textvariable=sound_var, values=(*RINGTONES, "Custom WAV"), state="readonly"
        ).pack(side="left", fill="x", expand=True)
        sound_path_var = tk.StringVar(value=Path(self.custom_sound).name if self.custom_sound else "No sound file selected")

        def browse_sound() -> None:
            path = filedialog.askopenfilename(
                parent=popup,
                title="Choose a WAV ringtone",
                filetypes=(("WAV audio", "*.wav"),),
            )
            if not path:
                return
            if Path(path).suffix.lower() != ".wav":
                messagebox.showerror("Unsupported sound", "Choose a WAV audio file.", parent=popup)
                return
            self.custom_sound = path
            sound_path_var.set(Path(path).name)
            sound_var.set("Custom WAV")

        tk.Button(sound_frame, text="Choose WAV…", command=browse_sound).pack(side="left", padx=(7, 0))
        tk.Label(body, textvariable=sound_path_var, font=("Segoe UI", 8), bg=BACKGROUND, fg=MUTED).pack(anchor="w")

        def save_settings() -> None:
            profile = profile_var.get().strip()
            selected_categories = [category_list.get(i) for i in range(category_list.size())]
            if not selected_categories:
                messagebox.showerror("Category required", "Keep at least one task category.", parent=popup)
                return
            chosen_ringtone = sound_var.get()
            if chosen_ringtone == "Custom WAV":
                if not self.custom_sound or not Path(self.custom_sound).is_file():
                    messagebox.showerror("Sound file missing", "Choose an existing WAV file.", parent=popup)
                    return
            settings = {
                "profile_name": profile,
                "categories": selected_categories,
                "ringtone": chosen_ringtone,
                "custom_sound": self.custom_sound,
            }
            try:
                self.persist_json(self.settings_path, settings)
            except OSError as exc:
                messagebox.showerror("Settings save error", str(exc), parent=popup)
                return
            self.profile_name = profile
            self.categories = selected_categories
            self.ringtone = chosen_ringtone
            self.category_box.configure(values=self.categories)
            if self.category_box.get() not in self.categories:
                self.category_box.set(self.categories[0])
            self.update_greeting()
            popup.destroy()

        tk.Button(
            body, text="Save Settings", bg=BLUE, fg="white", relief="flat", padx=14, pady=6,
            command=save_settings,
        ).pack(anchor="e", pady=(10, 0))
        popup.grab_set()

    def play_reminder_sound(self) -> None:
        if self.ringtone == "Custom WAV":
            if not self.custom_sound or not Path(self.custom_sound).is_file():
                raise OSError("The selected WAV sound file is unavailable.")
            if winsound is None:
                raise OSError("Custom WAV playback is supported on Windows only.")
            winsound.PlaySound(
                self.custom_sound, winsound.SND_FILENAME | winsound.SND_ASYNC
            )
            return
        if winsound is None:
            self.root.bell()
            return
        sound_flag = {
            "System bell": winsound.MB_OK,
            "Chime": winsound.MB_ICONASTERISK,
            "Alert": winsound.MB_ICONEXCLAMATION,
        }.get(self.ringtone, winsound.MB_OK)
        winsound.MessageBeep(sound_flag)

    def check_reminders(self) -> None:
        now = datetime.now()
        changed = False
        alerts: list[tuple[str, str]] = []
        for task in self.tasks:
            start = task_datetime(task["start_at"])
            end = task_datetime(task["end_at"])
            if not (start <= now < end) and not (start - timedelta(minutes=5) <= now < start):
                continue
            if now < start and task["reminded_before_start"] != "true":
                task["reminded_before_start"] = "true"
                alerts.append((task["task"], "starts in 5 minutes"))
                changed = True
            elif start <= now < end and task["reminded_at_start"] != "true":
                task["reminded_at_start"] = "true"
                alerts.append((task["task"], "is starting now"))
                changed = True
        if changed:
            try:
                self.save_tasks(self.tasks)
            except OSError as exc:
                messagebox.showerror("Reminder save error", str(exc), parent=self.root)
            self.refresh_tasks()
            for task_text, timing in alerts:
                try:
                    self.play_reminder_sound()
                except (OSError, RuntimeError, tk.TclError) as exc:
                    messagebox.showerror("Sound playback error", str(exc), parent=self.root)
                messagebox.showinfo("Task reminder", f"{task_text}\n\n{timing}.", parent=self.root)
        self.refresh_tasks()
        try:
            self.root.after(15000, self.check_reminders)
        except tk.TclError:
            return


if __name__ == "__main__":
    try:
        app_root = tk.Tk()
        TaskReminderApp(app_root)
        app_root.mainloop()
    except tk.TclError as exc:
        messagebox.showerror("Application error", f"Could not start the app:\n{exc}")
