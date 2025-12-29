# snmpsim/gui/oid_editor.py

import tkinter as tk
from tkinter import ttk, messagebox

SNMP_TYPES = ["Integer", "Gauge", "Counter", "OctetString"]

class OIDEditor(ttk.Frame):
    def __init__(self, parent, device, on_apply=None):
        super().__init__(parent)
        self.device = device
        self.on_apply = on_apply

        self._build_ui()
        self._refresh_table()

    def _build_ui(self):
        self.tree = ttk.Treeview(
            self,
            columns=("oid", "type", "value"),
            show="headings",
            height=10
        )

        self.tree.heading("oid", text="OID")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("value", text="Valor")

        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        form = ttk.Frame(self)
        form.pack(fill="x", padx=5)

        ttk.Label(form, text="OID").grid(row=0, column=0)
        ttk.Label(form, text="Tipo").grid(row=0, column=1)
        ttk.Label(form, text="Valor").grid(row=0, column=2)

        self.oid_entry = ttk.Entry(form, width=30)
        self.type_combo = ttk.Combobox(form, values=SNMP_TYPES, width=15)
        self.value_entry = ttk.Entry(form, width=20)

        self.oid_entry.grid(row=1, column=0, padx=2)
        self.type_combo.grid(row=1, column=1, padx=2)
        self.value_entry.grid(row=1, column=2, padx=2)

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=5)

        ttk.Button(btns, text="Agregar / Actualizar", command=self.add_or_update).pack(side="left", padx=5)
        ttk.Button(btns, text="Eliminar", command=self.delete_selected).pack(side="left")
        ttk.Button(btns, text="Aplicar en caliente", command=self.apply_live).pack(side="right")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for oid, (typ, val) in self.device.oids.items():
            self.tree.insert("", "end", values=(oid, typ, val))

    def add_or_update(self):
        oid = self.oid_entry.get().strip()
        typ = self.type_combo.get()
        val = self.value_entry.get().strip()

        if not oid or not typ:
            messagebox.showerror("Error", "OID y Tipo son obligatorios")
            return

        self.device.set_oid(oid, typ, val)
        self._refresh_table()

    def delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            return

        oid = self.tree.item(sel[0])["values"][0]
        self.device.delete_oid(oid)
        self._refresh_table()

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return

        oid, typ, val = self.tree.item(sel[0])["values"]
        self.oid_entry.delete(0, tk.END)
        self.value_entry.delete(0, tk.END)

        self.oid_entry.insert(0, oid)
        self.type_combo.set(typ)
        self.value_entry.insert(0, val)

    def apply_live(self):
        if self.on_apply:
            self.on_apply(self.device)
        messagebox.showinfo("SNMPSim", "Valores aplicados en ejecución")
