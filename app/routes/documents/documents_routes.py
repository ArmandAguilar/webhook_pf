import json
import requests
import os
import logging
import pymysql
from dateutil import parser
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import httpx
from app.db.db import dbMysql
from pathlib import Path
# Importaciones locales
from app.db.database import get_db
from app.utilities.utilities_messages import is_message_for_profesor_forta, init_database
from app.utilities.raw_text import strip_html
from app.models.database.message import Tasks
from app.models.documents.documents_model import WebhookDocumentPayload

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

#-------------------------------------------------------------------------------
#Variables de entorno (cambiar a la parte superior)
load_dotenv()  
TMP_DIR = Path("app/core/tmp")
TMP_DIR.mkdir(exist_ok=True)

@router.post("/webhook/document/get", tags=["TASK"])
async def teamwork_document_get(payload: WebhookDocumentPayload):
    """
    Webhook para capturar archivos nuevos o actualizados desde Teamwork.

    - Soporta eventos:
        • file.created → obtiene `task_id` desde /files/{id}.json
        • task.updated → consulta los attachments de la tarea
    """
    try:
        logger.info("🔹 Payload recibido:")
        logger.info(payload.model_dump_json(indent=4, ensure_ascii=False))

        attachments_data = {}
        project_id = None
        task_id = None

        # =====================================================
        # 1️⃣ CASO A: file.created → archivo nuevo
        # =====================================================
        if payload.file:
            file_info = payload.file
            logger.info("📄 Evento detectado: file.created")

            project_id = file_info.projectId
            file_id = file_info.id
            file_name = file_info.name or file_info.originalName

            # --- Obtener el task_id desde Teamwork (relatedItems) ---
            try:
                teamwork_url = f"{os.getenv('TEAMWORK_BASE_URL')}/projects/api/v3/files/{file_id}.json"
                resp = requests.get(teamwork_url, auth=(os.getenv('TEAMWORK_API_KEY'), "x"), timeout=10)

                if resp.status_code == 200:
                    file_data = resp.json().get("file", {})
                    related_items = file_data.get("relatedItems", {})
                    tasks = related_items.get("tasks", [])
                    task_id = tasks[0] if tasks else None
                    logger.info(f"📎 task_id obtenido: {task_id}")
                else:
                    logger.warning(f"⚠️ No se pudo obtener info del archivo {file_id}: {resp.status_code}")

            except Exception as e:
                logger.error(f"❌ Error consultando file info: {e}")

            # --- Descargar el archivo (preferir downloadURL) ---
            download_url = file_data.get("downloadURL") if "file_data" in locals() else None
            if download_url:
                try:
                    file_path = TMP_DIR / file_name
                    resp = requests.get(download_url, auth=(os.getenv('TEAMWORK_API_KEY'), "x"), timeout=15)
                    if resp.status_code == 200:
                        file_path.write_bytes(resp.content)
                        logger.info(f"📥 Archivo descargado: {file_path}")
                    else:
                        logger.warning(f"⚠️ No se pudo descargar {file_name} (status={resp.status_code})")
                except Exception as e:
                    logger.error(f"❌ Error al descargar archivo: {e}")
            else:
                logger.warning("⚠️ No hay downloadURL disponible en el archivo.")

            attachments_data[file_id] = {
                "name": file_name,
                "size": file_info.size,
                "fecha": file_info.dateCreated,
            }

        # =====================================================
        # 2️⃣ CASO B: task.updated → respaldo
        # =====================================================
        elif payload.task:
            task_info = payload.task
            task_id = task_info.id
            project_id = task_info.projectId

            logger.info(f"📎 Evento detectado: task.updated (task_id={task_id})")

            response = requests.get(
                f"{os.getenv('TEAMWORK_BASE_URL')}/projects/api/v3/tasks/{task_id}.json",
                auth=(os.getenv('TEAMWORK_API_KEY'), "x"),
                timeout=10
            )

            if response.status_code == 200:
                task_data = response.json().get("task", {})
                attachments = task_data.get("attachments", [])
                for att in attachments:
                    attachments_data[att["id"]] = {
                        "name": att.get("name"),
                        "size": att.get("size"),
                        "fecha": att.get("dateAttached"),
                    }
            else:
                logger.warning(f"⚠️ Error al consultar tarea: {response.status_code}")

        else:
            logger.warning("⚠️ Payload no contiene datos válidos de file o task.")
            return {"status": "ignored", "reason": "payload sin archivo o tarea"}

        # =====================================================
        # 3️⃣ Guardar en la base de datos
        # =====================================================
        if attachments_data:
            try:
                connection = dbMysql.conMysql()
                with connection.cursor() as cursor:
                    sql = """
                        INSERT IGNORE INTO files_procceded 
                        (id_tw, id_tarea, id_file, file_name, size, fecha, procceded)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """

                    data_to_insert = []
                    for file_id, data in attachments_data.items():
                        fecha_raw = data.get("fecha")
                        try:
                            fecha = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00")) if fecha_raw else datetime.utcnow()
                        except Exception:
                            fecha = datetime.utcnow()

                        data_to_insert.append((
                            project_id,
                            task_id,
                            file_id,
                            data.get("name"),
                            data.get("size"),
                            fecha,
                            0
                        ))

                    cursor.executemany(sql, data_to_insert)
                    connection.commit()
                    logger.info(f"✅ {len(data_to_insert)} archivo(s) insertado(s) con project_id={project_id}, task_id={task_id}.")

            except Exception as e:
                logger.error(f"❌ Error al insertar en BD: {e}")
            finally:
                try:
                    connection.close()
                except Exception:
                    pass

        return {
            "status": "ok",
            "project_id": project_id,
            "task_id": task_id,
            "attachments": attachments_data,
        }

    except Exception as e:
        logger.exception(f"💥 Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")