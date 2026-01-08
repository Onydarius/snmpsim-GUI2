import time
import os

# Importaciones directas para evitar fallos de espacio de nombres
from pysnmp.hlapi.asyncio import SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
from pysnmp.hlapi.asyncio import getCmd

# --- CONFIGURACIÓN ---
COMMUNITY = 'site_01'        
IP = '127.0.0.1'
PORT = 1024
OID = '1.3.6.1.4.1.55555.1.4.0' 

async def get_snmp_data():
    try:
        # En las versiones más nuevas, getCmd es una corrutina (async)
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            SnmpEngine(),
            CommunityData(COMMUNITY),
            UdpTransportTarget((IP, PORT)),
            ContextData(),
            ObjectType(ObjectIdentity(OID))
        )

        if errorIndication:
            return f"Error de Red: {errorIndication}"
        elif errorStatus:
            return f"Error SNMP: {errorStatus.prettyPrint()} en {errorIndex}"
        else:
            for varBind in varBinds:
                return f"{varBind[0].prettyPrint()} = {varBind[1].prettyPrint()}"
                
    except Exception as e:
        return f"Error en el script: {str(e)}"

# Dado que Python 3.12+ requiere manejar el bucle de eventos:
import asyncio

def main():
    print(f"Iniciando monitor en {IP}:{PORT}...")
    
    async def loop():
        try:
            while True:
                resultado = await get_snmp_data()
                
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("="*60)
                print("         MONITOR SNMP - VERSIÓN ASÍNCRONA 3.14")
                print("="*60)
                print(f"Hora local:  {time.strftime('%H:%M:%S')}")
                print(f"Comunidad:   {COMMUNITY}")
                print(f"Objetivo:    {IP}:{PORT}")
                print("-" * 60)
                print(f"DATO RECUPERADO:")
                print(f"  {resultado}")
                print("-" * 60)
                print("Presiona Ctrl+C para detener.")
                
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass

    try:
        asyncio.run(loop())
    except KeyboardInterrupt:
        print("\nMonitor detenido.")

if __name__ == "__main__":
    main()