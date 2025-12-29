# snmpsim/gui/models.py
from dataclasses import dataclass, field
import uuid

@dataclass
class SimulatedDevice:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "New Device"
    community: str = "public"
    version: str = "v2c"
    context: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    data_file: str = ""
    oids: dict = field(default_factory=dict)  # oid -> SNMP object
