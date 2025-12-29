import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import os


class TopBar(ttk.Frame):

    def __init__(self, parent, on_start, on_stop):
        super().__init__(parent)
        self.on_start = on_start
        self.on_stop = on_stop

        self._build_ui()

    def _build_ui(self):
        # Botones
        ttk.Button(self, text="▶", width=3, command=self.on_start).pack(
            side="left", padx=(5, 2)
        )
        ttk.Button(self, text="⏹", width=3, command=self.on_stop).pack(
            side="left", padx=(0, 10)
        )

        # Estado
        self.status_var = tk.StringVar(value="STOPPED")
        self.status_label = ttk.Label(
            self,
            textvariable=self.status_var,
            foreground="red",
            font=("Segoe UI", 10, "bold")
        )
        self.status_label.pack(side="left", padx=(0, 15))

        ttk.Separator(self, orient="vertical").pack(
            side="left", fill="y", padx=10
        )
        ttk.Label(self, text="Data dir").pack(side="left")


        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_data_dir = os.path.abspath(
            os.path.join(base_dir, "..", "data")
        )

        self.data_dir_var = tk.StringVar(value=default_data_dir)
        self.data_dir_entry = ttk.Entry(
            self, textvariable=self.data_dir_var, width=30
        )
        self.data_dir_entry.pack(side="left", padx=5)

        ttk.Button(
            self, text="📁", width=3, command=self._select_dir
        ).pack(side="left")

        # Endpoint
        ttk.Label(self, text="IP").pack(side="left")
        self.ip_entry = ttk.Entry(self, width=15)
        self.ip_entry.insert(0, "127.0.0.1")
        self.ip_entry.pack(side="left", padx=5)

        ttk.Label(self, text="Port").pack(side="left")
        self.port_entry = ttk.Entry(self, width=6)
        self.port_entry.insert(0, "1024")
        self.port_entry.pack(side="left", padx=5)

    # ---------- API pública ----------

    def set_running(self, running: bool):
        if running:
            self.status_var.set("RUNNING")
            self.status_label.config(foreground="green")
            self.data_dir_entry.config(state="disabled")
            self.ip_entry.config(state="disabled")
            self.port_entry.config(state="disabled")    
        else:
            self.status_var.set("STOPPED")
            self.status_label.config(foreground="red")
            self.data_dir_entry.config(state="normal")
            self.ip_entry.config(state="normal")
            self.port_entry.config(state="normal")  

    def get_endpoint(self) -> str:
        ip = self.ip_entry.get().strip()
        port = self.port_entry.get().strip()
        return f"{ip}:{port}"

    def _select_dir(self):
            path = filedialog.askdirectory()
            if path:
                self.data_dir_var.set(path)

    def get_data_dir(self) -> str:
        return self.data_dir_var.get()  
