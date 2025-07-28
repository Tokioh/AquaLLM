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

# =================== FUNCIONES PARA CONSULTAS RÁPIDAS ===================

async def consulta_saldo_actual(identificador: str) -> dict:
    """Consulta específica para saldo actual del cliente"""
    if not supabase:
        return {"error": "Conexión no disponible"}
    
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        facturas_pendientes = [f for f in datos.get('facturas', []) if f['estado_pago'] == 'Pendiente']
        total_adeudado = sum(f['monto'] for f in facturas_pendientes)
        
        return {
            "tipo_consulta": "saldo_actual",
            "titulo": "Estado de Cuenta Actual",
            "datos": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "total_adeudado": float(total_adeudado),
                "facturas_pendientes": len(facturas_pendientes),
                "proxima_fecha_vencimiento": facturas_pendientes[0]['fecha_vencimiento'] if facturas_pendientes else None
            },
            "resumen": f"Su saldo actual es de ${total_adeudado:.2f} con {len(facturas_pendientes)} factura(s) pendiente(s).",
            "sugerencias": ["¿Cómo puedo pagar mi factura?", "¿Dónde puedo pagar?", "¿Hay descuentos disponibles?"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_consumo_actual(identificador: str) -> dict:
    """Consulta específica para consumo actual"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        consumos = datos.get('consumos', [])
        consumo_actual = consumos[0] if consumos else None
        promedio = sum(c['consumo_metros_cubicos'] for c in consumos) / len(consumos) if consumos else 0
        
        return {
            "tipo_consulta": "consumo_actual",
            "titulo": "Consumo de Agua Actual",
            "datos": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "consumo_actual": consumo_actual['consumo_metros_cubicos'] if consumo_actual else 0,
                "periodo": consumo_actual['periodo'] if consumo_actual else "",
                "promedio_6_meses": round(promedio, 2),
                "diferencia_promedio": round((consumo_actual['consumo_metros_cubicos'] - promedio) if consumo_actual else 0, 2)
            },
            "resumen": f"Su consumo en {consumo_actual['periodo'] if consumo_actual else 'el periodo actual'} es de {consumo_actual['consumo_metros_cubicos'] if consumo_actual else 0} m³.",
            "sugerencias": ["¿Cómo ahorrar agua?", "Comparar con mes anterior", "¿Mi consumo es normal?"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_proxima_factura(identificador: str) -> dict:
    """Consulta específica para próxima fecha de vencimiento"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        facturas_pendientes = [f for f in datos.get('facturas', []) if f['estado_pago'] == 'Pendiente']
        facturas_pendientes.sort(key=lambda x: x['fecha_vencimiento'])
        proxima_factura = facturas_pendientes[0] if facturas_pendientes else None
        
        return {
            "tipo_consulta": "proxima_factura",
            "titulo": "Próximo Vencimiento",
            "datos": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "fecha_vencimiento": proxima_factura['fecha_vencimiento'] if proxima_factura else None,
                "monto": float(proxima_factura['monto']) if proxima_factura else 0,
                "periodo": proxima_factura['periodo'] if proxima_factura else "",
                "dias_restantes": "Próximo"  # Se puede implementar cálculo de días
            },
            "resumen": f"Su próxima factura vence el {proxima_factura['fecha_vencimiento'] if proxima_factura else 'N/A'} por ${proxima_factura['monto'] if proxima_factura else 0}.",
            "sugerencias": ["¿Cómo puedo pagar?", "¿Puedo pagar en línea?", "¿Dónde puedo pagar?"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_informacion_medidor(identificador: str) -> dict:
    """Consulta específica para información del medidor"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        medidor = datos.get('medidor', {})
        
        return {
            "tipo_consulta": "informacion_medidor",
            "titulo": "Información del Medidor",
            "datos": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "numero_medidor": medidor.get('numero_medidor', 'N/A'),
                "ubicacion": medidor.get('ubicacion', 'N/A'),
                "estado_servicio": datos.get('contrato', {}).get('estado_servicio', 'N/A')
            },
            "resumen": f"Su medidor #{medidor.get('numero_medidor', 'N/A')} está ubicado en {medidor.get('ubicacion', 'ubicación no especificada')}.",
            "sugerencias": ["¿Cómo cambiar mi medidor?", "¿Cómo reportar una fuga?", "Estado de mis solicitudes"]
        }
    except Exception as e:
        return {"error": str(e)}

# Mapeo de consultas rápidas
CONSULTAS_RAPIDAS = {
    "saldo_actual": consulta_saldo_actual,
    "consumo_actual": consulta_consumo_actual,
    "proxima_factura": consulta_proxima_factura,
    "informacion_medidor": consulta_informacion_medidor,
}