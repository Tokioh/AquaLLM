from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json
import asyncio

from .models.schemas import ChatRequest, ChatResponse, QuickQueryRequest, StructuredResponse
from .services.database import buscar_datos_cliente, CONSULTAS_RAPIDAS
from .services.llm import construir_prompt, generar_respuesta_llm_ollama

app = FastAPI(
    title="AquaLLM API",
    description="API para el sistema de atención al cliente de la empresa de agua potable.",
    version="1.0.0"
)

# --- Configuración de CORS ---
# Esto permite que nuestro frontend (que se ejecutará en un dominio diferente)
# pueda comunicarse con nuestro backend.
origins = [
    "http://localhost:3000",  # La URL de desarrollo de React
    # Aquí añadiríamos la URL de nuestro frontend en producción (Vercel)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"], # Permite todas las cabeceras
)

@app.get("/")
def read_root():
    """Endpoint de bienvenida que devuelve un saludo."""
    return {"message": "¡Bienvenido a la API de AquaLLM!"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat_handler(request: ChatRequest):
    """
    Maneja las solicitudes de chat del usuario.
    """
    print(f"Recibida pregunta: '{request.question}' con identificador: '{request.identifier}'")

    identificador = request.identifier
    
    # 1. Buscar datos del cliente
    datos_cliente = await buscar_datos_cliente(identificador) if identificador else {}
    if datos_cliente.get("error"):
        raise HTTPException(status_code=500, detail=datos_cliente.get("error"))

    # 2. Construir el prompt con el historial de conversación
    historial = request.history if request.history else []
    prompt = construir_prompt(request.question, datos_cliente, historial)

    # 3. Generar respuesta del LLM usando la función de Ollama
    respuesta_llm = generar_respuesta_llm_ollama(prompt)

    # 4. Devolver la respuesta
    return ChatResponse(answer=respuesta_llm)

@app.post("/api/chat-stream")
async def chat_stream_handler(request: ChatRequest):
    """
    Maneja las solicitudes de chat con actualizaciones de estado en tiempo real.
    """
    async def generate_status_updates():
        try:
            # Paso 1: Validación inicial
            yield f"data: {json.dumps({'status': 'Iniciando procesamiento...', 'step': 1, 'total': 5})}\n\n"
            await asyncio.sleep(0.5)  # Simular tiempo de procesamiento
            
            # Paso 2: Validar identificador
            identificador = request.identifier
            if not identificador:
                yield f"data: {json.dumps({'status': 'Solicitando identificador del cliente...', 'step': 2, 'total': 5})}\n\n"
                await asyncio.sleep(0.3)
                # Construir respuesta para solicitar identificador
                historial = request.history if request.history else []
                prompt = construir_prompt(request.question, {}, historial)
                respuesta_llm = generar_respuesta_llm_ollama(prompt)
                yield f"data: {json.dumps({'status': 'Completado', 'step': 5, 'total': 5, 'response': respuesta_llm, 'done': True})}\n\n"
                return
            
            yield f"data: {json.dumps({'status': 'Identificador recibido, validando...', 'step': 2, 'total': 5})}\n\n"
            await asyncio.sleep(0.5)
            
            # Paso 3: Consultar base de datos
            yield f"data: {json.dumps({'status': 'Consultando base de datos...', 'step': 3, 'total': 5})}\n\n"
            await asyncio.sleep(0.7)
            
            datos_cliente = await buscar_datos_cliente(identificador)
            if datos_cliente.get("error"):
                yield f"data: {json.dumps({'status': 'Error en base de datos', 'step': 3, 'total': 5, 'error': datos_cliente.get('error')})}\n\n"
                return
                
            yield f"data: {json.dumps({'status': 'Datos del cliente obtenidos exitosamente', 'step': 3, 'total': 5})}\n\n"
            await asyncio.sleep(0.5)
            
            # Paso 4: Preparar consulta para IA
            yield f"data: {json.dumps({'status': 'Preparando consulta para inteligencia artificial...', 'step': 4, 'total': 5})}\n\n"
            await asyncio.sleep(0.5)
            
            historial = request.history if request.history else []
            prompt = construir_prompt(request.question, datos_cliente, historial)
            
            # Paso 5: Generar respuesta con IA
            yield f"data: {json.dumps({'status': 'Generando respuesta inteligente...', 'step': 5, 'total': 5})}\n\n"
            await asyncio.sleep(0.3)
            
            respuesta_llm = generar_respuesta_llm_ollama(prompt)
            
            # Finalizar
            yield f"data: {json.dumps({'status': 'Respuesta generada exitosamente', 'step': 5, 'total': 5, 'response': respuesta_llm, 'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': f'Error: {str(e)}', 'error': True, 'done': True})}\n\n"

    return StreamingResponse(
        generate_status_updates(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.post("/api/quick-query", response_model=StructuredResponse)
async def quick_query_handler(request: QuickQueryRequest):
    """
    Maneja consultas rápidas con respuestas estructuradas.
    """
    print(f"Consulta rápida: '{request.query_type}' para identificador: '{request.identifier}'")
    
    # Validar tipo de consulta
    if request.query_type not in CONSULTAS_RAPIDAS:
        raise HTTPException(status_code=400, detail="Tipo de consulta no válido")
    
    # Ejecutar consulta específica
    try:
        consulta_func = CONSULTAS_RAPIDAS[request.query_type]
        resultado = await consulta_func(request.identifier)
        
        if resultado.get("error"):
            raise HTTPException(status_code=404, detail=resultado["error"])
        
        return StructuredResponse(**resultado)
        
    except Exception as e:
        print(f"Error en consulta rápida: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")