import json
import requests
import os
import logging
import httpx
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

from app.db.db import dbMysql
from app.models.task.tasks_model import WebhookTaskCommentsPayload
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

#-------------------------------------------------------------------------------
#Variables de entorno (cambiar a la parte superior)
load_dotenv()  

@router.post("/webhook/task/comments", tags=["TASK"])
async def teamwork_task_comments(payload: dict):
    """
    Webhook que recibe un comentario recién creado desde Teamwork.
    Guarda en BD solo si contiene @ProfesorF (limpiando el HTML)
    y responde con un mensaje automático de confirmación.
    """
    try:
        logger.info("🔹 Payload recibido:")
        logger.info(json.dumps(payload, indent=4, ensure_ascii=False))

        comment = payload.get("comment")
        if not comment:
            return {"status": "ignored", "reason": "No hay comentario en el payload"}

        # --- Datos base ---
        task_id = comment.get("objectId")
        project_id = comment.get("projectId")
        comment_id = comment.get("id")

        
        author_id = comment.get("userId") or payload.get("eventCreator", {}).get("id") or 0

        comment_body = comment.get("body", "")

        if not task_id or not project_id:
            raise HTTPException(status_code=400, detail="Faltan 'objectId' o 'projectId' en el payload")

        # 🧹 Limpiar el texto HTML
        clean_body = strip_html(comment_body)
        logger.info(f"🧹 Texto limpio: {clean_body}")

        # 🚫 Evitar procesar mensajes automáticos del sistema
        if "Mensaje recibido por el sistema" in clean_body:
            logger.info("⏭️ Comentario automático detectado, no se procesará.")
            return {"status": "ignored", "reason": "Comentario del sistema detectado."}

        # 🚫 Evitar procesar si no menciona al profesor
        if "@profesorf" not in clean_body.lower() and "@profesorf" not in clean_body.lower():
            logger.info("🚫 No contiene @ProfesorF, se ignora.")
            return {"status": "ignored", "reason": "No contiene mención al profesor."}

        # --- Guardar en BD ---
        try:
            connection = dbMysql.conMysql()
            with connection.cursor() as cursor:
                sql = """
                    INSERT IGNORE INTO task_comments_procceded
                    (id_tw, id_tarea, id_comment, id_replay_usuario, mensaje, Fecha, Procceded)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                fecha_raw = comment.get("dateCreated")
                try:
                    fecha = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00")) if fecha_raw else datetime.utcnow()
                except Exception:
                    fecha = datetime.utcnow()

                cursor.execute(sql, (
                    project_id,           # id_tw
                    task_id,              # id_tarea
                    comment_id,           # id_comment
                    author_id,            # id_replay_usuario ✅ ahora correcto
                    clean_body,           # mensaje
                    fecha.date(),         # Fecha
                    0                     # Procceded
                ))
                connection.commit()
                logger.info("✅ Comentario insertado correctamente en BD")

        finally:
            try:
                connection.close()
            except Exception:
                pass

        # --- 💬 Enviar respuesta automática ---
        try:
            reply_url = f"{os.getenv('TEAMWORK_BASE_URL')}/tasks/{task_id}/comments.json"
            reply_body = ":white_check_mark: Mensaje recibido por el sistema."
            reply_payload = {"comment": {"body": reply_body, "isPrivate": True, "notify": str(author_id)}}

            reply_resp = requests.post(
                reply_url,
                auth=(os.getenv("KEY_BOT_PF"), "x"),
                headers={"Content-Type": "application/json"},
                json=reply_payload,
                timeout=10
            )

            if reply_resp.status_code == 201:
                logger.info(f"💬 Respuesta automática publicada en la tarea {task_id}")
            else:
                logger.warning(f"⚠️ No se pudo publicar la respuesta ({reply_resp.status_code})")

        except Exception as reply_err:
            logger.error(f"❌ Error al publicar respuesta automática: {reply_err}")

        return {
            "status": "ok",
            "message": "Comentario procesado correctamente.",
            "author_id": author_id,
            "task_id": task_id,
            "project_id": project_id
        }

    except Exception as e:
        logger.exception(f"💥 Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")