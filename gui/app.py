import tkinter as tk
from tkinter import ttk
import os
import queue  # Necesario para evitar que la interfaz se congele

# Importar nuestros componentes modulares
from gui.topbar import TopBar
from gui.sidebar import DeviceSidebar
from gui.editor import DeviceEditor
from gui.snmpsim_runner import SNMPSimRunner


class SNMPSimApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("SNMPSim Manager Pro")
        self.geometry("1200x700")

        # 1. Configurar cola de mensajes (Thread-Safe Log)
        self.log_queue = queue.Queue()

        # 2. Inicializar el Runner
        # Pasamos self.queue_log como la función que recibirá los textos
        self.sim_runner = SNMPSimRunner(on_output=self.queue_log)

        # 3. Construir Interfaz
        self._build_layout()
        
        # 4. Iniciar el monitor de logs (revisa la cola cada 100ms)
        self.check_log_queue()

        # 5. Cargar directorio inicial si existe
        initial_dir = self.topbar.get_data_dir()
        if initial_dir and os.path.exists(initial_dir):
            self.sidebar.set_directory(initial_dir)

    def _build_layout(self):
        # A. TopBar
        self.topbar = TopBar(
            self,
            on_start=self.start_simulation,
            on_stop=self.stop_simulation,
            on_dir_change=self.on_directory_changed
        )
        self.topbar.pack(fill="x", pady=2)

        separator = ttk.Separator(self, orient='horizontal')
        separator.pack(side="top", fill="x", padx=10, pady=5)

        # B. Paneles Divisores
        self.paned = ttk.PanedWindow(self, orient="horizontal")
        self.paned.pack(fill="both", expand=True)

        # C. Sidebar
        self.sidebar = DeviceSidebar(self.paned, on_selection_change=self.on_file_selected)
        self.paned.add(self.sidebar, weight=1)

        # D. Editor
        self.editor = DeviceEditor(self.paned,
                                   on_file_renamed=self.on_file_renamed,
                                   on_template_saved=self.on_template_saved)
        self.paned.add(self.editor, weight=4)

        # E. Consola de Salida
        self.console_frame = ttk.Frame(self, height=150)
        self.console_frame.pack(fill="x", side="bottom")
        
        # Widget Text para logs (fondo oscuro, letra verde)
        self.console_text = tk.Text(self.console_frame, height=8, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9))
        self.console_text.pack(side="left", fill="both", expand=True)
        
        # Scrollbar para la consola
        scroll = ttk.Scrollbar(self.console_frame, command=self.console_text.yview)
        scroll.pack(side="right", fill="y")
        self.console_text.config(yscrollcommand=scroll.set)

    # ---------------- LOGGING SEGURO (THREAD-SAFE) ---------------- #

    def queue_log(self, message):
        """Este método lo llama el hilo secundario (Runner). Solo mete datos en la cola."""
        self.log_queue.put(message)

    def check_log_queue(self):
        """Este método lo ejecuta la GUI principal. Saca datos de la cola y pinta."""
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self.console_text.insert(tk.END, f"{msg}\n")
                self.console_text.see(tk.END)  # Auto-scroll al final
            except queue.Empty:
                pass
        
        # Se vuelve a llamar a sí mismo en 100ms
        self.after(100, self.check_log_queue)

    # ---------------- ACCIONES DE LA APP ---------------- #

    def start_simulation(self):
        endpoint = self.topbar.get_endpoint()
        data_dir = self.topbar.get_data_dir()
        
        self.console_text.delete(1.0, tk.END)  # Limpiar consola
        self.console_text.insert(tk.END, f"--- PREPARANDO SIMULACIÓN ---\n")
        
        self.topbar.set_running(True)
        self.sim_runner.start(endpoint, data_dir)

    def stop_simulation(self):
        self.topbar.set_running(False)
        self.sim_runner.stop()

    def on_directory_changed(self, new_path):
        if hasattr(self, 'sidebar') and self.sidebar:
            self.sidebar.set_directory(new_path)

    def on_file_selected(self, file_path):
        self.editor.load_file(file_path)

    def on_file_renamed(self, new_path):
        """Si cambian la comunidad, actualizamos el sidebar."""
        self.sidebar.refresh()
        new_filename = os.path.basename(new_path)
        if self.sidebar.tree.exists(new_filename):
            self.sidebar.tree.selection_set(new_filename)
            self.sidebar.tree.see(new_filename)

    def on_template_saved(self):
        """Si guardan plantilla, recargamos menú del sidebar."""
        if hasattr(self.sidebar, 'reload_templates'):
            self.sidebar.reload_templates()


if __name__ == "__main__":
    app = SNMPSimApp()
    app.mainloop()
