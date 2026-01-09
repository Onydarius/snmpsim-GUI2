# snmpsim/main_gui.py
import ctypes
import os
import sys


def resource_path(relative_path):
    try:
        # PyInstaller crea una carpeta temporal y guarda la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def apply_dark_title_bar(window):
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ctypes.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ctypes.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = ctypes.c_int(2)
    set_window_attribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(rendering_policy), ctypes.sizeof(rendering_policy))


if __name__ == "__main__":
    import multiprocessing
    import asyncio
    import shelve
    import dbm.dumb
    
        
    multiprocessing.freeze_support()
    
    if len(sys.argv) > 1 and sys.argv[1] == "-m":
        sys.modules['dbm.ndbm'] = dbm.dumb
        
        from snmpsim.commands import responder
        
        # Limpiar argumentos: [exe, -m, mod, ...] -> [exe, ...]
        sys.argv = [sys.argv[0]] + sys.argv[3:]
        
        # Parche de Event Loop para Python 3.12+
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            responder.main()
        except SystemExit:
            pass
        finally:
            loop.close()
        sys.exit(0)
        
        
    from gui.app import SNMPSimApp
    import sv_ttk
    
    app = SNMPSimApp()
    
    
    if os.path.exists("assets/icon.ico"):
        app.iconbitmap("assets/icon.ico")

    try:
        apply_dark_title_bar(app)
    except Exception as e:
        print(f"No se pudo aplicar modo oscuro a la barra: {e}")

    sv_ttk.set_theme("dark") 
    
    app.mainloop()
