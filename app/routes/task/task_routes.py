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


@router.post("/webhook/task/create")
async def teamwork_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Endpoint principal del webhook de Teamwork"""
    
    
    try:
        # Obtener el payload
        payload = await request.json()
        # Desestructuración
        event_creator = payload["eventCreator"]
        project = payload["project"]
        task = payload["task"]
        task_list = payload["taskList"]
        users = payload["users"]

        # Variables individuales
        # Event Creator
        creator_id = event_creator["id"]
        creator_first_name = event_creator["firstName"]
        creator_last_name = event_creator["lastName"]
        creator_avatar = event_creator["avatar"]

        # Project
        project_id = project["id"]
        project_name = project["name"]
        project_description = project["description"]
        project_status = project["status"]
        project_tags = project["tags"]
        project_owner_id = project["ownerId"]
        project_company_id = project["companyId"]
        project_category_id = project["categoryId"]
        project_date_created = project["dateCreated"]

        # Task
        task_id = task["id"]
        task_name = task["name"]
        task_description = task["description"]
        task_status = task["status"]
        task_progress = task["progress"]
        task_project_id = task["projectId"]
        task_date_created = task["dateCreated"]
        task_date_updated = task["dateUpdated"]
        task_workflows_stages = task["workflowsStages"]

        # Task List
        task_list_id = task_list["id"]
        task_list_name = task_list["name"]
        task_list_status = task_list["status"]
        task_list_project_id = task_list["projectId"]

       #2 .- SAVE TASK CREATE 
        new_task = Tasks(
            id_task = task_id,
            taskListId = task_list_id,
            task_name = task_name,
            id_project = task_project_id,
            project_name = project_name,
            id_usuario = creator_id,
            name_usuario = creator_first_name + " " + creator_last_name,
            description = task_description,
            dateCreated = datetime.fromisoformat(task_date_created.replace('Z', '+00:00'))
        )
        db.add(new_task)
        db.commit()
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


@router.post("/webhook/task/update")
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
