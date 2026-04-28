import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


CATEGORIES = {
    "Vivienda": [
        "Renta / Hipoteca",
        "Mantenimiento",
        "Reparaciones",
        "Seguro",
        "Impuestos",
        "Condominio",
    ],
    "Servicios": [
        "Electricidad",
        "Agua",
        "Gas",
        "Internet",
        "Teléfono móvil",
        "Teléfono fijo",
        "TV / Streaming",
    ],
    "Alimentación": [
        "Supermercado",
        "Compras mayoristas",
        "Delivery",
        "Restaurantes",
    ],
    "Transporte": [
        "Transporte público",
        "Combustible",
        "Taxi / Apps",
        "Mantenimiento auto",
        "Seguro auto",
        "Estacionamiento",
        "Peajes",
        "Licencias",
    ],
    "Salud": [
        "Seguro médico",
        "Medicamentos",
        "Consultas",
        "Terapias",
        "Dentista",
        "Exámenes",
    ],
    "Finanzas": ["Préstamos", "Tarjetas de crédito", "Ahorro", "Inversiones", "Comisiones"],
    "Educación": ["Universidad", "Cursos", "Material", "Suscripciones"],
    "Cuidado": ["Higiene", "Peluquería", "Cosméticos"],
    "Entretenimiento": ["Salidas", "Suscripciones", "Gimnasio", "Hobbies", "Viajes"],
    "Familia": ["Colegiatura", "Pensión", "Mascotas"],
    "Otros": ["Ropa", "Regalos", "Donaciones", "Servicios profesionales"],
}

DEFAULT_ROWS = [
    {"Categoria": "Alimentación", "Gasto": "Supermercado", "Presupuesto": 213.00, "Actual": 222.00},
    {"Categoria": "Finanzas", "Gasto": "Tarjetas de crédito", "Presupuesto": 0.00, "Actual": 0.00},
    {"Categoria": "Educación", "Gasto": "Material", "Presupuesto": 1312.00, "Actual": 313.00},
    {"Categoria": "Salud", "Gasto": "Exámenes", "Presupuesto": 1312.00, "Actual": 22223.00},
]

DATA_FILE = "gastos.json"


class BudgetApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Control de gastos")
        self.geometry("1180x720")
        self.minsize(1050, 650)

        self.rows = []
        self.selected_index = None

        self._configure_style()
        self._build_ui()
        self._load_initial_data()
        self._refresh_all()

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background="#f4f7fb")
        style.configure("TLabel", background="#f4f7fb", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"), foreground="#14324a", background="#f4f7fb")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10), foreground="#51606f", background="#f4f7fb")
        style.configure("TButton", font=("Segoe UI", 10))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background="#2b6cb0", foreground="white")
        style.map("Accent.TButton", background=[("active", "#245c97")])
        style.configure("Treeview", rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("Card.TLabelframe", background="#f4f7fb", borderwidth=0)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 11, "bold"), background="#f4f7fb", foreground="#14324a")

    def _build_ui(self):
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        header = ttk.Frame(container)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(header, text="Control de gastos", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Organiza categorías, presupuesto y gasto real en una sola pantalla.",
            style="SubHeader.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        body = ttk.Panedwindow(container, orient=tk.HORIZONTAL)
        body.pack(fill="both", expand=True)

        left = ttk.Frame(body, padding=(0, 0, 12, 0))
        right = ttk.Frame(body)
        body.add(left, weight=2)
        body.add(right, weight=5)

        self._build_catalog_panel(left)
        self._build_form_panel(right)
        self._build_summary_panel(right)

        footer = ttk.Frame(container)
        footer.pack(fill="x", pady=(12, 0))
        ttk.Button(footer, text="Guardar", style="Accent.TButton", command=self.save_data).pack(side="left")
        ttk.Button(footer, text="Cargar", command=self.load_data).pack(side="left", padx=(8, 0))
        ttk.Button(footer, text="Limpiar formulario", command=self.clear_form).pack(side="left", padx=(8, 0))
        ttk.Button(footer, text="Eliminar seleccionado", command=self.delete_selected).pack(side="right")

    def _build_catalog_panel(self, parent):
        frame = ttk.Labelframe(parent, text="Catálogo de categorías", style="Card.TLabelframe", padding=12)
        frame.pack(fill="both", expand=True)

        self.category_list = tk.Listbox(
            frame,
            height=20,
            activestyle="none",
            font=("Segoe UI", 10),
            relief="flat",
            highlightthickness=1,
            highlightbackground="#d8e0ea",
            selectbackground="#2b6cb0",
            selectforeground="white",
        )
        self.category_list.pack(fill="both", expand=True, side="left")
        self.category_list.bind("<<ListboxSelect>>", self.on_category_select)

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.category_list.yview)
        scrollbar.pack(fill="y", side="right")
        self.category_list.configure(yscrollcommand=scrollbar.set)

        for category in CATEGORIES:
            self.category_list.insert(tk.END, category)

        self.category_list.selection_set(0)

        self.items_label = ttk.Label(frame, text="Selecciona una categoría para ver sus gastos.")
        self.items_label.pack(anchor="w", pady=(10, 0))

        self.items_box = tk.Text(
            frame,
            height=11,
            wrap="word",
            font=("Segoe UI", 10),
            relief="flat",
            bg="#ffffff",
            fg="#1f2937",
            highlightthickness=1,
            highlightbackground="#d8e0ea",
            state="disabled",
        )
        self.items_box.pack(fill="both", expand=False, pady=(8, 0))

    def _build_form_panel(self, parent):
        form = ttk.Labelframe(parent, text="Nuevo gasto fijo", style="Card.TLabelframe", padding=12)
        form.pack(fill="x")

        grid = ttk.Frame(form)
        grid.pack(fill="x")

        self.category_var = tk.StringVar(value="Alimentación")
        self.gasto_var = tk.StringVar()
        self.presupuesto_var = tk.StringVar()
        self.actual_var = tk.StringVar()
        self.search_var = tk.StringVar()

        ttk.Label(grid, text="Categoría").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=(0, 6))
        ttk.Label(grid, text="Gasto").grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(0, 6))
        ttk.Label(grid, text="Presupuesto").grid(row=0, column=2, sticky="w", padx=(0, 8), pady=(0, 6))
        ttk.Label(grid, text="Actual").grid(row=0, column=3, sticky="w", pady=(0, 6))

        self.category_combo = ttk.Combobox(grid, textvariable=self.category_var, values=list(CATEGORIES.keys()), state="readonly", width=22)
        self.gasto_combo = ttk.Combobox(grid, textvariable=self.gasto_var, values=[], width=30)
        self.presupuesto_entry = ttk.Entry(grid, textvariable=self.presupuesto_var, width=18)
        self.actual_entry = ttk.Entry(grid, textvariable=self.actual_var, width=18)

        self.category_combo.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.gasto_combo.grid(row=1, column=1, sticky="ew", padx=(0, 8))
        self.presupuesto_entry.grid(row=1, column=2, sticky="ew", padx=(0, 8))
        self.actual_entry.grid(row=1, column=3, sticky="ew")

        grid.columnconfigure(1, weight=2)
        grid.columnconfigure(2, weight=1)
        grid.columnconfigure(3, weight=1)

        buttons = ttk.Frame(form)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Agregar", style="Accent.TButton", command=self.add_row).pack(side="left")
        ttk.Button(buttons, text="Actualizar seleccionado", command=self.update_selected).pack(side="left", padx=(8, 0))
        ttk.Button(buttons, text="Duplicar gasto", command=self.duplicate_selected).pack(side="left", padx=(8, 0))

        search = ttk.Labelframe(parent, text="Búsqueda", style="Card.TLabelframe", padding=12)
        search.pack(fill="x", pady=(12, 0))

        ttk.Label(search, text="Filtrar por categoría o gasto").pack(anchor="w")
        search_row = ttk.Frame(search)
        search_row.pack(fill="x", pady=(6, 0))

        ttk.Entry(search_row, textvariable=self.search_var).pack(side="left", fill="x", expand=True)
        ttk.Button(search_row, text="Filtrar", command=self.refresh_table).pack(side="left", padx=(8, 0))
        ttk.Button(search_row, text="Mostrar todo", command=self.clear_filter).pack(side="left", padx=(8, 0))

    def _build_summary_panel(self, parent):
        summary = ttk.Labelframe(parent, text="Gastos fijos", style="Card.TLabelframe", padding=12)
        summary.pack(fill="both", expand=True, pady=(12, 0))

        columns = ("Categoria", "Gasto", "Presupuesto", "Actual", "Diferencia")
        self.tree = ttk.Treeview(summary, columns=columns, show="headings", selectmode="browse")
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        headings = {
            "Categoria": "Categoría",
            "Gasto": "Gasto",
            "Presupuesto": "Presupuesto",
            "Actual": "Actual",
            "Diferencia": "Diferencia",
        }
        widths = {"Categoria": 140, "Gasto": 190, "Presupuesto": 140, "Actual": 140, "Diferencia": 140}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w", stretch=True)

        scrollbar = ttk.Scrollbar(summary, orient="vertical", command=self.tree.yview)
        scrollbar.pack(fill="y", side="right")
        self.tree.configure(yscrollcommand=scrollbar.set)

        totals_frame = ttk.Frame(parent)
        totals_frame.pack(fill="x", pady=(10, 0))

        self.total_budget_var = tk.StringVar(value="$0.00")
        self.total_actual_var = tk.StringVar(value="$0.00")
        self.total_diff_var = tk.StringVar(value="$0.00")
        self.rows_var = tk.StringVar(value="0 registros")

        self._make_kpi(totals_frame, "Presupuesto total", self.total_budget_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._make_kpi(totals_frame, "Gasto total", self.total_actual_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._make_kpi(totals_frame, "Diferencia", self.total_diff_var).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._make_kpi(totals_frame, "Registros", self.rows_var).pack(side="left", fill="x", expand=True)

    def _make_kpi(self, parent, title, value_var):
        card = ttk.Labelframe(parent, text=title, style="Card.TLabelframe", padding=10)
        ttk.Label(card, textvariable=value_var, font=("Segoe UI", 15, "bold"), foreground="#14324a").pack(anchor="w")
        return card

    def _load_initial_data(self):
        if os.path.exists(DATA_FILE):
            self.load_data(silent=True)
            return
        self.rows = [dict(row) for row in DEFAULT_ROWS]

    def on_category_select(self, event=None):
        selection = self.category_list.curselection()
        if not selection:
            return
        category = self.category_list.get(selection[0])
        self.category_var.set(category)
        self.gasto_combo.configure(values=CATEGORIES.get(category, []))
        if CATEGORIES.get(category):
            self.gasto_var.set(CATEGORIES[category][0])
        self._update_catalog_text(category)

    def _update_catalog_text(self, category):
        items = CATEGORIES.get(category, [])
        text = "\n".join(f"• {item}" for item in items) if items else "Sin elementos."
        self.items_box.configure(state="normal")
        self.items_box.delete("1.0", tk.END)
        self.items_box.insert(tk.END, text)
        self.items_box.configure(state="disabled")
        self.items_label.configure(text=f"Elementos de {category}")

    def _parse_amount(self, value):
        value = value.strip().replace(",", "")
        if not value:
            return 0.0
        return float(value)

    def _current_form_data(self):
        category = self.category_var.get().strip()
        gasto = self.gasto_var.get().strip()
        presupuesto = self._parse_amount(self.presupuesto_var.get())
        actual = self._parse_amount(self.actual_var.get())
        if not category:
            raise ValueError("Selecciona una categoría.")
        if not gasto:
            raise ValueError("Escribe o selecciona un gasto.")
        return {"Categoria": category, "Gasto": gasto, "Presupuesto": presupuesto, "Actual": actual}

    def add_row(self):
        try:
            row = self._current_form_data()
        except ValueError as exc:
            messagebox.showwarning("Validación", str(exc))
            return
        except Exception:
            messagebox.showwarning("Validación", "Revisa que presupuesto y actual sean números válidos.")
            return

        self.rows.append(row)
        self._refresh_all()
        self.clear_form(keep_category=True)

    def update_selected(self):
        if self.selected_index is None:
            messagebox.showinfo("Actualizar", "Selecciona un registro en la tabla.")
            return
        try:
            row = self._current_form_data()
        except ValueError as exc:
            messagebox.showwarning("Validación", str(exc))
            return
        except Exception:
            messagebox.showwarning("Validación", "Revisa que presupuesto y actual sean números válidos.")
            return

        self.rows[self.selected_index] = row
        self._refresh_all(select_index=self.selected_index)

    def duplicate_selected(self):
        if self.selected_index is None:
            messagebox.showinfo("Duplicar", "Selecciona un registro en la tabla.")
            return
        self.rows.append(dict(self.rows[self.selected_index]))
        self._refresh_all(select_index=len(self.rows) - 1)

    def delete_selected(self):
        if self.selected_index is None:
            messagebox.showinfo("Eliminar", "Selecciona un registro en la tabla.")
            return
        del self.rows[self.selected_index]
        self.selected_index = None
        self._refresh_all()
        self.clear_form(keep_category=True)

    def on_row_select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            self.selected_index = None
            return
        item_id = selected[0]
        index = self.tree.index(item_id)
        visible_rows = self._filtered_rows()
        if index >= len(visible_rows):
            return
        row = visible_rows[index]
        self.selected_index = self.rows.index(row)
        self.category_var.set(row["Categoria"])
        self.gasto_var.set(row["Gasto"])
        self.presupuesto_var.set(self._format_plain(row["Presupuesto"]))
        self.actual_var.set(self._format_plain(row["Actual"]))
        self.gasto_combo.configure(values=CATEGORIES.get(row["Categoria"], []))
        self._update_catalog_text(row["Categoria"])

    def clear_form(self, keep_category=False):
        if not keep_category:
            self.category_var.set("Alimentación")
        self.gasto_var.set("")
        self.presupuesto_var.set("")
        self.actual_var.set("")
        self.selected_index = None
        self.tree.selection_remove(self.tree.selection())
        self.gasto_combo.configure(values=CATEGORIES.get(self.category_var.get(), []))
        self._update_catalog_text(self.category_var.get())

    def clear_filter(self):
        self.search_var.set("")
        self.refresh_table()

    def _filtered_rows(self):
        query = self.search_var.get().strip().lower()
        if not query:
            return self.rows
        return [
            row
            for row in self.rows
            if query in row["Categoria"].lower() or query in row["Gasto"].lower()
        ]

    def refresh_table(self, select_index=None):
        self.tree.delete(*self.tree.get_children())
        for row in self._filtered_rows():
            presupuesto = row["Presupuesto"]
            actual = row["Actual"]
            diferencia = presupuesto - actual
            self.tree.insert(
                "",
                tk.END,
                values=(
                    row["Categoria"],
                    row["Gasto"],
                    self._format_currency(presupuesto),
                    self._format_currency(actual),
                    self._format_currency(diferencia),
                ),
            )

        if select_index is not None:
            items = self.tree.get_children()
            if 0 <= select_index < len(items):
                self.tree.selection_set(items[select_index])
                self.tree.focus(items[select_index])

    def _refresh_all(self, select_index=None):
        self.gasto_combo.configure(values=CATEGORIES.get(self.category_var.get(), []))
        self.refresh_table(select_index=select_index)
        self._refresh_totals()
        if self.category_list.curselection():
            current = self.category_list.get(self.category_list.curselection()[0])
            self._update_catalog_text(current)
        else:
            self._update_catalog_text(self.category_var.get())

    def _refresh_totals(self):
        budget = sum(row["Presupuesto"] for row in self.rows)
        actual = sum(row["Actual"] for row in self.rows)
        diff = budget - actual
        self.total_budget_var.set(self._format_currency(budget))
        self.total_actual_var.set(self._format_currency(actual))
        self.total_diff_var.set(self._format_currency(diff))
        self.rows_var.set(f"{len(self.rows)} registros")

    def _format_currency(self, amount):
        return f"DOP {amount:,.2f}"

    def _format_plain(self, amount):
        return f"{amount:.2f}".rstrip("0").rstrip(".") if amount % 1 else f"{int(amount)}"

    def save_data(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as fh:
                json.dump(self.rows, fh, ensure_ascii=False, indent=2)
            messagebox.showinfo("Guardar", f"Datos guardados en {DATA_FILE}.")
        except Exception as exc:
            messagebox.showerror("Guardar", f"No se pudo guardar: {exc}")

    def load_data(self, silent=False):
        path = DATA_FILE
        if not os.path.exists(path):
            if not silent:
                messagebox.showinfo("Cargar", "No existe un archivo guardado todavía.")
            return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            cleaned = []
            for item in data:
                cleaned.append(
                    {
                        "Categoria": str(item.get("Categoria", "")).strip() or "Otros",
                        "Gasto": str(item.get("Gasto", "")).strip(),
                        "Presupuesto": float(item.get("Presupuesto", 0) or 0),
                        "Actual": float(item.get("Actual", 0) or 0),
                    }
                )
            self.rows = cleaned
            self._refresh_all()
            if not silent:
                messagebox.showinfo("Cargar", "Datos cargados correctamente.")
        except Exception as exc:
            if not silent:
                messagebox.showerror("Cargar", f"No se pudo cargar: {exc}")


def main():
    app = BudgetApp()
    app.on_category_select()
    app.mainloop()


if __name__ == "__main__":
    main()
