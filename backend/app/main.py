from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models.schemas import ChatRequest, ChatResponse
from .services.database import buscar_datos_cliente
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