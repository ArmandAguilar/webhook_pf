import json
import requests
import os
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime


# Importaciones locales
from app.db.database import get_db
from app.utilities.utilities_messages import is_message_for_profesor_forta, init_database
from app.utilities.raw_text import strip_html
from app.models.database.message import Tasks

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar DB al arrancar
init_database()


@router.post("/webhook/file/upload")
async def teamwork_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Endpoint principal del webhook de Teamwork"""
    
    
    try:
        # Obtener el payload
        payload = await request.json()

        print(payload)

       #2 .- SAVE TASK CREATE 
        # new_task = Tasks(
        #     id_task = task_id,
        #     taskListId = task_list_id,
        #     task_name = task_name,
        #     id_project = task_project_id,
        #     project_name = project_name,
        #     id_usuario = creator_id,
        #     name_usuario = creator_first_name + " " + creator_last_name,
        #     description = task_description,
        #     dateCreated = datetime.fromisoformat(task_date_created.replace('Z', '+00:00'))
        # )
        # db.add(new_task)
        # db.commit()
        return {
                "status": "saved", 
                "reason": "mensaje guardado"
            }

    except json.JSONDecodeError:
        logger.error("Error: Payload no es JSON válido")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
