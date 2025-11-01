from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# =====================================================
# 🧩 MODELOS Pydantic para validar payloads
# =====================================================
class EventCreator(BaseModel):
    id: int
    firstName: str
    lastName: str | None = None
    avatar: str | None = None


class FileData(BaseModel):
    id: int
    name: str | None = None
    originalName: str | None = None
    projectId: int | None = None
    size: int | None = None
    dateCreated: str | None = None
    downloadURL: str | None = None
    previewURL: str | None = None


class TaskData(BaseModel):
    id: int
    projectId: int
    attachments: list | None = None


class WebhookDocumentPayload(BaseModel):
    eventCreator: EventCreator | None = None
    file: FileData | None = None
    task: TaskData | None = None

