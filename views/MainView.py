import shutil
import subprocess
import sys
import tkinter as tk
import tkinter.ttk as ttk
import csv
import os

from models.PathModel import PathModel
from views.EditView import EditView
from views.AllocationView import AllocationView

import json
from models.TankModel import TankModel
from views.TanksView import TanksView


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

        self.eca_density = 1.0
        self.non_eca_density = 1.0
        self.last_eca_consumption_t = 0.0
        self.last_non_eca_consumption_t = 0.0
        self.eca_tanks = []
        self.non_eca_tanks = []
        self.load_tanks_data()


        self.create_widgets()

        self.eca_result_label.config(text="ECA consumption: 0.0 t (0.0 m³)")
        self.non_eca_result_label.config(text="Non ECA consumption: 0.0 t (0.0 m³)")
        self.update_order_labels(0.0, 0.0)
        self.update_active_rob_after_route_labels()

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

        self.tanks_button = ttk.Button(self.spinbox_frame, text="Tanks", command=self.tanks_view_open)
        self.tanks_button.grid(row=0, column=3, padx=(8, 0))


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

        self.eca_order_label = ttk.Label(self.result_frame, text="ECA order to fill: 0 t (0 m³)")
        self.eca_order_label.pack(pady=(10, 0))

        self.non_eca_order_label = ttk.Label(self.result_frame, text="Non-ECA order to fill: 0 t (0 m³)")
        self.non_eca_order_label.pack()

        self.eca_rob_label = ttk.Label(self.result_frame, text="Active ECA ROB: 0.0 t (0.0 m³)")
        self.eca_rob_label.pack(pady=(12, 0))

        self.non_eca_rob_label = ttk.Label(self.result_frame, text="Active Non-ECA ROB: 0.0 t (0.0 m³)")
        self.non_eca_rob_label.pack()

        self.order_warn_label = ttk.Label(self.result_frame, text="")
        self.order_warn_label.pack(pady=(6, 0))

        self.allocate_button = ttk.Button(
            self.spinbox_frame, text="Allocate", state=tk.DISABLED,
            command=lambda: self.allocation_view_open()
        )
        self.allocate_button.grid(row=0, column=4, padx=(8, 0))


    def update_segments(self):
        self.clear_input()
        self.disable_input()
        self.allocate_button.config(state=tk.DISABLED)

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

        eca_sum = 0.0
        non_eca_sum = 0.0
        for seg in self.path_segments:
            if seg.is_eca:
                eca_sum += seg.consumption
            else:
                non_eca_sum += seg.consumption

        self.last_eca_consumption_t = float(eca_sum)
        self.last_non_eca_consumption_t = float(non_eca_sum)

        eca_m3 = round(eca_sum / self.eca_density, 3) if self.eca_density > 0 else 0.0
        non_m3 = round(non_eca_sum / self.non_eca_density, 3) if self.non_eca_density > 0 else 0.0

        self.eca_result_label.config(text=f"ECA consumption: {round(eca_sum, 2)} t ({eca_m3} m³)")
        self.non_eca_result_label.config(text=f"Non ECA consumption: {round(non_eca_sum, 2)} t ({non_m3} m³)")

        self.update_order_labels(eca_sum, non_eca_sum)
        self.update_active_rob_after_route_labels()

        # Allocate: включаем только если есть расход
        if len(self.path_segments) > 0 and (eca_sum > 0 or non_eca_sum > 0):
            self.allocate_button.config(state=tk.ACTIVE)
        else:
            self.allocate_button.config(state=tk.DISABLED)

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

        self.last_eca_consumption_t = float(eca_sum)
        self.last_non_eca_consumption_t = float(non_eca_sum)

        eca_m3 = round(eca_sum / self.eca_density, 3) if self.eca_density > 0 else 0.0
        non_m3 = round(non_eca_sum / self.non_eca_density, 3) if self.non_eca_density > 0 else 0.0

        self.eca_result_label.config(text=f"ECA consumption: {round(eca_sum, 2)} t ({eca_m3} m³)")
        self.non_eca_result_label.config(text=f"Non ECA consumption: {round(non_eca_sum, 2)} t ({non_m3} m³)")

        self.update_order_labels(eca_sum, non_eca_sum)
        self.update_active_rob_after_route_labels()
        self.allocate_button.config(state=tk.ACTIVE)


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

        self.last_eca_consumption_t = float(eca_sum)
        self.last_non_eca_consumption_t = float(non_eca_sum)

        eca_m3 = round(eca_sum / self.eca_density, 3) if self.eca_density > 0 else 0.0
        non_m3 = round(non_eca_sum / self.non_eca_density, 3) if self.non_eca_density > 0 else 0.0

        self.eca_result_label.config(text=f"ECA consumption: {round(eca_sum, 2)} t ({eca_m3} m³)")
        self.non_eca_result_label.config(text=f"Non ECA consumption: {round(non_eca_sum, 2)} t ({non_m3} m³)")

        self.update_order_labels(eca_sum, non_eca_sum)
        self.update_active_rob_after_route_labels()
        self.allocate_button.config(state=tk.ACTIVE)


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

    def tanks_data_path(self):
        app_support_path = get_application_support_path()
        return os.path.join(app_support_path, "tanks_data.json")

    def load_tanks_data(self):
        path = self.tanks_data_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.eca_density = float(data.get("eca_density", 1.0))
            self.non_eca_density = float(data.get("non_eca_density", 1.0))

            self.eca_tanks = [TankModel.from_dict(x) for x in data.get("eca_tanks", [])]
            self.non_eca_tanks = [TankModel.from_dict(x) for x in data.get("non_eca_tanks", [])]
        except Exception:
            # Если файл битый — просто стартуем с дефолтами
            self.eca_density = 1.0
            self.non_eca_density = 1.0
            self.eca_tanks = []
            self.non_eca_tanks = []

    def save_tanks_data(self):
        data = {
            "eca_density": float(self.eca_density),
            "non_eca_density": float(self.non_eca_density),
            "eca_tanks": [t.to_dict() for t in self.eca_tanks],
            "non_eca_tanks": [t.to_dict() for t in self.non_eca_tanks],
        }
        with open(self.tanks_data_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _active_totals_m3(self, tanks):
        total_current = 0.0
        total_capacity = 0.0
        for t in tanks:
            if not t.active:
                continue
            total_current += max(0.0, float(t.current_m3))
            total_capacity += max(0.0, float(t.capacity_m3))
        return total_current, total_capacity

    def calc_order_to_fill(self, eca_consumption_t, non_eca_consumption_t):
        """
        Возвращает (eca_order_m3, eca_order_t, non_order_m3, non_order_t, warnings_list)
        Логика: расход уменьшает общий пул активных танков, потом считаем сколько не хватает до их суммарной вместимости.
        """
        warnings = []

        eca_density = float(self.eca_density) if float(self.eca_density) > 0 else 1.0
        non_density = float(self.non_eca_density) if float(self.non_eca_density) > 0 else 1.0

        eca_current, eca_capacity = self._active_totals_m3(self.eca_tanks)
        non_current, non_capacity = self._active_totals_m3(self.non_eca_tanks)

        eca_used_m3 = float(eca_consumption_t) / eca_density if eca_density else 0.0
        non_used_m3 = float(non_eca_consumption_t) / non_density if non_density else 0.0

        eca_remaining = eca_current - eca_used_m3
        non_remaining = non_current - non_used_m3

        # --- ECA deficit
        if eca_remaining < 0:
            deficit_m3 = -eca_remaining
            deficit_t = deficit_m3 * eca_density
            warnings.append(
                f"ECA fuel is not enough: deficit {round(deficit_t, 2)} t ({round(deficit_m3, 3)} m³)."
            )
            eca_remaining = 0.0

        # --- Non-ECA deficit
        if non_remaining < 0:
            deficit_m3 = -non_remaining
            deficit_t = deficit_m3 * non_density
            warnings.append(
                f"Non-ECA fuel is not enough: deficit {round(deficit_t, 2)} t ({round(deficit_m3, 3)} m³)."
            )
            non_remaining = 0.0

        eca_order_m3 = max(0.0, eca_capacity - eca_remaining)
        non_order_m3 = max(0.0, non_capacity - non_remaining)

        eca_order_t = eca_order_m3 * eca_density
        non_order_t = non_order_m3 * non_density

        return (
            round(eca_order_m3, 3), round(eca_order_t, 2),
            round(non_order_m3, 3), round(non_order_t, 2),
            warnings
        )

    def update_order_labels_from_current_results(self):
        try:
            # "ECA consumption: 12.5 t (12.626 m³)"
            eca_part = self.eca_result_label.cget("text").split(":")[1].strip()
            non_part = self.non_eca_result_label.cget("text").split(":")[1].strip()

            eca_sum = float(eca_part.split("t")[0].strip())
            non_sum = float(non_part.split("t")[0].strip())
        except Exception:
            eca_sum = 0.0
            non_sum = 0.0

        self.update_order_labels(eca_sum, non_sum)

    def update_order_labels(self, eca_sum, non_eca_sum):
        e_m3, e_t, n_m3, n_t, warnings = self.calc_order_to_fill(eca_sum, non_eca_sum)

        self.eca_order_label.config(text=f"ECA order to fill: {e_t} t ({e_m3} m³)")
        self.non_eca_order_label.config(text=f"Non-ECA order to fill: {n_t} t ({n_m3} m³)")

        if warnings:
            self.order_warn_label.config(text=" / ".join(warnings), foreground="red")
        else:
            self.order_warn_label.config(text="", foreground="black")


    def edit_view_open(self):
        EditView(self)

    def tanks_view_open(self):
        TanksView(self)

    def allocate_consumption_sequential(self, tanks, consumption_t, density):
        """
        tanks: список TankModel (уже отфильтрованные активные) в нужном порядке
        consumption_t: расход в тоннах
        density: t/m3
        Возвращает:
          per_tank: list of dict {tank, used_m3, used_t, remaining_m3}
          deficit_m3, deficit_t
        """
        density = float(density) if float(density) > 0 else 1.0
        remaining_need_m3 = float(consumption_t) / density

        per_tank = []
        for t in tanks:
            cur = max(0.0, float(t.current_m3))
            used_m3 = min(cur, remaining_need_m3)
            remaining_need_m3 -= used_m3

            used_t = used_m3 * density
            remaining_m3 = cur - used_m3

            per_tank.append({
                "tank": t,
                "used_m3": round(used_m3, 3),
                "used_t": round(used_t, 2),
                "remaining_m3": round(remaining_m3, 3),
            })

            if remaining_need_m3 <= 1e-12:
                remaining_need_m3 = 0.0
                break

        deficit_m3 = max(0.0, remaining_need_m3)
        deficit_t = deficit_m3 * density

        return per_tank, round(deficit_m3, 3), round(deficit_t, 2)

    def allocation_view_open(self):
        try:
            eca_part = self.eca_result_label.cget("text").split(":")[1].strip()
            non_part = self.non_eca_result_label.cget("text").split(":")[1].strip()

            eca_sum = float(eca_part.split("t")[0].strip())
            non_sum = float(non_part.split("t")[0].strip())
        except Exception:
            eca_sum = 0.0
            non_sum = 0.0

        AllocationView(self, eca_sum, non_sum)

    def update_active_rob_after_route_labels(self):
        eca_cur_m3, _ = self._active_totals_m3(self.eca_tanks)
        non_cur_m3, _ = self._active_totals_m3(self.non_eca_tanks)

        eca_d = float(self.eca_density) if float(self.eca_density) > 0 else 1.0
        non_d = float(self.non_eca_density) if float(self.non_eca_density) > 0 else 1.0

        # расход в m3 по маршруту
        eca_used_m3 = (float(self.last_eca_consumption_t) / eca_d) if eca_d > 0 else 0.0
        non_used_m3 = (float(self.last_non_eca_consumption_t) / non_d) if non_d > 0 else 0.0

        eca_rem_m3 = eca_cur_m3 - eca_used_m3
        non_rem_m3 = non_cur_m3 - non_used_m3

        # если ушли в минус — показываем 0, но можно подсветить дефицит красным
        eca_def_m3 = max(0.0, -eca_rem_m3)
        non_def_m3 = max(0.0, -non_rem_m3)

        eca_rem_m3 = max(0.0, eca_rem_m3)
        non_rem_m3 = max(0.0, non_rem_m3)

        eca_rem_t = round(eca_rem_m3 * eca_d, 2)
        non_rem_t = round(non_rem_m3 * non_d, 2)

        self.eca_rob_label.config(text=f"Active ECA remaining after route: {eca_rem_t} t ({round(eca_rem_m3, 3)} m³)")
        self.non_eca_rob_label.config(
            text=f"Active Non-ECA remaining after route: {non_rem_t} t ({round(non_rem_m3, 3)} m³)")

        # если есть дефицит — делаем эти строки красными, иначе обычными
        if eca_def_m3 > 0:
            self.eca_rob_label.config(foreground="red")
        else:
            self.eca_rob_label.config(foreground="black")

        if non_def_m3 > 0:
            self.non_eca_rob_label.config(foreground="red")
        else:
            self.non_eca_rob_label.config(foreground="black")