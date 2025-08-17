
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
#from app.models.messages.messages_model import WebhookPayload
from app.utilities.utilities_messages import is_message_for_profesor_forta, init_database
from app.utilities.raw_text import strip_html
from app.models.database.message import Message, MessageReplay

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar DB al arrancar
init_database()


@router.post("/webhook/message/create")
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
        logger.info(f"Webhook recibido: {payload['message']['id']}")
        print(payload)
        
        #1 .- EXTRACCION DE DATOS DEL MENSAJE
        # Extraer variables del eventCreator
        event_creator_id = payload["eventCreator"]["id"]
        event_creator_first_name = payload["eventCreator"]["firstName"]
        event_creator_last_name = payload["eventCreator"]["lastName"]
        event_creator_avatar = payload["eventCreator"]["avatar"]

        # Extraer variables del message
        message_id = payload["message"]["id"]
        message_subject = payload["message"]["subject"]
        message_status = payload["message"]["status"]
        message_category_id = payload["message"]["categoryId"]
        message_project_id = payload["message"]["projectId"]
        message_tags = payload["message"]["tags"]

        # Extraer variables del post
        post_id = payload["message"]["post"]["id"]
        post_body = payload["message"]["post"]["body"]
        post_content_type = payload["message"]["post"]["contentType"]
        post_status = payload["message"]["post"]["status"]
        post_user_id = payload["message"]["post"]["userId"]
        post_message_id = payload["message"]["post"]["messageId"]
        post_date_created = payload["message"]["post"]["dateCreated"]
        post_date_updated = payload["message"]["post"]["dateUpdated"]

        #2 .- VERIFICAMOS SI ES PARA PROFESOR FORTA

        post_body_raw = strip_html(post_body)
        if is_message_for_profesor_forta(post_body_raw):
            #3 .- Guardar el mensaje
            new_message = Message(
                teamwork_id = message_id,
                project_id = message_project_id,
                author_id = post_user_id,
                author_name = event_creator_first_name + " " + event_creator_last_name,
                author_email = event_creator_avatar,
                created_at = datetime.fromisoformat(post_date_created.replace('Z', '+00:00')),
                received_at = datetime.now(),
                message_content = post_body_raw
            )
            db.add(new_message)
            db.commit()
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


@router.post("/webhook/message/reply")
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

        #1 .- EXTRACCION DE DATOS DEL MENSAJE
        creator_id = payload["eventCreator"]["id"]
        creator_name = f'{payload["eventCreator"]["firstName"]} {payload["eventCreator"]["lastName"]}'
        avatar_url = payload["eventCreator"]["avatar"]

        post_id = payload["messagePost"]["id"]
        post_body = payload["messagePost"]["body"]
        message_id = payload["messagePost"]["messageId"] #teamwork_id
        created_at = payload["messagePost"]["dateCreated"]
        


        post_body_raw = strip_html(post_body)

        #2 .- VERIFICAMOS SI ES PARA PROFESOR FORTA

        post_body_raw = strip_html(post_body)
        if is_message_for_profesor_forta(post_body_raw):
            #3 .- Guardar el mensaje
            new_message = MessageReplay(
                author_id = creator_id,
                author_name = creator_name,
                post_id = post_id,
                teamwork_id = message_id,
                post_body = post_body_raw,
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            )
            db.add(new_message)
            db.commit()

            #4 .- Procesar el mensaje LLM
            headers = {'X-API-Key': os.environ.get('_API_KEY_PF_')}
            mensaje = post_body_raw.replace("\n", "").replace("\t", "")

            payload = {
                    "id_project":506482,
                    "nombre_proyecto":"TI TEAM",
                    "id_usuario":creator_id,
                    "nombre_usuario":creator_name,
                    "message":post_body_raw,
                    "status":"ready"
                }
            
            print("::Llamando al API GEMINI::")
            req_chat_send_msg = requests.post(f"{str(os.environ.get('_URL_PF_API_GEMINAI_'))}/pf/geminia/accion",data=json.dumps(payload) ,headers=headers)
            if req_chat_send_msg.status_code == 201:
                aws_data_model = json.loads(req_chat_send_msg.text)
                mensaje_modelo = aws_data_model['message']

            
                #5 .- Teamwork Reaply
                payload = {
                    "messagereply": {
                        "body": mensaje_modelo,
                        "notify": "" 
                    }
                }
                
                req_replay = requests.post(f"{str(os.environ.get('_URL_TEAMWORK_'))}/messages/{message_id}/messageReplies.json", data=json.dumps(payload), auth=(str(os.environ.get('_KEY_BOT_')), ''))
                print(req_replay.text)
                if req_replay.status_code == 201:
                    logger.info(f"Mensaje respondido: Ok")

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



# @router.get("/messages")
# async def get_messages(limit: int = 50, db: Session = Depends(get_db)):
#     """Endpoint para consultar los mensajes guardados"""
#     try:
#         # Obtener mensajes ordenados por fecha de recepción descendente
#         messages_query = db.query(Message).order_by(Message.received_at.desc()).limit(limit)
#         messages = messages_query.all()
        
#         # Convertir a diccionario para la respuesta
#         result_messages = []
#         for message in messages:
#             result_messages.append({
#                 "teamwork_id": message.teamwork_id,
#                 "event_type": message.event_type,
#                 "project_id": message.project_id,
#                 "content": message.message_content,
#                 "author_name": message.author_name,
#                 "author_email": message.author_email,
#                 "created_at": message.created_at,
#                 "received_at": message.received_at.isoformat() if message.received_at else None
#             })
        
#         return {"messages": result_messages, "total": len(result_messages)}
        
#     except Exception as e:
#         logger.error(f"Error al obtener mensajes: {e}")
#         raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# @router.get("/messages/{teamwork_id}")
# async def get_message_by_id(teamwork_id: int, db: Session = Depends(get_db)):
#     """Obtener un mensaje específico por su ID de Teamwork"""
#     try:
#         message = db.query(Message).filter(Message.teamwork_id == teamwork_id).first()
        
#         if not message:
#             raise HTTPException(status_code=404, detail="Mensaje no encontrado")
        
#         return {
#             "teamwork_id": message.teamwork_id,
#             "event_type": message.event_type,
#             "project_id": message.project_id,
#             "content": message.message_content,
#             "author_name": message.author_name,
#             "author_email": message.author_email,
#             "created_at": message.created_at,
#             "received_at": message.received_at.isoformat() if message.received_at else None,
#             "raw_payload": message.get_raw_payload()
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error al obtener mensaje {teamwork_id}: {e}")
#         raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")