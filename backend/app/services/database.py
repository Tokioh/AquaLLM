import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Crear una única instancia del cliente de Supabase
try:
    supabase: Client = create_client(url, key)
    print("Conexión a Supabase establecida exitosamente.")
except Exception as e:
    print(f"Error al conectar con Supabase: {e}")
    supabase = None

def get_supabase_client() -> Client:
    """Devuelve la instancia del cliente de Supabase."""
    return supabase

async def buscar_datos_cliente(identificador: str) -> dict:
    """
    Busca la información completa de un cliente y sus datos asociados
    a partir de un identificador (ID de cliente, N° de medidor o N° de factura).
    """
    if not supabase:
        return {"error": "La conexión a Supabase no está disponible."}

    datos_completos = {
        "cliente": None,
        "contrato": None,
        "medidor": None,
        "facturas": [],
        "consumos": [],
        "solicitudes": []
    }

    try:
        # Primero, intentamos buscar por número de medidor, que es muy específico
        response = supabase.table('medidores').select('*, contratos(*, clientes(*))').eq('numero_medidor', identificador).execute()
        if response.data:
            medidor = response.data[0]
            contrato = medidor['contratos']
            cliente = contrato['clientes']
            id_cliente = cliente['id_cliente']
            id_contrato = contrato['id_contrato']
            id_medidor = medidor['id_medidor']

        else:
            # Si no es un medidor, podría ser un número de factura (menos común, pero posible)
            # Esta lógica se puede expandir. Por simplicidad, nos centraremos en medidor y ID de cliente.
            # Podríamos añadir búsqueda por ID de factura o DNI del cliente aquí.

            # Intentamos buscar por ID de cliente (si el identificador es un número)
            if identificador.isdigit():
                response = supabase.table('clientes').select('*').eq('id_cliente', int(identificador)).execute()
                if response.data:
                    cliente = response.data[0]
                    id_cliente = cliente['id_cliente']
                    # Ahora buscamos su contrato activo
                    contrato_res = supabase.table('contratos').select('*').eq('id_cliente', id_cliente).eq('estado_servicio', 'Activo').execute()
                    if contrato_res.data:
                        contrato = contrato_res.data[0]
                        id_contrato = contrato['id_contrato']
                        medidor_res = supabase.table('medidores').select('*').eq('id_contrato', id_contrato).execute()
                        if medidor_res.data:
                            medidor = medidor_res.data[0]
                            id_medidor = medidor['id_medidor']

        # Si hemos encontrado un cliente y contrato, recopilamos el resto de la información
        if 'id_cliente' in locals():
            datos_completos['cliente'] = cliente
            datos_completos['contrato'] = contrato
            datos_completos['medidor'] = medidor

            # Buscar facturas, consumos y solicitudes
            facturas_res = supabase.table('facturas').select('*').eq('id_contrato', id_contrato).order('periodo', desc=True).limit(5).execute()
            datos_completos['facturas'] = facturas_res.data

            consumos_res = supabase.table('consumos').select('*').eq('id_medidor', id_medidor).order('periodo', desc=True).limit(5).execute()
            datos_completos['consumos'] = consumos_res.data

            solicitudes_res = supabase.table('solicitudes').select('*').eq('id_cliente', id_cliente).order('fecha_solicitud', desc=True).limit(3).execute()
            datos_completos['solicitudes'] = solicitudes_res.data

        return datos_completos

    except Exception as e:
        print(f"Error al buscar datos del cliente: {e}")
        return {"error": str(e)}

async def guardar_conversacion(session_id: str, pregunta: str, respuesta: str):
    """Guarda un intercambio de chat en la base de datos."""
    if not supabase or not session_id:
        return

    try:
        supabase.table('conversaciones').insert({
            "session_id": session_id,
            "pregunta": pregunta,
            "respuesta": respuesta
        }).execute()
    except Exception as e:
        print(f"Error al guardar la conversación: {e}")

async def obtener_historial_conversacion(session_id: str, limit: int = 3) -> list:
    """Obtiene el historial de conversación para una sesión."""
    if not supabase or not session_id:
        return []

    try:
        response = supabase.table('conversaciones').select('pregunta, respuesta').eq('session_id', session_id).order('created_at', desc=True).limit(limit).execute()
        # Invertimos el resultado para que el orden sea cronológico
        return list(reversed(response.data))
    except Exception as e:
        print(f"Error al obtener el historial de conversación: {e}")
        return []