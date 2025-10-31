from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

# ─────────────────────────────────────────────
# Submodelo: Comentario individual recibido desde Teamwork
# ─────────────────────────────────────────────
class TaskComment(BaseModel):
    """
    Representa un comentario de tarea en Teamwork.
    """
    id: int = Field(..., description="ID único del comentario en Teamwork.")
    author_id: Optional[int] = Field(None, alias="author-id", description="ID del usuario que escribió el comentario.")
    body: Optional[str] = Field(None, description="Texto del comentario.")
    datetime: Optional[str] = Field(None, description="Fecha y hora de creación en formato ISO.")
    projectId: Optional[int] = Field(None, description="ID del proyecto al que pertenece la tarea.")
    objectId: Optional[int] = Field(None, description="ID de la tarea a la que pertenece el comentario.")

    class Config:
        populate_by_name = True  # permite usar aliases como 'author-id'
        extra = "allow"


# ─────────────────────────────────────────────
# Modelo principal: payload del webhook de comentarios
# ─────────────────────────────────────────────
class WebhookTaskCommentsPayload(BaseModel):
    """
    Payload recibido desde Teamwork al crear o actualizar comentarios en tareas.
    
    Contiene información del comentario y de la tarea asociada.
    """
    comment: Optional[TaskComment] = Field(None, description="Objeto que contiene los datos del comentario recibido.")
    # Puedes agregar otros campos si el payload los contiene
    extra: Optional[Dict] = Field(None, description="Campos adicionales no tipados en el payload.")

    class Config:
        extra = "allow"