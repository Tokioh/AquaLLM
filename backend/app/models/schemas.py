from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class MessageHistory(BaseModel):
    pregunta: str
    respuesta: str

class ChatRequest(BaseModel):
    question: str
    identifier: str | None = None  # El usuario puede o no proporcionar un identificador al principio
    history: Optional[List[MessageHistory]] = None  # Historial de mensajes anteriores

class ChatResponse(BaseModel):
    answer: str

class QuickQueryRequest(BaseModel):
    query_type: str  # Tipo de consulta rápida
    identifier: str  # Identificador del cliente

class StructuredResponse(BaseModel):
    query_type: str
    title: str
    data: Dict[str, Any]
    summary: str
    suggestions: List[str]