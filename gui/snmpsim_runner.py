import subprocess
import sys
import os
import threading
import time
from pathlib import Path


class SNMPSimRunner: 

    def __init__(self, on_output=None):
        self.process = None
        self.on_output = on_output
        # Ajustamos base_dir para que apunte a la raíz del proyecto
        # Asumiendo que este archivo está en /gui/, subimos un nivel (.parent)
        self.base_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
        self.runtime_dir = self.base_dir / "runtime"

    def start(self, endpoint: str, data_dir: str):
        if self.process:
            return

        # 1. Asegurar que el directorio runtime exista
        if not self.runtime_dir.exists():
            try:
                self.runtime_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                if self.on_output: self.on_output(f"Error creando directorio runtime: {e}")
                return

        if self.on_output:
            self.on_output(f"--- Iniciando simulador ---")
            self.on_output(f"Data: {data_dir}")
            self.on_output(f"Endpoint: {endpoint}")

        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            empty_dir = os.path.join(os.environ['TEMP'], "snmpsim_empty")
            os.makedirs(empty_dir, exist_ok=True)
            executable = sys.executable
            cmd = [
                executable,
                "-m", "snmpsim.commands.responder",  # Invocamos el módulo interno
                "--data-dir", data_dir,
                "--agent-udpv4-endpoint", endpoint
            ]
        else:
            # En modo desarrollo, seguimos usando tu launcher.py
            launcher_path = self.base_dir / "gui" / "launcher.py"
            cmd = [
                "python",
                str(launcher_path),
                "--data-dir", data_dir,
                "--variation-modules-dir", empty_dir,
                "--agent-udpv4-endpoint", endpoint
            ]

        try:
            # Usamos cwd=str(self.runtime_dir) para que cree archivos temporales ahí si lo necesita
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.runtime_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
                bufsize=1  # Line buffered
            )

            # Hilos para leer la salida sin bloquear la GUI
            threading.Thread(target=self._read_stream, args=(self.process.stdout,), daemon=True).start()
            threading.Thread(target=self._read_stream, args=(self.process.stderr,), daemon=True).start()
            
        except Exception as e:
            if self.on_output:
                self.on_output(f"ERROR CRÍTICO AL INICIAR: {e}")

    def _read_stream(self, stream):
        """Lee línea por línea del subproceso."""
        try:
            for line in iter(stream.readline, ""):
                if self.on_output:
                    self.on_output(line.rstrip())
        except ValueError:
            pass  # El archivo se cerró

    def stop(self):
        if self.process:
            if self.on_output:
                self.on_output("--- Deteniendo simulador... ---")
            
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()  # Forzar cierre si se cuelga
            
            self.process = None
            if self.on_output:
                self.on_output("--- Simulador detenido ---")
