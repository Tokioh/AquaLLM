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
            # Podríamos añadir búsqueda por ID de factura o Cedula del cliente aquí.

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
            "query_type": "saldo_actual",
            "title": "Estado de Cuenta Actual",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "total_adeudado": float(total_adeudado),
                "facturas_pendientes": len(facturas_pendientes),
                "proxima_fecha_vencimiento": facturas_pendientes[0]['fecha_vencimiento'] if facturas_pendientes else None
            },
            "summary": f"Su saldo actual es de ${total_adeudado:.2f} con {len(facturas_pendientes)} factura(s) pendiente(s).",
            "suggestions": ["¿Cómo puedo pagar mi factura?", "¿Dónde puedo pagar?", "¿Hay descuentos disponibles?"]
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
            "query_type": "consumo_actual",
            "title": "Consumo de Agua Actual",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "consumo_actual": consumo_actual['consumo_metros_cubicos'] if consumo_actual else 0,
                "periodo": consumo_actual['periodo'] if consumo_actual else "",
                "promedio_6_meses": round(promedio, 2),
                "diferencia_promedio": round((consumo_actual['consumo_metros_cubicos'] - promedio) if consumo_actual else 0, 2)
            },
            "summary": f"Su consumo en {consumo_actual['periodo'] if consumo_actual else 'el periodo actual'} es de {consumo_actual['consumo_metros_cubicos'] if consumo_actual else 0} m³.",
            "suggestions": ["¿Cómo ahorrar agua?", "Comparar con mes anterior", "¿Mi consumo es normal?"]
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
            "query_type": "proxima_factura",
            "title": "Próximo Vencimiento",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "fecha_vencimiento": proxima_factura['fecha_vencimiento'] if proxima_factura else None,
                "monto": float(proxima_factura['monto']) if proxima_factura else 0,
                "periodo": proxima_factura['periodo'] if proxima_factura else "",
                "dias_restantes": "Próximo"  # Se puede implementar cálculo de días
            },
            "summary": f"Su próxima factura vence el {proxima_factura['fecha_vencimiento'] if proxima_factura else 'N/A'} por ${proxima_factura['monto'] if proxima_factura else 0}.",
            "suggestions": ["¿Cómo puedo pagar?", "¿Puedo pagar en línea?", "¿Dónde puedo pagar?"]
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
            "query_type": "informacion_medidor",
            "title": "Información del Medidor",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "numero_medidor": medidor.get('numero_medidor', 'N/A'),
                "ubicacion": medidor.get('ubicacion', 'N/A'),
                "estado_servicio": datos.get('contrato', {}).get('estado_servicio', 'N/A')
            },
            "summary": f"Su medidor #{medidor.get('numero_medidor', 'N/A')} está ubicado en {medidor.get('ubicacion', 'ubicación no especificada')}.",
            "suggestions": ["¿Cómo cambiar mi medidor?", "¿Cómo reportar una fuga?", "Estado de mis solicitudes"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_promedio_facturacion(identificador: str) -> dict:
    """Consulta específica para promedio de facturación"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        facturas = datos.get('facturas', [])
        if not facturas:
            return {"error": "No hay facturas disponibles"}
        
        promedio = sum(f['monto'] for f in facturas) / len(facturas)
        total_facturas = len(facturas)
        
        return {
            "query_type": "promedio_facturacion",
            "title": "Promedio de Facturación",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "promedio_mensual": round(promedio, 2),
                "total_facturas": total_facturas,
                "monto_total": round(sum(f['monto'] for f in facturas), 2)
            },
            "summary": f"Su promedio de facturación mensual es de ${promedio:.2f} basado en {total_facturas} facturas.",
            "suggestions": ["Ver detalles de facturas", "¿Cómo reducir mi consumo?", "Historial de pagos"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_facturas_vencidas(identificador: str) -> dict:
    """Consulta específica para facturas vencidas"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        facturas_vencidas = [f for f in datos.get('facturas', []) if f['estado_pago'] == 'Vencida']
        total_vencido = sum(f['monto'] for f in facturas_vencidas)
        
        return {
            "query_type": "facturas_vencidas",
            "title": "Facturas Vencidas",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "facturas_vencidas": len(facturas_vencidas),
                "monto_total_vencido": float(total_vencido),
                "estado": "Vencidas" if facturas_vencidas else "Al día"
            },
            "summary": f"Tiene {len(facturas_vencidas)} factura(s) vencida(s) por un total de ${total_vencido:.2f}." if facturas_vencidas else "¡Excelente! No tiene facturas vencidas.",
            "suggestions": ["¿Cómo puedo pagar?", "Plan de pagos", "Evitar recargos"] if facturas_vencidas else ["Mantener al día", "Configurar recordatorios"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_promedio_consumo(identificador: str) -> dict:
    """Consulta específica para promedio de consumo"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        consumos = datos.get('consumos', [])
        if not consumos:
            return {"error": "No hay datos de consumo disponibles"}
        
        promedio = sum(c['consumo_metros_cubicos'] for c in consumos) / len(consumos)
        
        return {
            "query_type": "promedio_consumo",
            "title": "Promedio de Consumo",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "promedio_6_meses": round(promedio, 2),
                "total_periodos": len(consumos),
                "consumo_minimo": min(c['consumo_metros_cubicos'] for c in consumos),
                "consumo_maximo": max(c['consumo_metros_cubicos'] for c in consumos)
            },
            "summary": f"Su promedio de consumo es de {promedio:.2f} m³ basado en {len(consumos)} períodos.",
            "suggestions": ["¿Cómo ahorrar agua?", "Comparar con otros clientes", "Tips de eficiencia"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_comparar_mes_anterior(identificador: str) -> dict:
    """Consulta específica para comparar con mes anterior"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        consumos = datos.get('consumos', [])
        if len(consumos) < 2:
            return {"error": "No hay suficientes datos para comparar"}
        
        actual = consumos[0]['consumo_metros_cubicos']
        anterior = consumos[1]['consumo_metros_cubicos']
        diferencia = actual - anterior
        porcentaje = (diferencia / anterior * 100) if anterior > 0 else 0
        
        return {
            "query_type": "comparar_mes_anterior",
            "title": "Comparación con Mes Anterior",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "consumo_actual": actual,
                "consumo_anterior": anterior,
                "diferencia": diferencia,
                "porcentaje_cambio": round(porcentaje, 1)
            },
            "summary": f"Su consumo {'aumentó' if diferencia > 0 else 'disminuyó'} en {abs(diferencia)} m³ ({abs(porcentaje):.1f}%) respecto al mes anterior.",
            "suggestions": ["¿Por qué cambió mi consumo?", "Tips para ahorrar", "Revisar fugas"] if diferencia > 0 else ["¡Excelente ahorro!", "Mantener eficiencia"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_consumo_normal(identificador: str) -> dict:
    """Consulta específica para verificar si el consumo es normal"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        consumos = datos.get('consumos', [])
        if not consumos:
            return {"error": "No hay datos de consumo disponibles"}
        
        actual = consumos[0]['consumo_metros_cubicos']
        promedio = sum(c['consumo_metros_cubicos'] for c in consumos) / len(consumos)
        desviacion = abs(actual - promedio)
        es_normal = desviacion <= (promedio * 0.3)  # 30% de tolerancia
        
        return {
            "query_type": "consumo_normal",
            "title": "Evaluación de Consumo",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "consumo_actual": actual,
                "promedio_historico": round(promedio, 2),
                "desviacion": round(desviacion, 2),
                "evaluacion": "Normal" if es_normal else "Atípico"
            },
            "summary": f"Su consumo actual {'está dentro del rango normal' if es_normal else 'es atípico comparado con su historial'}.",
            "suggestions": ["Continuar así", "Consejos de ahorro"] if es_normal else ["Revisar posibles fugas", "Contactar servicio técnico", "Revisar hábitos de consumo"]
        }
    except Exception as e:
        return {"error": str(e)}

async def consulta_estado_solicitudes(identificador: str) -> dict:
    """Consulta específica para estado de solicitudes"""
    try:
        datos = await buscar_datos_cliente(identificador)
        if not datos.get('cliente'):
            return {"error": "Cliente no encontrado"}
        
        solicitudes = datos.get('solicitudes', [])
        abiertas = [s for s in solicitudes if s['estado_solicitud'] == 'Abierta']
        en_proceso = [s for s in solicitudes if s['estado_solicitud'] == 'En Proceso']
        cerradas = [s for s in solicitudes if s['estado_solicitud'] == 'Cerrada']
        
        return {
            "query_type": "estado_solicitudes",
            "title": "Estado de Solicitudes",
            "data": {
                "cliente": datos['cliente']['nombre'] + " " + datos['cliente']['apellido'],
                "solicitudes_abiertas": len(abiertas),
                "solicitudes_en_proceso": len(en_proceso),
                "solicitudes_cerradas": len(cerradas),
                "total_solicitudes": len(solicitudes)
            },
            "summary": f"Tiene {len(abiertas)} solicitud(es) abierta(s), {len(en_proceso)} en proceso y {len(cerradas)} cerrada(s).",
            "suggestions": ["Ver detalles de solicitudes", "Nueva solicitud", "Seguimiento de casos"]
        }
    except Exception as e:
        return {"error": str(e)}

# Funciones informativas (no requieren datos específicos del cliente)
async def consulta_reportar_fuga(identificador: str) -> dict:
    """Información sobre cómo reportar una fuga"""
    return {
        "query_type": "reportar_fuga",
        "title": "¿Cómo Reportar una Fuga?",
        "data": {
            "telefono_emergencia": "(05)262-1300 ext.3",
            "horario_atencion": "24 horas",
            "tiempo_respuesta": "2-4 horas",
            "documentos_necesarios": "Ninguno para emergencias"
        },
        "summary": "Para reportar una fuga, llame al (05)262-1300 ext.3. Atendemos 24 horas y respondemos en 2-4 horas.",
        "suggestions": ["Cerrar llave de paso", "Tomar fotos del problema", "Estar disponible para la visita"]
    }

async def consulta_cambiar_medidor(identificador: str) -> dict:
    """Información sobre cambio de medidor"""
    return {
        "query_type": "cambiar_medidor",
        "title": "¿Cómo Cambiar mi Medidor?",
        "data": {
            "proceso": "Solicitud → Inspección → Instalación",
            "tiempo_estimado": "7-15 días hábiles",
            "costo": "Varía según el tipo de medidor",
            "documentos_requeridos": "Cédula, contrato de servicio"
        },
        "summary": "El cambio de medidor toma 7-15 días hábiles. Debe presentar cédula y contrato de servicio.",
        "suggestions": ["Agendar inspección", "Tipos de medidores disponibles", "Costos del servicio"]
    }

async def consulta_como_pagar(identificador: str) -> dict:
    """Información sobre métodos de pago"""
    return {
        "query_type": "como_pagar",
        "title": "¿Cómo Puedo Pagar mi Factura?",
        "data": {
            "metodos_disponibles": "Efectivo, tarjeta, transferencia, online",
            "comision_online": "Sin comisión",
            "fecha_limite": "Hasta la fecha de vencimiento",
            "recargo_mora": "5% después del vencimiento"
        },
        "summary": "Puede pagar en efectivo, con tarjeta, transferencia o en línea sin comisión hasta la fecha de vencimiento.",
        "suggestions": ["Pagar en línea", "Ubicaciones de pago", "Configurar pago automático"]
    }

async def consulta_donde_pagar(identificador: str) -> dict:
    """Información sobre lugares de pago"""
    return {
        "query_type": "donde_pagar",
        "title": "¿Dónde Puedo Pagar?",
        "data": {
            "oficinas_principales": "Centro de Manta Epam",
            "bancos_afiliados": "Banco Pacifico, Banco guayaquil",
            "supermercados": "Megamaxi, Farmacias cruz azul",
            "horarios": "Lunes a viernes 8:00-17:00"
        },
        "summary": "Puede pagar en nuestras oficinas, bancos afiliados o supermercados de lunes a viernes de 8:00 a 17:00.",
        "suggestions": ["Oficina más cercana", "Pago en línea 24/7", "App móvil"]
    }

async def consulta_pago_online(identificador: str) -> dict:
    """Información sobre pago en línea"""
    return {
        "query_type": "pago_online",
        "title": "¿Puedo Pagar en Línea?",
        "data": {
            "disponibilidad": "24 horas, 7 días",
            "metodos_aceptados": "Tarjetas de crédito/débito",
            "comision": "Sin comisión",
            "confirmacion": "Inmediata por email y SMS"
        },
        "summary": "Sí, puede pagar en línea 24/7 con tarjetas, sin comisión y con confirmación inmediata.",
        "suggestions": ["Acceder al portal de pagos", "Descargar app móvil", "Registrarse para pago automático"]
    }

async def consulta_descuentos(identificador: str) -> dict:
    """Información sobre descuentos disponibles"""
    return {
        "query_type": "descuentos",
        "title": "¿Hay Descuentos Disponibles?",
        "data": {
            "descuento_puntual": "5% por pago antes del vencimiento",
            "descuento_tercera_edad": "10% para mayores de 65 años",
            "descuento_estudiantes": "10% para estudiantes universitarios",
            "programa_lealtad": "Puntos por pagos puntuales"
        },
        "summary": "Ofrecemos descuentos del 5% por pago puntual, 10% tercera edad y 10% estudiantes universitarios.",
        "suggestions": ["Aplicar descuento tercera edad", "Verificar elegibilidad estudiantes", "Programa de lealtad"]
    }

# Mapeo de consultas rápidas
CONSULTAS_RAPIDAS = {
    "saldo_actual": consulta_saldo_actual,
    "consumo_actual": consulta_consumo_actual,
    "proxima_factura": consulta_proxima_factura,
    "informacion_medidor": consulta_informacion_medidor,
    "promedio_facturacion": consulta_promedio_facturacion,
    "facturas_vencidas": consulta_facturas_vencidas,
    "promedio_consumo": consulta_promedio_consumo,
    "comparar_mes_anterior": consulta_comparar_mes_anterior,
    "consumo_normal": consulta_consumo_normal,
    "estado_solicitudes": consulta_estado_solicitudes,
    "reportar_fuga": consulta_reportar_fuga,
    "cambiar_medidor": consulta_cambiar_medidor,
    "como_pagar": consulta_como_pagar,
    "donde_pagar": consulta_donde_pagar,
    "pago_online": consulta_pago_online,
    "descuentos": consulta_descuentos,
}