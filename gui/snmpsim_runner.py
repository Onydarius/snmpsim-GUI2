import subprocess
import sys
import os
import threading
from pathlib import Path




class SNMPSimRunner: 

    def __init__(self, on_output=None):
        self.process = None
        self.on_output = on_output
        self.base_dir = Path(__file__).resolve().parent.parent
        self.runtime_dir = self.base_dir / "runtime"


    def start(self, endpoint: str, data_dir: str):
        if self.process:
            return


        print("data_dir:", data_dir)
        cmd = [
            sys.executable,
            "-m", "snmpsim.commands.responder",
            "--data-dir", data_dir,
            "--agent-udpv4-endpoint", endpoint
        ]   

        self.process = subprocess.Popen(
            cmd,
            cwd=self.runtime_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        threading.Thread(
            target=self._read_stream,
            args=(self.process.stdout,),
            daemon=True
        ).start()

        threading.Thread(
            target=self._read_stream,
            args=(self.process.stderr,),
            daemon=True
        ).start()

    def _read_stream(self, stream):
        for line in iter(stream.readline, ""):
            if self.on_output:
                self.on_output(line.rstrip())

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process = None
