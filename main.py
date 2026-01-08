# snmpsim/main_gui.py
from gui.app import SNMPSimApp
import sv_ttk
import ctypes
import os


def apply_dark_title_bar(window):
    """
    Usa la API de Windows para forzar la barra de título a modo oscuro.
    """
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = ctypes.c_int(2)
    set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))


if __name__ == "__main__":
    app = SNMPSimApp()
    
    if os.path.exists("icon.ico"):
        app.iconbitmap("icon.ico")

    try:
        apply_dark_title_bar(app)
    except Exception as e:
        print(f"No se pudo aplicar modo oscuro a la barra: {e}")

    sv_ttk.set_theme("dark") 
    
    app.mainloop()
