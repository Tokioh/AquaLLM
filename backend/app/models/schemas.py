from pydantic import BaseModel
from typing import List, Optional

class MessageHistory(BaseModel):
    pregunta: str
    respuesta: str

class ChatRequest(BaseModel):
    question: str
    identifier: str | None = None  # El usuario puede o no proporcionar un identificador al principio
    history: Optional[List[MessageHistory]] = None  # Historial de mensajes anteriores

class ChatResponse(BaseModel):
    answer: str