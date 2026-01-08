# utils.py
import re
import os
import platform
import subprocess

def is_valid_ip(ip: str) -> bool:
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    if not re.match(pattern, ip):
        return False
    return all(0 <= int(octet) <= 255 for octet in ip.split('.'))

def is_valid_port(port) -> bool:
    try:
        p = int(port)
        return 1 <= p <= 65535
    except (ValueError, TypeError):
        return False

def open_file_explorer(path: str) -> bool:
    if not os.path.exists(path):
        return False
    
    current_os = platform.system()
    try:
        if current_os == "Windows":
            os.startfile(path)
        elif current_os == "Darwin":  # macOS
            subprocess.Popen(["open", path])
        else:  # Linux
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False