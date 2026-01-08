import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, Menu
import os
import shutil
import json


class DeviceSidebar(ttk.Frame):

    def __init__(self, parent, on_selection_change):
        super().__init__(parent)
        self.on_selection_change = on_selection_change
        self.current_dir = ""
        self.all_files = []
        
        self.templates = self._load_templates()

        self._build_ui()

    def _build_ui(self):
        # Header
        header = ttk.Frame(self)
        header.pack(fill="x", padx=5, pady=5)
        ttk.Label(header, text="Dispositivos", font=("Segoe UI", 10, "bold")).pack(side="left")
        
        # Barra de búsqueda
        search_frame = ttk.Frame(header)
        search_frame.pack(fill="x", pady=(5, 0))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)  # Evento al escribir
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        # Botones inferiores
        btn_frame = ttk.Frame(self)
        btn_frame.pack(side="bottom", fill="x", pady=5, padx=5)
        
        ttk.Button(btn_frame, text="🔄", width=3, command=self.refresh).pack(side="left")
        
        # Botón con menú desplegable para "+ Nuevo"
        self.btn_new = ttk.Menubutton(btn_frame, text="➕ Nuevo", direction='above')
        self.menu_new = Menu(self.btn_new, tearoff=0)
        
        # Llenar el menú de plantillas dinámicamente
        for name in self.templates.keys():
            self.menu_new.add_command(label=name, command=lambda n=name: self._create_from_template(n))
            
        self.btn_new.config(menu=self.menu_new)
        self.btn_new.pack(side="right", fill="x", expand=True, padx=(5, 0))
        
        # Contenedor de la Lista y el scroll
        list_frame = ttk.Frame(self)
        list_frame.pack(side="top", fill="both", expand=True, padx=5, pady=2)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")
        
        # Árbol de archivos
        self.tree = ttk.Treeview(list_frame, selectmode="browse", show="tree")
        self.tree.pack(side="left", fill="both", expand=True)
       
        # Conectar Scrollbar con Treeview
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=self.tree.yview)

        # Eventos
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-3>", self._show_context_menu)  # Clic derecho

        # Menú contextual (Clic derecho)
        self.context_menu = Menu(self, tearoff=0)
        self.context_menu.add_command(label="Duplicar", command=self._duplicate_device)
        self.context_menu.add_command(label="Renombrar", command=self._rename_device)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Eliminar", command=self._delete_device)

    # ---------------- LÓGICA DE FILTRADO (NUEVO) ---------------- #

    def _on_search_change(self, *args):
        query = self.search_var.get().lower()
        self._populate_tree(query)

    def _populate_tree(self, filter_text=""):
        """Llena el Treeview basándose en self.all_files y el filtro."""
        # Limpiar vista actual
        self.tree.delete(*self.tree.get_children())
        
        for filename in self.all_files:
            # Lógica de filtro: si el texto está en el nombre
            display_name = os.path.splitext(filename)[0]
            
            if filter_text in display_name.lower():
                # Añadimos un icono unicode para que se vea bonito
                text_with_icon = f"📄 {display_name}"
                self.tree.insert("", "end", iid=filename, text=text_with_icon)
    
    # ---------------- GESTIÓN DE ARCHIVOS ---------------- #

    def set_directory(self, path):
        self.current_dir = path
        self.refresh()

    def refresh(self):
        self.all_files = []
        
        # Limpiar lista actual
        self.tree.delete(*self.tree.get_children())
        
        self.reload_templates_from_disk()
        
        if self.current_dir and os.path.exists(self.current_dir):
            try:
                # Cachear todos los archivos .snmprec
                files = [f for f in os.listdir(self.current_dir) if f.endswith(".snmprec")]
                self.all_files = sorted(files)
            except Exception as e:
                print(f"Error listando: {e}")
        
        # Repoblar usando el filtro actual (si hay texto escrito, se mantiene el filtro)
        self._populate_tree(self.search_var.get().lower())

    def _on_select(self, event):
        selected = self.tree.selection()
        if selected:
            filename = selected[0]  # El ID es el nombre completo con extensión
            full_path = os.path.join(self.current_dir, filename)
            if self.on_selection_change:
                self.on_selection_change(full_path)

    # ---------------- ACCIONES (Templates, Duplicar, Borrar) ---------------- #

    def _load_templates(self):
        default = {"Dispositivo Vacío": {"content": "", "meta": {}}}
        path = "templates.json"
        
        if not os.path.exists(path): return default
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Validación simple
                if "Dispositivo Vacío" not in data:
                    data = {**default, **data}
                return data
        except Exception as e:
            print(f"Error template: {e}")
            return default

    def _show_context_menu(self, event):
        """Muestra menú al hacer clic derecho sobre un ítem."""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _create_from_template(self, template_name):
        if not self.current_dir:
            messagebox.showwarning("Aviso", "Selecciona un directorio de datos.")
            return

        new_name = simpledialog.askstring("Nuevo", "Nombre del dispositivo:")
        if not new_name: return

        if not new_name.endswith(".snmprec"): new_name += ".snmprec"

        # Rutas
        path_snmprec = os.path.join(self.current_dir, new_name)
        path_meta = os.path.join(self.current_dir, f"{new_name}.meta.json")
        
        if os.path.exists(path_snmprec):
            messagebox.showerror("Error", "Ya existe ese archivo.")
            return

        # Obtener datos del nuevo formato
        template_data = self.templates.get(template_name, {"content": "", "meta": {}})
        
        # Soportar formato antiguo (string) por si acaso el json es viejo
        if isinstance(template_data, str):
            content = template_data
            meta = {}
        else:
            content = template_data.get("content", "")
            meta = template_data.get("meta", {})

        try:
            # 1. Crear .snmprec
            with open(path_snmprec, "w", encoding="utf-8") as f:
                f.write(content)
            
            # 2. Crear .meta.json
            with open(path_meta, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=4)

            self.refresh()
            # Auto-seleccionar
            if self.tree.exists(new_name):
                self.tree.selection_set(new_name)
                self.tree.see(new_name)
                self._on_select(None)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo crear: {e}")

    # Método auxiliar para recargar plantillas externamente (usado si el Editor guarda una nueva)
    def reload_templates(self):
        self.templates = self._load_templates()
        # Reconstruir menú
        self.menu_new.delete(0, "end")
        for name in self.templates.keys():
            self.menu_new.add_command(label=name, command=lambda n=name: self._create_from_template(n))
            
    def _duplicate_device(self):
        selected = self.tree.selection()
        if not selected: 
            return
        
        filename = selected[0]  # Ej: router.snmprec
        src_path = os.path.join(self.current_dir, filename)
        
        base_name = os.path.splitext(filename)[0]
        new_name = simpledialog.askstring("Duplicar", f"Nombre para la copia de {base_name}:", initialvalue=f"{base_name}_copy")
        
        if not new_name:
            return

        if not new_name.endswith(".snmprec"):
            new_name += ".snmprec"

        dest_path = os.path.join(self.current_dir, new_name)

        if os.path.exists(dest_path):
            messagebox.showerror("Error", "Ya existe un archivo con ese nombre.")
            return

        try:
            shutil.copy2(src_path, dest_path)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Error", f"Fallo al duplicar: {e}")

    def _delete_device(self):
        selected = self.tree.selection()
        if not selected: 
            return
            
        filename = selected[0]
        display_name = self.tree.item(filename)['text']  # El nombre sin extensión
        
        if messagebox.askyesno("Eliminar", f"¿Estás seguro de eliminar '{display_name}'?"):
            path = os.path.join(self.current_dir, filename)
            try:
                os.remove(path)
                self.refresh()
                # Limpiar el editor avisando selección vacía o nula
                # (Opcional: podrías implementar un método clear en editor)
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo eliminar: {e}")

    def reload_templates_from_disk(self): 
        self.templates = self._load_templates()

        # Reconstruir el menú
        self.menu_new.delete(0, "end")
        for name in self.templates.keys():
            self.menu_new.add_command(label=name, command=lambda n=name: self._create_from_template(n))
        
        print("Plantillas recargadas.")
        
    def _rename_device(self):
        selected = self.tree.selection()
        if not selected:
            return

        filename = selected[0]  # El ID es el nombre completo (ej: router.snmprec)
        current_name_no_ext = os.path.splitext(filename)[0]  # Para mostrar al usuario
        
        # Pedir nuevo nombre
        new_name = simpledialog.askstring(
            "Renombrar",
            f"Nuevo nombre para '{current_name_no_ext}':",
            initialvalue=current_name_no_ext
        )

        if not new_name:
            return  # Usuario canceló

        # Limpiar espacios y asegurar extensión
        new_name = new_name.strip()
        if not new_name.endswith(".snmprec"):
            new_name += ".snmprec"

        # Verificar si el nombre cambió
        if new_name == filename:
            return

        # Rutas completas
        src_path = os.path.join(self.current_dir, filename)
        dst_path = os.path.join(self.current_dir, new_name)

        # Validar que no exista ya
        if os.path.exists(dst_path):
            messagebox.showerror("Error", f"Ya existe un archivo llamado '{new_name}'.")
            return

        try:
            os.rename(src_path, dst_path)
            
            # Actualizar la lista
            self.refresh()
            
            # Seleccionar el archivo renombrado automáticamente
            # Esto es importante para que el Editor sepa que el archivo cambió
            if self.tree.exists(new_name):
                self.tree.selection_set(new_name)
                self.tree.see(new_name)
                # Forzamos el evento de selección para actualizar el editor derecho
                self._on_select(None) 
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo renombrar el archivo: {e}")
