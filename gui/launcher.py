import sys
import asyncio
import os

# Forzamos compatibilidad antes de importar snmpsim
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio._WindowsSelectorEventLoopPolicy())

# Creamos un loop explícito para evitar el error "There is no current event loop"
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Ahora sí importamos y ejecutamos snmpsim
from snmpsim.commands import responder

if __name__ == "__main__":
    # Pasamos el control al main de snmpsim
    sys.exit(responder.main())