import tkinter as tk
import tkinter.ttk as ttk

from models.TankModel import TankModel


class TanksView(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Tanks")
        self.parent = parent

        # Локальные копии: меняем здесь, в MainView пишем только по Save
        self._eca_tanks = [TankModel.from_dict(t.to_dict()) for t in self.parent.eca_tanks]
        self._non_eca_tanks = [TankModel.from_dict(t.to_dict()) for t in self.parent.non_eca_tanks]

        self._eca_density = tk.DoubleVar(value=float(self.parent.eca_density))
        self._non_eca_density = tk.DoubleVar(value=float(self.parent.non_eca_density))

        self._selected_table = None  # "eca" / "non"
        self._selected_iid = None

        # Явный выбор, куда добавлять новый танк
        self.add_target = tk.StringVar(value="eca")

        self.create_widgets()
        self.load_tables()

    def create_widgets(self):
        # Density frame
        density_frame = ttk.LabelFrame(self, text="Fuel density (t/m³)")
        density_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Label(density_frame, text="ECA:").grid(row=0, column=0, sticky="w")
        ttk.Entry(density_frame, width=10, textvariable=self._eca_density).grid(row=0, column=1, padx=5)

        ttk.Label(density_frame, text="Non-ECA:").grid(row=0, column=2, sticky="w", padx=(15, 0))
        ttk.Entry(density_frame, width=10, textvariable=self._non_eca_density).grid(row=0, column=3, padx=5)

        # Tables frame
        tables_frame = ttk.Frame(self)
        tables_frame.pack(fill=tk.BOTH, expand=True, padx=10)

        # --- ECA table
        eca_frame = ttk.LabelFrame(tables_frame, text="ECA Tanks")
        eca_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.eca_tree = self._make_tree(eca_frame)
        eca_scroll = ttk.Scrollbar(eca_frame, orient=tk.VERTICAL, command=self.eca_tree.yview)
        self.eca_tree.configure(yscrollcommand=eca_scroll.set)

        self.eca_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        eca_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # --- Non-ECA table
        non_frame = ttk.LabelFrame(tables_frame, text="Non-ECA Tanks")
        non_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.non_eca_tree = self._make_tree(non_frame)
        non_scroll = ttk.Scrollbar(non_frame, orient=tk.VERTICAL, command=self.non_eca_tree.yview)
        self.non_eca_tree.configure(yscrollcommand=non_scroll.set)

        self.non_eca_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        non_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Визуальные теги для строк
        self.eca_tree.tag_configure("inactive", foreground="gray50")
        self.non_eca_tree.tag_configure("inactive", foreground="gray50")

        # Bindings (ВАЖНО: на Treeview, не на frame)
        # Bindings
        self.eca_tree.bind("<Button-1>", lambda e: self._prepare_focus_and_clear("eca"), add=True)
        self.non_eca_tree.bind("<Button-1>", lambda e: self._prepare_focus_and_clear("non"), add=True)

        self.eca_tree.bind("<<TreeviewSelect>>", lambda e: self.on_select("eca"))
        self.non_eca_tree.bind("<<TreeviewSelect>>", lambda e: self.on_select("non"))

        self.eca_tree.bind("<Double-1>", lambda e: self.toggle_active_by_event("eca", e))
        self.non_eca_tree.bind("<Double-1>", lambda e: self.toggle_active_by_event("non", e))

        # Editor
        editor = ttk.LabelFrame(self, text="Selected tank")
        editor.pack(fill=tk.X, padx=10, pady=10)

        self.name_var = tk.StringVar()
        self.current_var = tk.DoubleVar(value=0.0)
        self.capacity_var = tk.DoubleVar(value=0.0)

        ttk.Label(editor, text="Name").grid(row=0, column=0, sticky="w")
        ttk.Entry(editor, width=18, textvariable=self.name_var).grid(row=0, column=1, padx=5)

        ttk.Label(editor, text="Current (m³)").grid(row=0, column=2, sticky="w", padx=(15, 0))
        ttk.Entry(editor, width=10, textvariable=self.current_var).grid(row=0, column=3, padx=5)

        ttk.Label(editor, text="Capacity (m³)").grid(row=0, column=4, sticky="w", padx=(15, 0))
        ttk.Entry(editor, width=10, textvariable=self.capacity_var).grid(row=0, column=5, padx=5)

        # Add target (явно)
        add_target_frame = ttk.Frame(editor)
        add_target_frame.grid(row=1, column=0, columnspan=6, sticky="w", pady=(8, 0))

        ttk.Label(add_target_frame, text="Add to:").pack(side=tk.LEFT)
        ttk.Radiobutton(add_target_frame, text="ECA", value="eca", variable=self.add_target).pack(side=tk.LEFT, padx=6)
        ttk.Radiobutton(add_target_frame, text="Non-ECA", value="non", variable=self.add_target).pack(side=tk.LEFT)

        # Buttons
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(btns, text="Add tank", command=self.add_tank).pack(side=tk.LEFT)
        ttk.Button(btns, text="Update selected", command=self.update_tank).pack(side=tk.LEFT, padx=8)
        ttk.Button(btns, text="Delete selected", command=self.delete_tank).pack(side=tk.LEFT)

        ttk.Button(btns, text="Save", command=self.save_and_close).pack(side=tk.RIGHT)

        hint = ttk.Label(self, text='Tip: double-click a row to toggle "Active" (Yes/No)')
        hint.pack(pady=(0, 10))

    def _make_tree(self, parent):
        columns = ("name", "current", "capacity", "active")
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode=tk.BROWSE)

        tree.heading("name", text="Tank name")
        tree.heading("current", text="Current (m³)")
        tree.heading("capacity", text="Capacity (m³)")
        tree.heading("active", text="Active")

        tree.column("name", width=160)
        tree.column("current", width=110, anchor="center")
        tree.column("capacity", width=110, anchor="center")
        tree.column("active", width=70, anchor="center")

        return tree

    def load_tables(self):
        for t in self.eca_tree.get_children():
            self.eca_tree.delete(t)
        for t in self.non_eca_tree.get_children():
            self.non_eca_tree.delete(t)

        for i, tank in enumerate(self._eca_tanks):
            tags = ("inactive",) if not tank.active else ()
            self.eca_tree.insert("", "end", iid=f"e{i}", values=self._tank_row(tank), tags=tags)

        for i, tank in enumerate(self._non_eca_tanks):
            tags = ("inactive",) if not tank.active else ()
            self.non_eca_tree.insert("", "end", iid=f"n{i}", values=self._tank_row(tank), tags=tags)

    def _tank_row(self, tank: TankModel):
        return (
            tank.name,
            round(float(tank.current_m3), 3),
            round(float(tank.capacity_m3), 3),
            "✅" if tank.active else "⛔",
        )

    def _prepare_focus_and_clear(self, which):
        """
        Перед тем как Treeview выберет строку:
        - даём фокус текущей таблице (чтобы выделение рисовалось)
        - очищаем выделение в другой таблице
        - обновляем add_target, чтобы "Add tank" шёл туда же, куда кликаешь
        """
        if which == "eca":
            self.eca_tree.focus_set()
            self.non_eca_tree.selection_remove(self.non_eca_tree.selection())
            self.add_target.set("eca")
        else:
            self.non_eca_tree.focus_set()
            self.eca_tree.selection_remove(self.eca_tree.selection())
            self.add_target.set("non")

    def on_select(self, which):
        tree = self.eca_tree if which == "eca" else self.non_eca_tree

        sel = tree.selection()
        if not sel:
            return

        self._selected_table = which
        self._selected_iid = sel[0]

        # Важно: фокус, чтобы подсветка была видимой
        tree.focus_set()
        tree.focus(self._selected_iid)

        values = tree.item(self._selected_iid)["values"]
        self.name_var.set(values[0])
        self.current_var.set(float(values[1]))
        self.capacity_var.set(float(values[2]))

    def _get_list_and_index(self):
        if not self._selected_table or not self._selected_iid:
            return None, None
        if self._selected_table == "eca":
            idx = int(self._selected_iid[1:])
            return self._eca_tanks, idx
        idx = int(self._selected_iid[1:])
        return self._non_eca_tanks, idx

    def toggle_active_by_event(self, which, event):
        tree = self.eca_tree if which == "eca" else self.non_eca_tree
        row_iid = tree.identify_row(event.y)
        if not row_iid:
            return

        # выбрать строку (чтобы editor обновился)
        tree.selection_set(row_iid)
        self._selected_table = which
        self._selected_iid = row_iid

        if which == "eca":
            idx = int(row_iid[1:])
            self._eca_tanks[idx].active = not self._eca_tanks[idx].active
        else:
            idx = int(row_iid[1:])
            self._non_eca_tanks[idx].active = not self._non_eca_tanks[idx].active

        self.load_tables()
        # вернуть selection обратно после перезагрузки
        tree.selection_set(row_iid)

    def add_tank(self):
        which = self.add_target.get()  # теперь всегда явно выбран

        tank = TankModel(
            name=self.name_var.get().strip() or "New tank",
            current_m3=float(self.current_var.get()),
            capacity_m3=float(self.capacity_var.get()),
            active=True,
        )

        if which == "eca":
            self._eca_tanks.append(tank)
        else:
            self._non_eca_tanks.append(tank)

        self.load_tables()

    def update_tank(self):
        lst, idx = self._get_list_and_index()
        if lst is None:
            return

        lst[idx].name = self.name_var.get().strip() or lst[idx].name
        lst[idx].current_m3 = float(self.current_var.get())
        lst[idx].capacity_m3 = float(self.capacity_var.get())

        self.load_tables()

        # восстановим выделение
        if self._selected_table == "eca":
            self.eca_tree.selection_set(f"e{idx}")
        else:
            self.non_eca_tree.selection_set(f"n{idx}")

    def delete_tank(self):
        lst, idx = self._get_list_and_index()
        if lst is None:
            return

        del lst[idx]
        self._selected_iid = None
        self._selected_table = None

        self.name_var.set("")
        self.current_var.set(0.0)
        self.capacity_var.set(0.0)

        self.load_tables()

    def save_and_close(self):
        eca_d = float(self._eca_density.get())
        non_d = float(self._non_eca_density.get())

        if eca_d <= 0:
            eca_d = 1.0
        if non_d <= 0:
            non_d = 1.0

        self.parent.eca_density = eca_d
        self.parent.non_eca_density = non_d
        self.parent.eca_tanks = self._eca_tanks
        self.parent.non_eca_tanks = self._non_eca_tanks

        self.parent.save_tanks_data()
        self.parent.update_order_labels_from_current_results()

        self.destroy()
