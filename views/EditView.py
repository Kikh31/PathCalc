import tkinter as tk
import tkinter.ttk as ttk


class EditView(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Edit Tables")
        self.parent = parent

        self._eca_table = self.parent.eca_table.copy()
        self._non_eca_table = self.parent.non_eca_table.copy()

        self.create_widgets()

    def create_widgets(self):
        # ECA spinbox
        self.table_rows = tk.IntVar(value=len(self.parent.eca_table))
        self.eca_spinbox = ttk.Spinbox(self, from_=1, to=30, textvariable=self.table_rows, state="readonly",
                                       command=self.update_rows)
        self.eca_spinbox.pack()

        # ECA frame
        self.eca_frame = ttk.Frame(self)
        self.eca_frame.pack()

        # ECA label
        self.eca_label = tk.Label(self.eca_frame, text="ECA Table")
        self.eca_label.pack(pady=5)

        # ECA scrollbar
        self.eca_scrollbar = ttk.Scrollbar(self.eca_frame, orient=tk.VERTICAL)
        self.eca_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # ECA table
        columns = ('Speed', 'Laden Cons', 'Ballast Cons')

        self.eca_tree = ttk.Treeview(self.eca_frame, columns=columns, show='headings', selectmode=tk.BROWSE,
                                     yscrollcommand=self.eca_scrollbar.set)
        self.eca_tree.heading('Speed', text='Speed')
        self.eca_tree.heading('Laden Cons', text='Laden Cons')
        self.eca_tree.heading('Ballast Cons', text='Ballast Cons')
        self.eca_tree.pack(pady=5, fill=tk.BOTH, expand=True)

        self.eca_scrollbar.config(command=self.eca_tree.yview)

        self.load_eca_table()

        self.eca_tree.bind("<<TreeviewSelect>>", self.eca_item_selected)

        # NON ECA frame
        self.non_eca_frame = ttk.Frame(self)
        self.non_eca_frame.pack()

        # NON ECA label
        self.non_eca_label = tk.Label(self.non_eca_frame, text="Non-ECA Table")
        self.non_eca_label.pack(pady=5)

        # NON ECA scrollbar
        self.non_eca_scrollbar = ttk.Scrollbar(self.non_eca_frame, orient=tk.VERTICAL)
        self.non_eca_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # NON ECA table
        self.non_eca_tree = ttk.Treeview(self.non_eca_frame, columns=columns, show='headings', selectmode=tk.BROWSE,
                                         yscrollcommand=self.non_eca_scrollbar.set)
        self.non_eca_tree.heading('Speed', text='Speed')
        self.non_eca_tree.heading('Laden Cons', text='Laden Cons')
        self.non_eca_tree.heading('Ballast Cons', text='Ballast Cons')
        self.non_eca_tree.pack(pady=5, fill=tk.BOTH, expand=True)

        self.non_eca_scrollbar.config(command=self.non_eca_tree.yview)

        self.load_non_eca_table()

        self.non_eca_tree.bind("<<TreeviewSelect>>", self.non_eca_item_selected)

        # Input Frame
        self.input_frame = ttk.Frame(self)
        self.input_frame.pack()

        self.speed_entry_var = tk.DoubleVar()
        self.speed_entry = ttk.Entry(self.input_frame, width=10, state=tk.DISABLED, textvariable=self.speed_entry_var)
        self.speed_entry.grid(row=0, column=0)

        self.laden_entry_var = tk.DoubleVar()
        self.laden_entry = ttk.Entry(self.input_frame, width=10, state=tk.DISABLED, textvariable=self.laden_entry_var)
        self.laden_entry.grid(row=0, column=1)

        self.ballast_entry_var = tk.DoubleVar()
        self.ballast_entry = ttk.Entry(self.input_frame, width=10, state=tk.DISABLED,
                                       textvariable=self.ballast_entry_var)
        self.ballast_entry.grid(row=0, column=2)

        # Update row
        self.update_row_button = ttk.Button(self.input_frame, text="Обновить строку", state=tk.DISABLED,
                                        command=self.update_selected)
        self.update_row_button.grid(row=1, column=0, columnspan=3)

        # Update tables
        self.update_tables_button = ttk.Button(self, text="Обновить таблицы", command=self.save_changes)
        self.update_tables_button.pack(pady=30)



    def load_eca_table(self):
        for row in self.eca_tree.get_children():
            self.eca_tree.delete(row)

        i = 0
        for row in self._eca_table:
            self.eca_tree.insert('', 'end', iid=f'a{i}', values=(row[0], row[1], row[2]))
            i += 1

    def load_non_eca_table(self):
        for row in self.non_eca_tree.get_children():
            self.non_eca_tree.delete(row)

        i = 0
        for row in self._non_eca_table:
            self.non_eca_tree.insert('', 'end', iid=f'b{i}', values=(row[0], row[1], row[2]))
            i += 1

    def save_changes(self):
        eca_data = []
        for row in self.eca_tree.get_children():
            values = self.eca_tree.item(row, 'values')
            eca_data.append([float(values[0]), float(values[1]), float(values[2])])
        self.parent.eca_table = eca_data
        self.parent.save_table('eca_table.csv', self.parent.eca_table)

        non_eca_data = []
        for row in self.non_eca_tree.get_children():
            values = self.non_eca_tree.item(row, 'values')
            non_eca_data.append([float(values[0]), float(values[1]), float(values[2])])
        self.parent.non_eca_table = non_eca_data
        self.parent.save_table('non_eca_table.csv', self.parent.non_eca_table)

        self.parent.recalculate_consumption()

        self.destroy()

    def update_rows(self):
        current_len = len(self._eca_table)
        new_len = self.table_rows.get()

        if new_len > current_len:
            for i in range(new_len - current_len):
                self._eca_table.append([0.0, 0.0, 0.0])
                self._non_eca_table.append([0.0, 0.0, 0.0])
        elif new_len < current_len:
            self._eca_table = self._eca_table[:new_len]
            self._non_eca_table = self._non_eca_table[:new_len]

        self.load_eca_table()
        self.load_non_eca_table()

    def eca_item_selected(self, event):
        selected_item = self.eca_tree.selection()

        if not selected_item:
            return

        for item in self.non_eca_tree.selection():
            self.non_eca_tree.selection_remove(item)

        self.index = selected_item[0]
        self.items = self.eca_tree.item(self.index)["values"]

        self.speed_entry_var.set(self.items[0])
        self.laden_entry_var.set(self.items[1])
        self.ballast_entry_var.set(self.items[2])

        self.activate_input()

    def non_eca_item_selected(self, event):
        selected_item = self.non_eca_tree.selection()

        if not selected_item:
            return

        for item in self.eca_tree.selection():
            self.eca_tree.selection_remove(item)

        self.index = selected_item[0]
        self.items = self.non_eca_tree.item(self.index)["values"]

        self.speed_entry_var.set(self.items[0])
        self.laden_entry_var.set(self.items[1])
        self.ballast_entry_var.set(self.items[2])

        self.activate_input()

    def update_selected(self):
        speed = self.speed_entry_var.get()
        laden_cons = self.laden_entry_var.get()
        ballast_cons = self.ballast_entry_var.get()

        if self.index[0] == 'a':
            self._eca_table[int(self.index[1:])] = [speed, laden_cons, ballast_cons]
        elif self.index[0] == 'b':
            self._non_eca_table[int(self.index[1:])] = [speed, laden_cons, ballast_cons]

        self.update_rows()
        self.disable_input()
        self.clear_input()

    def activate_input(self):
        self.speed_entry.config(state=tk.ACTIVE)
        self.laden_entry.config(state=tk.ACTIVE)
        self.ballast_entry.config(state=tk.ACTIVE)
        self.update_row_button.config(state=tk.ACTIVE)

    def disable_input(self):
        self.speed_entry.config(state=tk.DISABLED)
        self.laden_entry.config(state=tk.DISABLED)
        self.ballast_entry.config(state=tk.DISABLED)
        self.update_row_button.config(state=tk.DISABLED)

    def clear_input(self):
        self.speed_entry_var.set(0.0)
        self.laden_entry_var.set(0.0)
        self.ballast_entry_var.set(0.0)
