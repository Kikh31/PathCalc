import tkinter as tk
import tkinter.ttk as ttk

class AllocationView(tk.Toplevel):
    def __init__(self, parent, eca_consumption_t, non_eca_consumption_t):
        super().__init__(parent)
        self.parent = parent
        self.title("Allocate consumption")

        self.eca_consumption_t = float(eca_consumption_t)
        self.non_eca_consumption_t = float(non_eca_consumption_t)

        # Берём только активные танки
        self.eca_list = [t for t in self.parent.eca_tanks if t.active]
        self.non_list = [t for t in self.parent.non_eca_tanks if t.active]

        # Результаты preview
        self.eca_preview = []
        self.non_preview = []
        self.eca_def = (0.0, 0.0)
        self.non_def = (0.0, 0.0)

        self._build_ui()
        self._preview_all()

    def _build_ui(self):
        root = ttk.Frame(self)
        root.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        top = ttk.Frame(root)
        top.pack(fill=tk.X)

        eca_m3 = round(self.eca_consumption_t / self.parent.eca_density, 3) if self.parent.eca_density > 0 else 0.0
        non_m3 = round(self.non_eca_consumption_t / self.parent.non_eca_density,
                       3) if self.parent.non_eca_density > 0 else 0.0

        ttk.Label(top, text=f"ECA consumption: {round(self.eca_consumption_t, 2)} t ({eca_m3} m³)").pack(side=tk.LEFT)
        ttk.Label(top, text=f"Non-ECA consumption: {round(self.non_eca_consumption_t, 2)} t ({non_m3} m³)").pack(
            side=tk.LEFT, padx=20)

        body = ttk.Frame(root)
        body.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.eca_block = self._make_block(body, "ECA (active tanks)", which="eca")
        self.eca_block.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.non_block = self._make_block(body, "Non-ECA (active tanks)", which="non")
        self.non_block.pack(fill=tk.BOTH, expand=True)

        bottom = ttk.Frame(root)
        bottom.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(bottom, text="Apply changes", command=self._apply).pack(side=tk.RIGHT)
        ttk.Button(bottom, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=8)

    def _make_block(self, parent, title, which):
        frame = ttk.LabelFrame(parent, text=title)

        # left: order list
        left = ttk.Frame(frame)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        cols = ("name", "current", "capacity")
        tree = ttk.Treeview(left, columns=cols, show="headings", height=10, selectmode=tk.BROWSE)
        tree.heading("name", text="Tank")
        tree.heading("current", text="Current m³")
        tree.heading("capacity", text="Cap m³")
        tree.column("name", width=140)
        tree.column("current", width=90, anchor="center")
        tree.column("capacity", width=90, anchor="center")
        tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        btns = ttk.Frame(left)
        btns.pack(fill=tk.X, pady=(6, 0))

        ttk.Button(btns, text="Up", command=lambda: self._move(which, -1)).pack(side=tk.LEFT)
        ttk.Button(btns, text="Down", command=lambda: self._move(which, +1)).pack(side=tk.LEFT, padx=6)

        # right: preview table
        right = ttk.Frame(frame)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))

        pcols = ("tank", "used_m3", "used_t", "rem_m3")
        preview = ttk.Treeview(right, columns=pcols, show="headings", height=10)
        preview.heading("tank", text="Tank")
        preview.heading("used_m3", text="Consume m³")
        preview.heading("used_t", text="Consume t")
        preview.heading("rem_m3", text="Remaining m³")
        preview.column("tank", width=140)
        preview.column("used_m3", width=95, anchor="center")
        preview.column("used_t", width=80, anchor="center")
        preview.column("rem_m3", width=105, anchor="center")
        preview.pack(fill=tk.BOTH, expand=True)

        deficit_label = ttk.Label(right, text="")
        deficit_label.pack(anchor="w", pady=(6, 0))

        # save refs
        if which == "eca":
            self.eca_order_tree = tree
            self.eca_preview_tree = preview
            self.eca_deficit_label = deficit_label
        else:
            self.non_order_tree = tree
            self.non_preview_tree = preview
            self.non_deficit_label = deficit_label

        self._load_order_tree(which)
        return frame

    def _load_order_tree(self, which):
        if which == "eca":
            tree = self.eca_order_tree
            data = self.eca_list
        else:
            tree = self.non_order_tree
            data = self.non_list

        tree.delete(*tree.get_children())
        for i, t in enumerate(data):
            tree.insert("", "end", iid=str(i), values=(t.name, round(t.current_m3, 3), round(t.capacity_m3, 3)))

        # auto select first
        if data:
            tree.selection_set("0")

    def _move(self, which, direction):
        if which == "eca":
            tree = self.eca_order_tree
            data = self.eca_list
        else:
            tree = self.non_order_tree
            data = self.non_list

        sel = tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(data):
            return

        data[idx], data[new_idx] = data[new_idx], data[idx]
        self._load_order_tree(which)
        tree.selection_set(str(new_idx))
        self._preview_all()

    def _preview_all(self):
        # ECA
        self.eca_preview, def_m3, def_t = self.parent.allocate_consumption_sequential(
            self.eca_list, self.eca_consumption_t, self.parent.eca_density
        )
        self.eca_def = (def_m3, def_t)
        self._render_preview("eca")

        # Non
        self.non_preview, def_m3, def_t = self.parent.allocate_consumption_sequential(
            self.non_list, self.non_eca_consumption_t, self.parent.non_eca_density
        )
        self.non_def = (def_m3, def_t)
        self._render_preview("non")

    def _render_preview(self, which):
        if which == "eca":
            tree = self.eca_preview_tree
            deficit_label = self.eca_deficit_label
            preview = self.eca_preview
            def_m3, def_t = self.eca_def
        else:
            tree = self.non_preview_tree
            deficit_label = self.non_deficit_label
            preview = self.non_preview
            def_m3, def_t = self.non_def
        tree.delete(*tree.get_children())

        for i, row in enumerate(preview):
            t = row["tank"]
            tree.insert("", "end", iid=str(i), values=(
                t.name, row["used_m3"], row["used_t"], row["remaining_m3"]
            ))

        if def_m3 > 0:
            deficit_label.config(text=f"DEFICIT: {def_t} t ({def_m3} m³)")
        else:
            deficit_label.config(text="")

    def _apply(self):
        # Применяем к реальным TankModel в parent по ссылкам (объекты те же)
        for row in self.eca_preview:
            row["tank"].current_m3 = float(row["remaining_m3"])
        for row in self.non_preview:
            row["tank"].current_m3 = float(row["remaining_m3"])

        # сохраняем
        self.parent.save_tanks_data()

        # обновляем order to fill по текущим итогам расхода (как было)
        self.parent.update_order_labels(self.eca_consumption_t, self.non_eca_consumption_t)

        self.destroy()