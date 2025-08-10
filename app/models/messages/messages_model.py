from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

# Modelo para el webhook payload
class WebhookPayload(BaseModel):
    event: str
    objectType: str
    objectId: int
    projectId: Optional[int] = None
    data: Dict[str, Any]