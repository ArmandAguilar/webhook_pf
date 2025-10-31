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
async def teamwork_task_comments(request: Request):
    """Webhook que obtiene y guarda comentarios con @ProfesorF desde Teamwork."""
    try:
        body = await request.body()
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body.decode("utf-8")}

        logger.info("🔹 Payload recibido:")
        logger.info(json.dumps(payload, indent=4))

        comment = payload.get("comment", {})
        task_id = comment.get("objectId")
        project_id = comment.get("projectId")
        author_id = comment.get("userId")
        comment_body = comment.get("body", "")

        if not task_id or not project_id:
            raise HTTPException(status_code=400, detail="Faltan 'objectId' o 'projectId' en el payload")

        # 🚫 Evitar bucle infinito (si el comentario lo hizo el bot o ya contiene el texto del sistema)
        if "Mensaje recibido por el sistema" in comment_body:
            logger.info("⏭️ Comentario automático detectado, no se procesará.")
            return {"status": "ignored", "reason": "Comentario del sistema detectado."}

        logger.info(f"✅ Task ID: {task_id} | Project ID: {project_id}")

        # --- Obtener comentarios de la tarea ---
        teamwork_url = f"{os.getenv('TEAMWORK_BASE_URL')}/projects/api/v3/tasks/{task_id}/comments.json"
        response = requests.get(
            teamwork_url,
            auth=(os.getenv("TEAMWORK_API_KEY"), "x"),
            timeout=10
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error al obtener comentarios de Teamwork")

        comments_data = response.json().get("comments", [])
        logger.info(f"💬 Total de comentarios encontrados: {len(comments_data)}")

        # --- Filtrar los que contengan @ProfesorF ---
        profesor_comments = [c for c in comments_data if "@ProfesorF" in c.get("body", "")]
        logger.info(f"🎯 Comentarios con @ProfesorF: {len(profesor_comments)}")

        detailed_comments = []
        for c in profesor_comments:
            comment_id = c.get("id")
            if not comment_id:
                continue

            comment_url = f"{os.getenv('TEAMWORK_BASE_URL')}/comments/{comment_id}.json"
            detail_resp = requests.get(
                comment_url,
                auth=(os.getenv("TEAMWORK_API_KEY"), "x"),
                timeout=10
            )

            if detail_resp.status_code == 200:
                comment_detail = detail_resp.json().get("comment", {})
                detailed_comments.append({
                    "id_comment": comment_detail.get("id"),
                    "author_id": comment_detail.get("author-id"),
                    "body": comment_detail.get("body"),
                    "date": comment_detail.get("datetime")
                })

        logger.info(f"✅ Comentarios procesados: {len(detailed_comments)}")

        # --- Guardar en BD sin duplicar ---
        if detailed_comments:
            try:
                connection = dbMysql.conMysql()
                with connection.cursor() as cursor:
                    sql = """
                        INSERT IGNORE INTO task_comments_procceded
                        (id_tw, id_tarea, id_comment, id_replay_usuario, mensaje, Fecha, Procceded)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    data_to_insert = []
                    for c in detailed_comments:
                        fecha_raw = c.get("date")
                        try:
                            fecha = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00")) if fecha_raw else datetime.utcnow()
                        except Exception:
                            fecha = datetime.utcnow()

                        data_to_insert.append((
                            project_id,
                            task_id,
                            c.get("id_comment"),
                            c.get("author_id"),
                            c.get("body"),
                            fecha.date(),
                            0
                        ))

                    cursor.executemany(sql, data_to_insert)
                    connection.commit()
                    logger.info(f"✅ {len(data_to_insert)} comentarios insertados (duplicados ignorados)")
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

            # --- 💬 Enviar un solo comentario de respuesta ---
            try:
                last_comment = detailed_comments[-1]
                author_id = last_comment.get("author_id")

                reply_url = f"{os.getenv('TEAMWORK_BASE_URL')}/tasks/{task_id}/comments.json"
                reply_body = f":white_check_mark: Mensaje recibido por el sistema."

                reply_payload = {"comment": {"body": reply_body, "isPrivate": False}}

                reply_resp = requests.post(
                    reply_url,
                    auth=(os.getenv("TEAMWORK_API_KEY"), "x"),
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

        else:
            logger.info("🟡 No se encontraron comentarios con @ProfesorF para insertar ni responder")

        return {"status": "ok", "project_id": project_id, "task_id": task_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"💥 Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")