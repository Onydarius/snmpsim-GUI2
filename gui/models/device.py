# snmpsim/models/device.py

class SNMPDevice:
    def __init__(self, name, community="public", version="2c", port=1161):
        self.name = name
        self.community = community
        self.version = version
        self.port = port
        self.oids = {}  # oid -> (type, value)

    def set_oid(self, oid, snmp_type, value):
        self.oids[oid] = (snmp_type, value)
