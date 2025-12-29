# snmpsim/io/snmpsim_writer.py

def write_snmprec(device, base_dir="data"):
    import os

    os.makedirs(base_dir, exist_ok=True)
    path = os.path.join(base_dir, f"{device.name}.snmprec")

    with open(path, "w", encoding="utf-8") as f:
        for oid, (typ, val) in device.oids.items():
            f.write(f"{oid}|{typ}|{val}\n")

    return path
