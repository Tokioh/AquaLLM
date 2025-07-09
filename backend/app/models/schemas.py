from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    identifier: str | None = None # El usuario puede o no proporcionar un identificador al principio

class ChatResponse(BaseModel):
    answer: str