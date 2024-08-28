import shutil
import subprocess
import sys
import tkinter as tk
import tkinter.ttk as ttk
import csv
import os

from models.PathModel import PathModel
from views.EditView import EditView


def resource_path(relative_path):
    """ Получает путь к ресурсу в запакованном приложении или в обычной директории """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def get_application_support_path():
    """ Возвращает путь к директории в ~/Library/Application Support/YourAppName """
    app_support_path = os.path.expanduser('~/Library/Application Support/PathCalc')
    os.makedirs(app_support_path, exist_ok=True)
    return app_support_path


def ensure_csv_in_application_support(file_name):
    """ Копирует файл из ресурсов в Application Support, если его там нет """
    app_support_path = get_application_support_path()
    destination_file_path = os.path.join(app_support_path, file_name)

    # Копируем файл только если он еще не существует в Application Support
    if not os.path.exists(destination_file_path):
        source_file_path = resource_path(file_name)
        if not os.path.exists(source_file_path):
            raise FileNotFoundError(f"Source file {file_name} not found in resources.")
        shutil.copy(source_file_path, destination_file_path)

    return destination_file_path


def load_table(file_name):
    """ Загружает таблицу из CSV файла в Application Support """
    table = []
    file_path = ensure_csv_in_application_support(file_name)

    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            table.append([float(value) for value in row])

    return table


class MainView(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.parent.title("PathCalc")

        self.path_segments = []

        self.non_eca_table = load_table('non_eca_table.csv')
        self.eca_table = load_table('eca_table.csv')

        self.create_widgets()

        self.pack()

    def create_widgets(self):
        # Main frame
        self.main_frame = ttk.Frame()
        self.main_frame.pack()
        # Spinbox frame
        self.spinbox_frame = ttk.Frame(self.main_frame)
        self.spinbox_frame.pack(fill=tk.X)

        # Label
        self.path_amount_label = ttk.Label(self.spinbox_frame, text="Кол-во отрезков пути:")
        self.path_amount_label.grid(row=0, column=0)

        # Spinbox
        self.path_amount_var = tk.IntVar(value=0)
        self.path_amount_spinbox = ttk.Spinbox(self.spinbox_frame, from_=0, to=30, textvariable=self.path_amount_var,
                                               state="readonly",
                                               command=self.update_segments)
        self.path_amount_spinbox.grid(row=0, column=1)

        # Edit Tables Button
        self.edit_table_button = ttk.Button(self.spinbox_frame, text="Изменить таблицы",
                                            command=self.edit_view_open)
        self.edit_table_button.grid(row=0, column=2)

        # Table Frame
        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.pack()

        # Table Scroll
        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient=tk.VERTICAL)
        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Table
        columns = ("№", "Расстояние", "Скорость", "ECA", "Погрузка", "Потребление")
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings", yscrollcommand=self.tree_scroll.set,
                                 selectmode=tk.BROWSE)
        self.tree.heading("№", text="№")
        self.tree.heading("Расстояние", text="Расстояние")
        self.tree.heading("Скорость", text="Скорость")
        self.tree.heading("ECA", text="ECA")
        self.tree.heading("Погрузка", text="Погрузка")
        self.tree.heading("Потребление", text="Потребление")
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree_scroll.config(command=self.tree.yview)

        self.tree.bind("<<TreeviewSelect>>", self.item_selected)

        # Input Frame
        self.input_frame = ttk.Frame(self.main_frame)
        self.input_frame.pack()

        self.dist_label = ttk.Label(self.input_frame, text="Расстояние(в милях):")
        self.dist_label.grid(row=0, column=0)
        self.dist_entry_var = tk.StringVar()
        self.dist_entry = ttk.Entry(self.input_frame, width=10, state=tk.DISABLED, textvariable=self.dist_entry_var)
        self.dist_entry.grid(row=0, column=1)

        self.speed_label = ttk.Label(self.input_frame, text="Скорость(в узлах):")
        self.speed_label.grid(row=1, column=0)
        self.speed_entry_var = tk.StringVar()
        self.speed_entry = ttk.Entry(self.input_frame, width=10, state=tk.DISABLED, textvariable=self.speed_entry_var)
        self.speed_entry.grid(row=1, column=1)

        self.eca_var = tk.BooleanVar(value=False)
        self.eca_checkbox = ttk.Checkbutton(self.input_frame, text="ECA area", variable=self.eca_var, state=tk.DISABLED)
        self.eca_checkbox.grid(row=2, columnspan=2)

        self.loading_type = tk.StringVar()
        self.laden_radiobutton = ttk.Radiobutton(self.input_frame, text="Laden", value="Laden",
                                                 variable=self.loading_type, state=tk.DISABLED)
        self.laden_radiobutton.grid(row=3, column=0)
        self.ballast_radiobutton = ttk.Radiobutton(self.input_frame, text="Ballast", value="Ballast",
                                                   variable=self.loading_type, state=tk.DISABLED)
        self.ballast_radiobutton.grid(row=3, column=1)

        self.update_button = ttk.Button(self.input_frame, text="Обновить данные", state=tk.DISABLED,
                                        command=self.update_selected)
        self.update_button.grid(row=4, column=0, columnspan=2)

        # Result Frame
        self.result_frame = ttk.Frame(self.main_frame)
        self.result_frame.pack(side="right")

        self.eca_result_label = ttk.Label(self.result_frame, text="ECA consumption: 0.0")
        self.eca_result_label.pack()

        self.non_eca_result_label = ttk.Label(self.result_frame, text="Non ECA consumption: 0.0")
        self.non_eca_result_label.pack()

    def update_segments(self):
        self.clear_input()
        self.disable_input()

        current_len = len(self.path_segments)
        new_len = self.path_amount_var.get()

        if new_len > current_len:
            for i in range(new_len - current_len):
                self.path_segments.append(PathModel(current_len + i + 1))
        elif new_len < current_len:
            self.path_segments = self.path_segments[:new_len]

        self.tree.delete(*self.tree.get_children())
        for i, segment in enumerate(self.path_segments):
            self.tree.insert("", "end", iid=segment.id,
                             values=(segment.id,
                                     segment.distance,
                                     segment.speed,
                                     segment.is_eca,
                                     segment.loading,
                                     segment.consumption))

    def item_selected(self, event):
        selected_item = self.tree.selection()

        if not selected_item:
            return

        self.index = selected_item[0]
        self.items = self.tree.item(self.index)["values"]

        self.dist_entry_var.set(self.items[1])
        self.speed_entry_var.set(self.items[2])
        self.eca_var.set(eval(self.items[3]))
        self.loading_type.set(self.items[4])

        self.activate_input()

    def update_selected(self):
        distance = float(self.dist_entry_var.get())
        speed = float(self.speed_entry_var.get())
        eca = self.eca_var.get()
        loading_type = self.loading_type.get()

        self.path_segments[int(self.index) - 1] = PathModel(
            self.index,
            distance,
            speed,
            eca,
            loading_type,
            self.calculate_consumption(loading_type, eca, distance, speed)
        )

        self.update_segments()
        self.disable_input()
        self.clear_input()

        eca_sum = 0.0
        non_eca_sum = 0.0
        for i in self.path_segments:
            if i.is_eca:
                eca_sum += i.consumption
            elif not i.is_eca:
                non_eca_sum += i.consumption

        self.eca_result_label.config(text=f"ECA consumption: {eca_sum}")
        self.non_eca_result_label.config(text=f"Non ECA consumption: {non_eca_sum}")

    def recalculate_consumption(self):
        for i in self.path_segments:
            i.consumption = self.calculate_consumption(
                i.loading,
                i.is_eca,
                i.distance,
                i.speed
            )

        self.update_segments()
        self.disable_input()
        self.clear_input()

        eca_sum = 0.0
        non_eca_sum = 0.0
        for i in self.path_segments:
            if i.is_eca:
                eca_sum += i.consumption
            elif not i.is_eca:
                non_eca_sum += i.consumption

        self.eca_result_label.config(text=f"ECA consumption: {eca_sum}")
        self.non_eca_result_label.config(text=f"Non ECA consumption: {non_eca_sum}")

    def activate_input(self):
        self.dist_entry.config(state=tk.ACTIVE)
        self.speed_entry.config(state=tk.ACTIVE)
        self.eca_checkbox.config(state=tk.ACTIVE)
        self.laden_radiobutton.config(state=tk.ACTIVE)
        self.ballast_radiobutton.config(state=tk.ACTIVE)
        self.update_button.config(state=tk.ACTIVE)

    def disable_input(self):
        self.dist_entry.config(state=tk.DISABLED)
        self.speed_entry.config(state=tk.DISABLED)
        self.eca_checkbox.config(state=tk.DISABLED)
        self.laden_radiobutton.config(state=tk.DISABLED)
        self.ballast_radiobutton.config(state=tk.DISABLED)
        self.update_button.config(state=tk.DISABLED)

    def clear_input(self):
        self.dist_entry_var.set("")
        self.speed_entry_var.set("")
        self.eca_var.set(False)
        self.loading_type.set("")

    def calculate_consumption(self, loading_type, eca, distance, speed):
        if distance * speed == 0:
            return 0.0

        j = 1
        if loading_type == "Ballast":
            j = 2

        work_table = self.eca_table
        if not eca:
            work_table = self.non_eca_table

        table_cons = 0
        for i in range(0, len(work_table)):
            if i + 1 == len(work_table) and work_table[i][0] == speed:
                table_cons = work_table[i][j]
                break

            if work_table[i + 1][0] > speed:
                table_cons = (work_table[i][j] +
                              ((work_table[i + 1][j] - work_table[i][j]) / 5) *
                              ((speed - work_table[i][0]) * 10))
                break

        consumption = (distance / speed) / 24 * table_cons
        return round(consumption, 1)

    def save_table(self, filename, table):
        app_support_path = get_application_support_path()
        file_path = os.path.join(app_support_path, filename)

        # Сохраняем таблицу в файл
        with open(file_path, mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for row in table:
                writer.writerow([float(row[0]), float(row[1]), float(row[2])])

    def edit_view_open(self):
        EditView(self)
