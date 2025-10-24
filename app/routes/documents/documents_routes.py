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
import asyncio
from pathlib import Path
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

#-------------------------------------------------------------------------------
#Variables de entorno 
load_dotenv()  
TEAMWORK_BASE_URL = os.getenv("TEAMWORK_BASE_URL")
TEAMWORK_API_KEY = os.getenv("TEAMWORK_API_KEY")
TEAMWORK_API_URL = f"{TEAMWORK_BASE_URL}/projects/api/v3/tasks/{{task_id}}.json"

TMP_DIR = Path("tmp")
TMP_DIR.mkdir(exist_ok=True)

DB_CONFIG = {
    "host": os.getenv("_HOST_MySQL_"),
    "user": os.getenv("_USER_MySQL_"),
    "password": os.getenv("_PASS_MySQL_"),
    "database": os.getenv("_DB_MySQL_"),
    "cursorclass": pymysql.cursors.DictCursor
}


@router.post("/webhook/document/get")
async def teamwork_document_get(request: Request):
    """Webhook que acepta JSON o texto plano."""
    try:
        body = await request.body()

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = {"raw": body.decode("utf-8")}
        #obtener payload al subir archivo
        #logger.info(f"Payload recibido: {payload}")

        task_id = payload.get("task", {}).get("id")
        project_id = payload.get("project", {}).get("id")

        if not task_id or not project_id:
            raise HTTPException(status_code=400, detail="Faltan 'task.id' o 'project.id' en el payload")

        logger.info(f"Task ID: {task_id} | Project ID: {project_id}")
        

        # --- Consulta de la tarea ---
        async with httpx.AsyncClient() as client:
            response = await client.get(
                TEAMWORK_API_URL.format(task_id=task_id),
                auth=(TEAMWORK_API_KEY, "x"),
                timeout=10.0
            )

        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Error al consultar Teamwork")

        task_data = response.json()
        attachments = task_data.get("task", {}).get("attachments", [])
        attachment_ids = [att["id"] for att in attachments if "id" in att]

        logger.info(f"📎 Attachments encontrados: {attachment_ids}")

        # --- Recuperar datos de cada attachment---
        attachments_data = {}

        if attachment_ids:
            async with httpx.AsyncClient(timeout=10.0) as client:
                tasks = [
                    client.get(f"{TEAMWORK_BASE_URL}/files/{att_id}.json", auth=(TEAMWORK_API_KEY, "x"))
                    for att_id in attachment_ids
                ]
                responses = await asyncio.gather(*tasks, return_exceptions=True)

                for att_id, resp in zip(attachment_ids, responses):
                    if isinstance(resp, Exception):
                        logger.error(f"Error HTTP al consultar {att_id}: {resp}")
                        continue

                    if resp.status_code == 200:
                        att_json = resp.json()
                        file_info = att_json.get("file", {})
                        attachments_data[att_id] = {
                            "name": file_info.get("name"),
                            "size": file_info.get("size"),
                            "fecha": file_info.get("createdAt")
                        }
                        # Descargar archivo del preview-url
                        preview_url = file_info.get("preview-URL")
                        if preview_url:
                            file_name = file_info.get("name", f"{att_id}.file")
                            file_path = TMP_DIR / file_name
                            try:
                                async with httpx.AsyncClient(timeout=10.0) as download_client:
                                    file_resp = await download_client.get(preview_url, follow_redirects=True)
                                    if file_resp.status_code == 200:
                                        file_path.write_bytes(file_resp.content)
                                        logger.info(f"📥 Archivo descargado: {file_path}")
                                    else:
                                        logger.warning(f"No se pudo descargar {file_name} ({file_resp.status_code})")
                            except Exception as e:
                                logger.error(f"Error descargando {file_name}: {e}")
                    else:
                        logger.warning(f"⚠️ No se pudo recuperar attachment {att_id}: {resp.status_code}")

        # --- Insertar en la base de datos ---
        if attachments_data:
            try:
                import pymysql
                from datetime import datetime
                import os

                connection = pymysql.connect(
                    host=os.getenv("_HOST_MySQL_"),
                    user=os.getenv("_USER_MySQL_"),
                    password=os.getenv("_PASS_MySQL_"),
                    database=os.getenv("_DB_MySQL_"),
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )

                with connection.cursor() as cursor:
                    sql = """
                        INSERT INTO files_procceded 
                        (id_tw, id_tarea, id_file, file_name, size, fecha, procceded)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            file_name = VALUES(file_name),
                            size = VALUES(size),
                            fecha = VALUES(fecha)
                    """
                    data_to_insert = []
                    for att_id, data in attachments_data.items():
                        fecha_raw = data.get("fecha")
                        try:
                            fecha = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))
                        except Exception:
                            fecha = datetime.utcnow()

                        data_to_insert.append((
                            project_id,
                            task_id,
                            att_id,
                            data.get("name"),
                            data.get("size"),
                            fecha,
                            0
                        ))

                    cursor.executemany(sql, data_to_insert)
                    logger.info(f"✅ {len(data_to_insert)} archivos registrados en la BD")

            except Exception as db_err:
                logger.error(f"❌ Error al insertar en la base de datos: {db_err}")
            finally:
                try:
                    connection.close()
                except:
                    pass

        # --- Construir respuesta ---
        response_data = {
            "status": "ok",
            "project_id": project_id,
            "task_id": task_id,
            "attachment_ids": attachment_ids,
            "attachments_data": attachments_data,
            "reason": "Tarea y attachments consultados correctamente"
        }

        logger.info(f"📤 Respuesta final: {response_data}")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"💥 Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
