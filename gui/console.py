import tkinter as tk
from tkinter import ttk

class Console(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)

        self.text = tk.Text(
            self,
            height=10,
            bg="black",
            fg="lime",
            insertbackground="white"
        )
        self.text.pack(fill="both", expand=True)

        self.text.config(state="disabled")

    def write(self, line: str):
        self.text.config(state="normal")
        self.text.insert("end", line + "\n")
        self.text.see("end")
        self.text.config(state="disabled")

    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")