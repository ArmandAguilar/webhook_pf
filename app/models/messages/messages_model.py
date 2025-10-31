from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ─────────────────────────────────────────────
# Submodelo: Información del post o contenido del mensaje
# ─────────────────────────────────────────────
class MessagePost(BaseModel):
    """
    Representa el contenido de un mensaje o respuesta (post) enviado desde Teamwork.
    """
    id: int = Field(..., description="ID único del post o reply dentro de Teamwork.")
    raw_body: Optional[str] = Field(None, alias="raw-body", description="Cuerpo original en formato HTML (si existe).")
    body: Optional[str] = Field(None, description="Cuerpo del mensaje en texto plano o procesado.")
    dateCreated: Optional[str] = Field(None, description="Fecha de creación del mensaje en formato ISO.")
    last_changed_on: Optional[str] = Field(None, alias="last-changed-on", description="Última fecha de modificación del mensaje.")


# ─────────────────────────────────────────────
# Submodelo: Mensaje principal
# ─────────────────────────────────────────────
class MessageData(BaseModel):
    """
    Representa un mensaje principal creado en Teamwork (no un reply).
    """
    id: int = Field(..., description="ID único del mensaje en Teamwork.")
    projectId: Optional[int] = Field(None, alias="projectId", description="ID del proyecto asociado al mensaje.")
    project_id: Optional[int] = Field(None, alias="project-id", description="Alias alternativo del ID del proyecto (según payload).")
    categoryName: Optional[str] = Field(None, alias="categoryName", description="Categoría del mensaje, p.ej. 'Inbox'.")
    post: Optional[MessagePost] = Field(None, description="Contenido del mensaje (texto, cuerpo, fechas, etc.).")


# ─────────────────────────────────────────────
# Submodelo: Reply (respuesta a un mensaje existente)
# ─────────────────────────────────────────────
class ReplyData(BaseModel):
    """
    Representa una respuesta (reply) a un mensaje existente.
    """
    id: int = Field(..., description="ID único del reply o respuesta en Teamwork.")
    messageId: Optional[int] = Field(None, alias="messageId", description="ID del mensaje al que responde.")
    userId: Optional[int] = Field(None, alias="userId", description="ID del usuario autor del reply.")
    raw_body: Optional[str] = Field(None, alias="raw-body", description="Cuerpo original del reply en formato HTML.")
    body: Optional[str] = Field(None, description="Cuerpo del reply en texto plano.")
    dateCreated: Optional[str] = Field(None, description="Fecha de creación del reply en formato ISO.")
    last_changed_on: Optional[str] = Field(None, alias="last-changed-on", description="Última fecha de modificación del reply.")


# ─────────────────────────────────────────────
# Submodelo: Información del usuario creador del evento
# ─────────────────────────────────────────────
class EventCreator(BaseModel):
    """
    Representa al usuario que generó el evento (creador del mensaje o reply).
    """
    id: Optional[int] = Field(None, description="ID del usuario que generó el evento.")


# ─────────────────────────────────────────────
# Modelo principal: WebhookPayload
# ─────────────────────────────────────────────
class WebhookPayload(BaseModel):
    """
    Modelo principal del webhook recibido desde Teamwork.

    Este payload puede representar dos tipos de eventos:
    - Un mensaje nuevo (`message`)
    - Un reply a un mensaje existente (`messagePost`)

    También puede incluir información del autor (`eventCreator`).
    """
    message: Optional[MessageData] = Field(None, description="Objeto que contiene los datos de un mensaje nuevo.")
    messagePost: Optional[ReplyData] = Field(None, description="Objeto que contiene los datos de un reply a un mensaje existente.")
    eventCreator: Optional[EventCreator] = Field(None, description="Información del usuario que generó el evento (mensaje o reply).")

    class Config:
        populate_by_name = True  # Permite usar aliases como 'raw-body' o 'project-id'
        extra = "allow"