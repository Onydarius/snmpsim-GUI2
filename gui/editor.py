import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import json

# Mapeo de Tipos SNMP
SNMP_TYPES = {
    "2": "Integer",
    "4": "String (Octet)",
    "64": "IP Address",
    "65": "Counter32",
    "66": "Gauge32",
    "67": "TimeTicks"
}
TAG_BY_NAME = {v: k for k, v in SNMP_TYPES.items()}
OID_SYSNAME = "1.3.6.1.2.1.1.5.0"


class DeviceEditor(ttk.Frame):

    def __init__(self, parent, on_file_renamed=None, on_template_saved=None):
        super().__init__(parent)
        self.on_file_renamed_callback = on_file_renamed
        self.on_template_saved_callback = on_template_saved
        self.current_file_path = None
        self.meta_file_path = None
        self.data = [] 
        
        self._build_ui()

    def _build_ui(self):
        # Notebook Principal
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True)

        # TAB 1: DASHBOARD
        self.tab_dashboard = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_dashboard, text="🎛 Panel de Simulación")
        
        # TAB 2: EDITOR
        self.tab_def = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_def, text="⚙ Configuración y OIDs")

        # Construir layouts (Estructura fija)
        self._build_dashboard_layout()
        self._build_editor_layout()
        
        # Eventos
        self.tabs.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # =======================================================
    # TAB 1: DASHBOARD (LAYOUT)
    # =======================================================
    def _build_dashboard_layout(self):
        self.dash_header = ttk.Frame(self.tab_dashboard, padding=15)
        self.dash_header.pack(fill="x", side="top")
        
        ttk.Separator(self.tab_dashboard, orient="horizontal").pack(fill="x")

        # Canvas y Scroll
        self.canvas = tk.Canvas(self.tab_dashboard, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.tab_dashboard, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        # Bindings para scroll correcto
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.scrollbar.pack(side="right", fill="y")

    def _render_dashboard(self):
        """Dibuja los controles dinámicamente."""
        # Limpiar contenido anterior
        for w in self.dash_header.winfo_children(): w.destroy()
        for w in self.scrollable_frame.winfo_children(): w.destroy()

        if not self.data and not self.current_file_path:
            ttk.Label(self.dash_header, text="Selecciona un dispositivo para comenzar.", font=("Segoe UI", 12)).pack()
            return

        # --- A. INFO CABECERA ---
        filename = os.path.basename(self.current_file_path)
        community = os.path.splitext(filename)[0]
        sysname_item = next((i for i in self.data if i["oid"] == OID_SYSNAME), None)
        device_name = sysname_item['value'] if sysname_item else "Desconocido (Sin sysName)"

        lbl_dev = ttk.Label(self.dash_header, text=device_name, font=("Segoe UI", 16, "bold"), foreground="#007acc")
        lbl_dev.pack(anchor="w")
        
        f_sub = ttk.Frame(self.dash_header)
        f_sub.pack(anchor="w", pady=(5, 0))
        ttk.Label(f_sub, text="Community String:", font=("Segoe UI", 9, "bold"), foreground="#555").pack(side="left")
        ttk.Label(f_sub, text=community, font=("Consolas", 10), background="#e1e1e1").pack(side="left", padx=5)

        # --- B. CONTROLES ---
        found_sensors = False
        for item in self.data:
            if item["oid"] == OID_SYSNAME: continue
            found_sensors = True
            
            display_title = item['name'] if item['name'] else item['oid']
            frame = ttk.LabelFrame(self.scrollable_frame, text=display_title, padding=5)
            frame.pack(fill="x", pady=5, expand=True)

            ctrl_container = ttk.Frame(frame)
            ctrl_container.pack(fill="x")

            ui_type = item.get("ui_type", "Text Entry")

            if ui_type == "Slider" and item['tag'] in ["2", "65", "66", "67"]:
                try: val = int(item['value'])
                except: val = 0
                scale = tk.Scale(ctrl_container, from_=0, to=100, orient="horizontal", showvalue=True)
                scale.set(val)
                scale.pack(fill="x", expand=True)
                scale.bind("<ButtonRelease-1>", lambda e, it=item, s=scale: self._update_realtime(it, int(s.get())))

            elif ui_type == "Toggle" and item['tag'] in ["2"]:
                try: val = int(item['value'])
                except: val = 0
                var = tk.IntVar(value=val)
                chk = ttk.Checkbutton(ctrl_container, text="ON / OFF", variable=var,
                                      command=lambda it=item, v=var: self._update_realtime(it, v.get()))
                chk.pack(anchor="w")
            else:
                entry = ttk.Entry(ctrl_container)
                entry.insert(0, item['value'])
                entry.pack(side="left", fill="x", expand=True)
                ttk.Button(ctrl_container, text="Set", width=4,
                           command=lambda it=item, e=entry: self._update_realtime(it, e.get())).pack(side="left", padx=2)
            
            # Botón Configuración (⚙)
            ttk.Button(ctrl_container, text="⚙", width=3, 
                       command=lambda it=item: EditDialog(self, it, self._on_edit_complete)).pack(side="right", padx=5)

        if not found_sensors:
            ttk.Label(self.scrollable_frame, text="No hay sensores configurados.", foreground="gray").pack(pady=20)

    # =======================================================
    # TAB 2: EDITOR (LAYOUT ROBUSTO)
    # =======================================================
    def _build_editor_layout(self):
        # 1. Contenedor Principal de Configuración
        self.main_config_frame = ttk.LabelFrame(self.tab_def, text="Configuración General", padding=10)
        self.main_config_frame.pack(fill="x", padx=10, pady=10)
        
        # 1.1 Frame Dinámico (Para Community y SysName) - Se limpia en refresh
        self.dynamic_config_frame = ttk.Frame(self.main_config_frame)
        self.dynamic_config_frame.pack(fill="x", pady=(0, 5))
        self.dynamic_config_frame.columnconfigure(1, weight=1)

        # 1.2 Botón Estático "Guardar Plantilla" (NUNCA SE BORRA)
        ttk.Separator(self.main_config_frame, orient="horizontal").pack(fill="x", pady=5)
        btn_tmpl = ttk.Button(self.main_config_frame, text="💾 Guardar configuración actual como Plantilla",
                              command=self._save_as_template)
        btn_tmpl.pack(fill="x", pady=5)

        # 2. Contenedor de Tabla
        list_frame = ttk.LabelFrame(self.tab_def, text="Tabla de OIDs (Raw Data)", padding=5)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Toolbar Estática
        toolbar = ttk.Frame(list_frame)
        toolbar.pack(fill="x", pady=2)
        ttk.Button(toolbar, text="Refrescar Tabla", command=self._refresh_editor_ui).pack(side="right")
        ttk.Button(toolbar, text="+ Nuevo OID", command=self._add_oid_dialog).pack(side="right", padx=5)

        # Treeview Estático
        cols = ("oid", "name", "type", "value", "ui")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings")
        self.tree.heading("oid", text="OID")
        self.tree.heading("name", text="Nombre Meta")
        self.tree.heading("type", text="Tipo")
        self.tree.heading("value", text="Valor")
        self.tree.heading("ui", text="UI")
        
        self.tree.column("oid", width=180)
        self.tree.column("name", width=120)
        self.tree.column("type", width=80)
        self.tree.column("value", width=100)
        self.tree.column("ui", width=80)

        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<Double-1>", self._on_double_click_row)

    def _refresh_editor_ui(self):
        """Actualiza solo los campos dinámicos y la tabla."""
        
        # A. Limpiar SOLO el frame dinámico y la tabla
        for w in self.dynamic_config_frame.winfo_children(): w.destroy()
        self.tree.delete(*self.tree.get_children())

        # Si no hay datos, terminamos (pero la UI estática sigue visible)
        if not self.data and not self.current_file_path:
            ttk.Label(self.dynamic_config_frame, text="No hay archivo cargado.").grid(row=0, column=0)
            return

        # B. Reconstruir campos dinámicos
        
        # 1. Community
        current_filename = os.path.basename(self.current_file_path)
        current_community = os.path.splitext(current_filename)[0]

        ttk.Label(self.dynamic_config_frame, text="Community String:").grid(row=0, column=0, sticky="w")
        e_comm = ttk.Entry(self.dynamic_config_frame)
        e_comm.insert(0, current_community)
        e_comm.grid(row=0, column=1, sticky="ew", padx=10)
        ttk.Button(self.dynamic_config_frame, text="Renombrar",
                   command=lambda: self._change_community_string(e_comm.get())).grid(row=0, column=2)

        # 2. sysName
        sysname_item = next((i for i in self.data if i["oid"] == OID_SYSNAME), None)
        ttk.Label(self.dynamic_config_frame, text="Device Name:").grid(row=1, column=0, sticky="w", pady=5)
        
        if sysname_item:
            e_name = ttk.Entry(self.dynamic_config_frame)
            e_name.insert(0, sysname_item['value'])
            e_name.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
            ttk.Button(self.dynamic_config_frame, text="Actualizar",
                       command=lambda: self._update_realtime(sysname_item, e_name.get())).grid(row=1, column=2, pady=5)
        else:
            ttk.Button(self.dynamic_config_frame, text="➕ Crear OID de Nombre",
                       command=self._add_sysname_oid).grid(row=1, column=1, sticky="ew", pady=5)

        # C. Rellenar Tabla
        for item in self.data:
            t = SNMP_TYPES.get(item['tag'], item['tag'])
            self.tree.insert("", "end", values=(item['oid'], item.get('name', ''), t, item['value'], item.get('ui_type', '')))

    # =======================================================
    # LOGICA DE DATOS
    # =======================================================
    def load_file(self, path):
        self.current_file_path = path
        folder = os.path.dirname(path)
        filename = os.path.basename(path)
        self.meta_file_path = os.path.join(folder, f"{filename}.meta.json")
        self.data = []

        if not os.path.exists(path): return

        meta_dict = {}
        if os.path.exists(self.meta_file_path):
            try:
                with open(self.meta_file_path, "r", encoding="utf-8") as f: meta_dict = json.load(f)
            except: pass

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 3:
                            oid, tag, val = parts[0], parts[1], parts[2]
                            meta = meta_dict.get(oid, {})
                            self.data.append({
                                "oid": oid, "tag": tag, "value": val,
                                "name": meta.get("name", ""),
                                "ui_type": meta.get("ui_type", "Text Entry")
                            })
            
            self._render_dashboard()
            self._refresh_editor_ui()
            self.tabs.select(0)
        except Exception as e:
            messagebox.showerror("Error", f"Error leyendo: {e}")

    def _update_realtime(self, item_dict, new_value):
        item_dict['value'] = str(new_value)
        self._save_to_disk()
        if item_dict['oid'] == OID_SYSNAME:
            self._render_dashboard()
            self._refresh_editor_ui()

    def _change_community_string(self, new_community):
        new_community = new_community.strip()
        if not new_community: return
        folder = os.path.dirname(self.current_file_path)
        new_filename = f"{new_community}.snmprec"
        new_path = os.path.join(folder, new_filename)
        new_meta_path = os.path.join(folder, f"{new_filename}.meta.json")

        if os.path.exists(new_path) and new_path != self.current_file_path:
            messagebox.showerror("Error", "Ya existe ese nombre de archivo.")
            return

        try:
            os.rename(self.current_file_path, new_path)
            if os.path.exists(self.meta_file_path):
                os.rename(self.meta_file_path, new_meta_path)
            
            self.current_file_path = new_path
            self.meta_file_path = new_meta_path
            
            if self.on_file_renamed_callback:
                self.on_file_renamed_callback(new_path)
            
            self._render_dashboard()
            self._refresh_editor_ui()
            messagebox.showinfo("Éxito", "Comunidad cambiada.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _add_sysname_oid(self):
        name = simpledialog.askstring("Nombre", "Nombre del Dispositivo:")
        if name:
            self.data.insert(0, {"oid": OID_SYSNAME, "tag": "4", "value": name, "name": "System Name", "ui_type": "Text Entry"})
            self._save_to_disk()
            self._save_metadata()
            self._refresh_editor_ui()
            self._render_dashboard()

    def _save_to_disk(self):
        if not self.current_file_path: return
        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                for item in self.data:
                    f.write(f"{item['oid']}|{item['tag']}|{item['value']}\n")
        except: pass

    def _save_metadata(self):
        if not self.meta_file_path: return
        meta = {i['oid']: {"name": i.get("name", ""), "ui_type": i.get("ui_type", "")} for i in self.data}
        try:
            with open(self.meta_file_path, "w", encoding="utf-8") as f: json.dump(meta, f, indent=4)
        except: pass

    def _save_as_template(self):
        if not self.data: return
        tmpl_name = simpledialog.askstring("Nueva Plantilla", "Nombre para la plantilla:")
        if not tmpl_name: return

        content_lines = []
        for item in self.data:
            content_lines.append(f"{item['oid']}|{item['tag']}|{item['value']}")
        content_str = "\n".join(content_lines)

        meta_dict = {}
        for item in self.data:
            if item.get("name") or item.get("ui_type") != "Text Entry":
                meta_dict[item['oid']] = {"name": item.get("name", ""), "ui_type": item.get("ui_type", "Text Entry")}

        new_template = {"content": content_str, "meta": meta_dict}
        json_path = "templates.json"
        current = {}
        
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f: current = json.load(f)
            except: pass
        
        current[tmpl_name] = new_template
        try:
            with open(json_path, "w", encoding="utf-8") as f: json.dump(current, f, indent=4)
            messagebox.showinfo("Éxito", f"Plantilla '{tmpl_name}' guardada.")
            if self.on_template_saved_callback: self.on_template_saved_callback()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")

    # =======================================================
    # EVENTOS Y AUXILIARES
    # =======================================================
    def _on_tab_changed(self, event):
        if not self.data and not self.current_file_path: return
        idx = self.tabs.index(self.tabs.select())
        if idx == 0: self._render_dashboard()
        else: self._refresh_editor_ui()

    def _add_oid_dialog(self):
        if not self.current_file_path: return
        oid = simpledialog.askstring("Nuevo", "OID:")
        if oid:
            if any(x['oid'] == oid for x in self.data):
                messagebox.showerror("Error", "OID duplicado")
                return
            self.data.append({"oid": oid, "tag": "2", "value": "0", "name": "", "ui_type": "Text Entry"})
            self._save_to_disk()
            self._save_metadata()
            self._refresh_editor_ui()

    def _on_double_click_row(self, event):
        item_id = self.tree.identify_row(event.y)
        if not item_id: return
        idx = self.tree.index(item_id)
        EditDialog(self, self.data[idx], self._on_edit_complete)

    def _on_edit_complete(self):
        self._save_to_disk()
        self._save_metadata()
        self._refresh_editor_ui()


# =======================================================
# POPUP DE EDICIÓN
# =======================================================
class EditDialog(tk.Toplevel):
    def __init__(self, parent, item_data, callback):
        super().__init__(parent)
        self.title("Editar OID")
        self.geometry("380x500")
        self.item = item_data
        self.callback = callback
        self._build()

    def _build(self):
        pad = {'padx': 15, 'pady': 5}
        
        ttk.Label(self, text="-- METADATA (INTERFAZ) --", font="bold").pack(pady=(10, 5))
        
        ttk.Label(self, text="Nombre Amigable (Sensor):").pack(**pad)
        e_name = ttk.Entry(self, width=35)
        e_name.insert(0, self.item.get('name', ''))
        e_name.pack(**pad)

        ttk.Label(self, text="Control Visual:").pack(**pad)
        cb_ui = ttk.Combobox(self, values=["Text Entry", "Slider", "Toggle"], state="readonly")
        cb_ui.set(self.item.get('ui_type', 'Text Entry'))
        cb_ui.pack(**pad)

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=15)
        ttk.Label(self, text="-- DATOS SNMP (TÉCNICO) --", font="bold").pack(pady=5)

        ttk.Label(self, text="OID:").pack(**pad)
        e_oid = ttk.Entry(self, width=35)
        e_oid.insert(0, self.item['oid'])
        e_oid.pack(**pad)

        ttk.Label(self, text="Valor:").pack(**pad)
        e_val = ttk.Entry(self, width=35)
        e_val.insert(0, self.item['value'])
        e_val.pack(**pad)

        ttk.Label(self, text="Tipo:").pack(**pad)
        cb_tag = ttk.Combobox(self, values=list(TAG_BY_NAME.keys()), state="readonly")
        cb_tag.set(SNMP_TYPES.get(self.item['tag'], "Integer"))
        cb_tag.pack(**pad)

        def save():
            self.item['name'] = e_name.get()
            self.item['ui_type'] = cb_ui.get()
            self.item['oid'] = e_oid.get()
            self.item['value'] = e_val.get()
            self.item['tag'] = TAG_BY_NAME.get(cb_tag.get(), "4")
            self.callback()
            self.destroy()

        ttk.Button(self, text="Guardar Cambios", command=save).pack(pady=20)