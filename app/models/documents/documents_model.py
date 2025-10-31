from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ─────────────────────────────────────────────
# Submodelo: Información del proyecto
# ─────────────────────────────────────────────
class ProjectData(BaseModel):
    """
    Representa la información básica del proyecto asociada al evento.
    """
    id: Optional[int] = Field(None, description="ID del proyecto en Teamwork.")
    name: Optional[str] = Field(None, description="Nombre del proyecto.")
    companyId: Optional[int] = Field(None, description="ID de la compañía asociada al proyecto (opcional).")

    class Config:
        extra = "allow"  # Permite campos adicionales inesperados


# ─────────────────────────────────────────────
# Submodelo: Información de la tarea
# ─────────────────────────────────────────────
class TaskData(BaseModel):
    """
    Representa la información básica de la tarea asociada al evento.
    """
    id: Optional[int] = Field(None, description="ID de la tarea donde se subió el documento.")
    name: Optional[str] = Field(None, description="Nombre o título de la tarea.")
    projectId: Optional[int] = Field(None, description="ID del proyecto al que pertenece la tarea.")

    class Config:
        extra = "allow"


# ─────────────────────────────────────────────
# Submodelo: Información del archivo adjunto
# ─────────────────────────────────────────────
class AttachmentData(BaseModel):
    """
    Representa los datos de un archivo adjunto dentro de una tarea.
    """
    id: Optional[int] = Field(None, description="ID único del archivo en Teamwork.")
    name: Optional[str] = Field(None, description="Nombre del archivo.")
    size: Optional[int] = Field(None, description="Tamaño del archivo en bytes.")
    createdAt: Optional[str] = Field(None, description="Fecha de creación del archivo en formato ISO.")
    preview_url: Optional[str] = Field(None, alias="preview-url", description="URL para previsualizar o descargar el archivo.")

    class Config:
        populate_by_name = True
        extra = "allow"


# ─────────────────────────────────────────────
# Modelo principal: payload del webhook de documentos
# ─────────────────────────────────────────────
class WebhookDocumentPayload(BaseModel):
    """
    Payload recibido por el webhook cuando se sube o asocia un archivo a una tarea en Teamwork.
    """
    project: Optional[ProjectData] = Field(None, description="Información del proyecto al que pertenece la tarea.")
    task: Optional[TaskData] = Field(None, description="Información de la tarea relacionada.")
    attachments: Optional[List[AttachmentData]] = Field(None, description="Lista de archivos adjuntos, si aplica.")
    event: Optional[str] = Field(None, description="Tipo de evento recibido, por ejemplo: 'file_uploaded'.")

    class Config:
        extra = "allow"