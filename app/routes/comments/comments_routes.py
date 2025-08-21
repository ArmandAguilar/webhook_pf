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
from app.models.database.message import Comments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar DB al arrancar
init_database()

@router.post("/webhook/comment/create")
async def teamwork_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Endpoint principal del webhook de Teamwork"""
    
    post_body_raw = ""
    
    try:
        # Obtener el payload
        payload = await request.json()
        print(payload)

        # Extraer variables
        creator_id = payload["eventCreator"]["id"]
        creator_first_name = payload["eventCreator"]["firstName"]
        creator_last_name = payload["eventCreator"]["lastName"]
        creator_avatar = payload["eventCreator"]["avatar"]

        comment_id = payload["comment"]["id"]
        comment_body = payload["comment"]["body"]
        comment_user_id = payload["comment"]["userId"]
        comment_object_id = payload["comment"]["objectId"]
        comment_object_type = payload["comment"]["objectType"]
        comment_project_id = payload["comment"]["projectId"]
        comment_notified_user_ids = payload["comment"]["notifiedUserIds"]
        comment_date_created = payload["comment"]["dateCreated"]
        comment_date_updated = payload["comment"]["dateUpdated"]

        #2 .- SAVE TASK CREATE 
        post_body_raw = strip_html(comment_body)
        if is_message_for_profesor_forta(post_body_raw):
            new_comment = Comments(
                autor_id = creator_id,
                autor_name = creator_first_name + " " + creator_last_name,
                projectId = comment_project_id,
                objectId = comment_object_id,
                objectType = comment_object_type,
                dateCreated = datetime.fromisoformat(comment_date_created.replace('Z', '+00:00')),
                body = post_body_raw)
        
            db.add(new_comment)
            db.commit()

            #4 .- SEND MESSAGE TO RAG
            print("::Llamando al API GEMINI::")

            headers = {'X-API-Key': os.environ.get('_API_KEY_PF_')}

            payload = {
                    "id_project":506482,
                    "nombre_proyecto":"TI TEAM",
                    "id_usuario":creator_id,
                    "nombre_usuario":creator_first_name + " " + creator_last_name,
                    "message":"extrae la informacion del archivo pdf (SLP-MP_-_Presupuesto_Adecuaciones_Proyecto_Ci (1) (5).pdf)",
                    "status":"ready"
                }
            req_chat_send_msg = requests.post(f"{str(os.environ.get('_URL_PF_API_GEMINAI_'))}/pf/geminia/accion",data=json.dumps(payload) ,headers=headers)
            if req_chat_send_msg.status_code == 201:
                aws_data_model = json.loads(req_chat_send_msg.text)
                mensaje_modelo = aws_data_model['message']

                print(mensaje_modelo)

            return {
                    "status": "saved", 
                    "reason": "mensaje guardado"
                }
        else:
            return {
                    "status": "ignored", 
                    "reason": "mensaje no dirigido al profesor forta"
                }

    except json.JSONDecodeError:
        logger.error("Error: Payload no es JSON válido")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    except Exception as e:
        logger.error(f"Error procesando webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
