# gui/topbar.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
from gui import utils

class TopBar(ttk.Frame):

    def __init__(self, parent, on_start, on_stop, on_dir_change=None):
        super().__init__(parent)
        self.on_start = on_start
        self.on_stop = on_stop
        self.on_dir_change = on_dir_change
        
        self._build_ui()

    def _build_ui(self):
        # Configurar validación de entrada numérica para el puerto
        vcmd = (self.register(self._only_numbers), '%P')

        # --- 1. Controles de Ejecución ---
        exec_frame = ttk.Frame(self)
        exec_frame.pack(side="left", padx=5)

        self.btn_start = ttk.Button(exec_frame, text="▶", width=3, command=self._handle_start)
        self.btn_start.pack(side="left", padx=2)
        
        self.btn_stop = ttk.Button(exec_frame, text="⏹", width=3, command=self.on_stop, state="disabled")
        self.btn_stop.pack(side="left", padx=2)

        # LED de estado
        self.led = tk.Canvas(self, width=15, height=15, highlightthickness=0)
        self.led_circle = self.led.create_oval(2, 2, 13, 13, fill="red")
        self.led.pack(side="left", padx=(5, 0))

        self.status_var = tk.StringVar(value="STOPPED")
        ttk.Label(self, textvariable=self.status_var, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5, 15))

        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=10)
        
        # --- 2. Directorio de Datos ---
        ttk.Label(self, text="Dir:").pack(side="left")
        
        # Inicializar con directorio actual por defecto para evitar vacío
        default_dir = os.path.abspath(os.getcwd())
        self.data_dir_var = tk.StringVar(value=default_dir)
        self.data_dir_var.trace_add("write", self._notify_dir_change)

        self.data_dir_entry = ttk.Entry(self, textvariable=self.data_dir_var, width=35)
        self.data_dir_entry.pack(side="left", padx=5)
        self.data_dir_entry.config(state="readonly") 

        self.btn_dir =  ttk.Button(self, text="...", width=3, command=self._select_dir)
        self.btn_dir.pack(side="left", padx=2)
        
        ttk.Button(self, text="↗", width=3, command=self._open_in_os).pack(side="left", padx=(0, 5))

        # --- 3. Red (IP/Puerto) ---
        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=10)
        
        ttk.Label(self, text="Host:").pack(side="left")
        self.ip_entry = ttk.Entry(self, width=12)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(side="left", padx=2)

        ttk.Label(self, text=":").pack(side="left")
        self.port_entry = ttk.Entry(self, width=6, validate='key', validatecommand=vcmd)
        self.port_entry.insert(0, "1024")
        self.port_entry.pack(side="left", padx=2)

        # --- 4. Perfiles ---
        ttk.Separator(self, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Label(self, text="Perfil:").pack(side="left")
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(self, textvariable=self.profile_var, width=15)
        self.profile_combo.pack(side="left", padx=5)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_select)

        self.btn_save = ttk.Button(self, text="💾", width=3, command=self._save_current_profile)
        self.btn_save.pack(side="left", padx=2)
        self.btn_delete = ttk.Button(self, text="🗑", width=3, command=self._delete_current_profile)
        self.btn_delete.pack(side="left", padx=2)
        
        # Cargar perfiles al iniciar
        self._refresh_profile_list()
        if self.profile_combo['values']:
            self.profile_combo.current(0)
            self._on_profile_select(None) 

    # ---------------- LÓGICA DE EJECUCIÓN ---------------- #

    def _handle_start(self):
        if self.validate_inputs():
            self.on_start()

    def set_running(self, running: bool):
        if running:
            self.status_var.set("RUNNING")
            self.led.itemconfig(self.led_circle, fill="#00FF00")  # Verde
            self.btn_start.config(state="disabled")
            self.btn_stop.config(state="normal")
            state = "disabled"
        else:
            self.status_var.set("STOPPED")
            self.led.itemconfig(self.led_circle, fill="red")
            self.btn_start.config(state="normal")
            self.btn_stop.config(state="disabled")
            state = "normal" # O 'readonly' para el directorio si prefieres
            
        self.ip_entry.config(state=state)
        self.port_entry.config(state=state)
        self.profile_combo.config(state=state)
        self.btn_delete.config(state=state)
        self.btn_save.config(state=state)
        self.btn_dir.config(state=state)
        

    def validate_inputs(self) -> bool:
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        data_dir = self.data_dir_var.get().strip()

        if not utils.is_valid_ip(ip):
            messagebox.showerror("Error de Red", f"La IP '{ip}' no es válida.")
            return False

        if not utils.is_valid_port(port):
            messagebox.showerror("Error de Red", "El puerto debe ser un número entre 1 y 65535.")
            return False
            
        if not os.path.isdir(data_dir):
            messagebox.showerror("Error de Archivo", "El directorio de datos seleccionado no existe.")
            return False

        return True

    # ---------------- LÓGICA DE ARCHIVOS ---------------- #

    def _select_dir(self):
        path = filedialog.askdirectory()
        if path:
            self.data_dir_var.set(os.path.abspath(path))

    def _open_in_os(self):
        path = self.data_dir_var.get()
        if not utils.open_file_explorer(path):
            messagebox.showwarning("Error", "No se pudo abrir la carpeta o no existe.")

    def _notify_dir_change(self, *args):
        if self.on_dir_change:
            self.on_dir_change(self.data_dir_var.get())

    # ---------------- LÓGICA DE PERFILES ---------------- #
    def _delete_current_profile(self):
        profile_name = self.profile_var.get().strip()
        if not profile_name:
            return

        # 1. Cargar perfiles
        try:
            with open("profiles.json", "r") as f:
                profiles = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return # No hay nada que borrar

        # 2. Verificar existencia
        if profile_name not in profiles:
            messagebox.showwarning("Error", f"El perfil '{profile_name}' no existe o no está guardado.")
            return

        # 3. Confirmación
        confirm = messagebox.askyesno("Confirmar eliminación", 
                                      f"¿Estás seguro de que deseas eliminar el perfil '{profile_name}'?")
        if not confirm:
            return

        # 4. Eliminar y Guardar
        del profiles[profile_name]
        
        try:
            with open("profiles.json", "w") as f:
                json.dump(profiles, f, indent=4)
            
            messagebox.showinfo("Éxito", "Perfil eliminado correctamente.")
            
            # 5. Actualizar UI
            self.profile_var.set("") # Limpiar selección
            self._refresh_profile_list()
            
            # Si quedan perfiles, seleccionar el primero
            if self.profile_combo['values']:
                self.profile_combo.current(0)
                self._on_profile_select(None)
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar los cambios: {e}")


    def _save_current_profile(self):
        profile_name = self.profile_var.get().strip()
        if not profile_name:
            messagebox.showwarning("Perfil", "Escribe un nombre para el perfil antes de guardar.")
            return

        new_data = {
            "data_dir": self.get_data_dir(),
            "ip": self.ip_entry.get(),
            "port": self.port_entry.get()
        }

        try:
            with open("profiles.json", "r") as f:
                profiles = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            profiles = {}

        # Preguntar si se sobrescribe
        if profile_name in profiles:
            if not messagebox.askyesno("Sobrescribir", f"El perfil '{profile_name}' ya existe. ¿Sobrescribir?"):
                return

        profiles[profile_name] = new_data

        try:
            with open("profiles.json", "w") as f:
                json.dump(profiles, f, indent=4)
            messagebox.showinfo("Perfil", f"Perfil '{profile_name}' guardado correctamente.")
            self._refresh_profile_list()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el perfil: {e}")

    def _refresh_profile_list(self):
        try:
            with open("profiles.json", "r") as f:
                profiles = json.load(f)
                self.profile_combo['values'] = list(profiles.keys())
        except (FileNotFoundError, json.JSONDecodeError):
            self.profile_combo['values'] = []

    def _on_profile_select(self, event):
        name = self.profile_var.get()
        try:
            with open("profiles.json", "r") as f:
                profiles = json.load(f)
                data = profiles.get(name)
                if data:
                    # Usamos .get() con defaults para evitar crashes si el JSON está incompleto
                    self.data_dir_var.set(data.get("data_dir", os.getcwd()))
                    
                    self.ip_entry.delete(0, tk.END)
                    self.ip_entry.insert(0, data.get("ip", "127.0.0.1"))
                    
                    self.port_entry.delete(0, tk.END)
                    self.port_entry.insert(0, data.get("port", "1024"))
        except Exception:
            # Silencioso o log error
            pass

    # ---------------- GETTERS & HELPERS ---------------- #

    def _only_numbers(self, char):
        return char.isdigit() or char == ""

    def get_endpoint(self) -> str:
        # Validación final silenciosa o fallback
        port = self.port_entry.get().strip()
        ip = self.ip_entry.get().strip()
        if not port.isdigit():
             port = "1024"
        return f"{ip}:{port}"

    def get_data_dir(self) -> str:
        return self.data_dir_var.get()