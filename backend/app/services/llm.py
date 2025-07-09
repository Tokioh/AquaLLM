import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

# --- Configuración para Hugging Face (opcional, como respaldo) ---
HAPI_KEY = os.environ.get("HUGGINGFACE_API_KEY")
headers = {"Authorization": f"Bearer {HAPI_KEY}"}

# --- Configuración para Ollama (local) ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"  # Usaremos /api/generate

def construir_prompt(pregunta_usuario: str, datos_cliente: dict) -> str:
    """
    Construye el prompt para enviar a la API de Ollama.
    """

    # 1. Construir el mensaje del sistema con el contexto
    if not datos_cliente or not datos_cliente.get('cliente'):
        # Si no hay datos, pedimos el número de cliente, medidor o factura.
        return (
            f"Por favor, responde amablemente al usuario que para ayudarle, necesito que me proporcione "
            f"su número de cliente, número de medidor o número de factura. La pregunta original del usuario fue: '{pregunta_usuario}'"
        )

    contexto_str = json.dumps(datos_cliente, indent=2, default=str)
    
    prompt = (
        f"Eres un asistente virtual de atención al cliente para una empresa de agua potable. "
        f"Tu nombre es AquaBot. Eres amable, servicial y muy preciso. "
        f"Usa SOLAMENTE la información proporcionada para responder a la pregunta del cliente. "
        f"No inventes información. Si la respuesta no está en los datos, indica amablemente que no tienes esa información. "
        f"Dirígete al cliente por su nombre de pila (si está disponible). Responde en español.\n\n"
        f"Los datos devueltos deben estar organizados de manera legible y clara\n\n"
        f"si la respuesta de la base de datos es un json,transformalo y organizalo como texto plano para que se muestre de manera legible.\n\n"
        f"--- INICIO DE DATOS DEL CLIENTE ---\n"
        f"{contexto_str}\n"
        f"--- FIN DE DATOS DEL CLIENTE ---\n\n"
        f"Pregunta: {pregunta_usuario}\n"
        f"Respuesta:"
    )

    return prompt

def verificar_ollama_activo() -> dict:
    """
    Verifica si el servidor de Ollama está activo y responde en el endpoint raíz.
    """
    try:
        # Hacemos una petición GET a la raíz del servidor Ollama. Debería responder.
        response = requests.get("http://localhost:11434/", timeout=5)
        response.raise_for_status()
        return {"status": "activo", "message": response.text}
    except requests.exceptions.RequestException as e:
        return {"status": "inactivo", "error": str(e)}

def generar_respuesta_llm_ollama(prompt: str) -> str:
    """
    Envía el prompt a la API de Ollama local y devuelve la respuesta del modelo.
    """
    # URL del endpoint de generación de Ollama
    API_URL_OLLAMA = "http://localhost:11434/api/generate"
    
    # Payload para el endpoint /api/generate
    payload = {
        "model": "gemma3:latest", # O el modelo que estés usando, ej: "tinyllama", "gemma:2b"
        "prompt": prompt,
        "stream": False # Para recibir la respuesta completa de una vez
    }

    try:
        # Usamos requests.post para enviar la solicitud
        response = requests.post(API_URL_OLLAMA, json=payload, timeout=60)
        response.raise_for_status() # Lanza un error si la petición falla (ej. 404, 500)
        
        # Parseamos la respuesta JSON
        resultado = response.json()
        
        # La respuesta de /api/generate está en la clave 'response'
        if 'response' in resultado:
            return resultado['response'].strip()
        else:
            # Esto podría pasar si hay un error en el formato de respuesta de Ollama
            print(f"Respuesta inesperada de Ollama: {resultado}")
            return "Lo siento, recibí una respuesta inesperada del servicio de IA."

    except requests.exceptions.RequestException as e:
        # Captura errores de conexión, timeout, etc.
        print(f"Error al contactar la API de Ollama: {e}")
        # Devuelve un mensaje de error claro para el frontend
        return f"Error en la comunicación con el servicio local de IA. Detalles: {e}"
    except Exception as e:
        # Captura cualquier otro error inesperado
        print(f"Error inesperado en la generación de respuesta con Ollama: {e}")
        return "Ha ocurrido un error inesperado al procesar tu solicitud con el servicio local."
