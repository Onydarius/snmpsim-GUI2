import tkinter as tk
from tkinter import ttk, messagebox
from pysnmp.proto import rfc1902

from .models import SimulatedDevice
from .snmpsim_runner import SNMPSimRunner
from gui.topbar import TopBar
from gui.console import Console

class SNMPSimGUI(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("SNMPSim Device Manager")
        self.geometry("1000x600")

        self.devices = {}
        self.current_device = None
        self.topbar = None

        self._build_ui()

        self.sim_runner = SNMPSimRunner(
            on_output=self.console.write
        )

    # ---------------- UI ---------------- #

    def _build_ui(self):
        self.topbar = TopBar(self, self.start_sim, self.stop_sim)
        self.topbar.pack(fill="x", pady=2)


        main = ttk.Frame(self)
        main.pack(fill="both", expand=True)

        self._build_device_list(main)
        self._build_device_editor(main)

        self.console = Console(self)
        self.console.pack(fill="both", expand=True)

    def _build_device_list(self, parent):
        frame = ttk.Frame(parent, width=250)
        frame.pack(side="left", fill="y")

        self.device_tree = ttk.Treeview(frame)
        self.device_tree.pack(fill="both", expand=True)
        self.device_tree.bind("<<TreeviewSelect>>", self.on_select_device)

        ttk.Button(frame, text="+ Add Device", command=self.add_device).pack(fill="x")
        ttk.Button(frame, text="✖ Remove", command=self.remove_device).pack(fill="x")

    def _build_device_editor(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(side="right", fill="both", expand=True)

        tabs = ttk.Notebook(frame)
        tabs.pack(fill="both", expand=True)

        self.general_tab = ttk.Frame(tabs)
        self.oid_tab = ttk.Frame(tabs)

        tabs.add(self.general_tab, text="General")
        tabs.add(self.oid_tab, text="OIDs")

        self._build_general_tab()
        self._build_oid_tab()

    # ---------------- General Tab ---------------- #

    def _build_general_tab(self):
        f = self.general_tab

        ttk.Label(f, text="Name").grid(row=0, column=0)
        self.name_entry = ttk.Entry(f)
        self.name_entry.grid(row=0, column=1)

        ttk.Label(f, text="Community").grid(row=1, column=0)
        self.community_entry = ttk.Entry(f)
        self.community_entry.grid(row=1, column=1)

        ttk.Label(f, text="SNMP Version").grid(row=2, column=0)
        self.version_combo = ttk.Combobox(f, values=["v1", "v2c"])
        self.version_combo.grid(row=2, column=1)

        ttk.Button(f, text="Save", command=self.save_general).grid(row=3, column=1)

    # ---------------- OID Tab ---------------- #

    def _build_oid_tab(self):
        f = self.oid_tab

        self.oid_table = ttk.Treeview(
            f, columns=("oid", "type", "value"), show="headings"
        )
        for c in ("oid", "type", "value"):
            self.oid_table.heading(c, text=c)

        self.oid_table.pack(fill="both", expand=True)

        controls = ttk.Frame(f)
        controls.pack(fill="x")

        ttk.Button(controls, text="+ Add OID", command=self.add_oid).pack(side="left")
        ttk.Button(controls, text="Apply", command=self.apply_oids).pack(side="right")

    # ---------------- Actions ---------------- #

    def start_sim(self):
        endpoint = self.topbar.get_endpoint()
        data_dir = self.topbar.get_data_dir()
        self.console.clear()
        self.sim_runner.start(endpoint, data_dir)
        self.topbar.set_running(True)   

    def stop_sim(self):
        self.sim_runner.stop()
        self.topbar.set_running(False)

    def add_device(self):
        dev = SimulatedDevice()
        self.devices[dev.id] = dev
        self.device_tree.insert("", "end", dev.id, text=dev.name)

    def remove_device(self):
        sel = self.device_tree.selection()
        if not sel:
            return
        dev = self.devices.pop(sel[0])
        self.device_tree.delete(sel[0])

    def on_select_device(self, _):
        sel = self.device_tree.selection()
        if not sel:
            return
        self.current_device = self.devices[sel[0]]
        self.load_device()

    def load_device(self):
        d = self.current_device
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, d.name)
        self.community_entry.delete(0, "end")
        self.community_entry.insert(0, d.community)
        self.version_combo.set(d.version)

        for i in self.oid_table.get_children():
            self.oid_table.delete(i)

        for oid, val in d.oids.items():
            self.oid_table.insert("", "end", values=(oid, type(val).__name__, val))

    def save_general(self):
        d = self.current_device
        d.name = self.name_entry.get()
        d.community = self.community_entry.get()
        d.version = self.version_combo.get()
        self.device_tree.item(d.id, text=d.name)

    def add_oid(self):
        self.oid_table.insert("", "end", values=("1.3.6.1.x.x", "Integer32", 0))

    def apply_oids(self):
        d = self.current_device
        d.oids.clear()

        for row in self.oid_table.get_children():
            oid, t, val = self.oid_table.item(row)["values"]
            snmp_val = rfc1902.Integer32(int(val))
            d.oids[oid] = snmp_val
