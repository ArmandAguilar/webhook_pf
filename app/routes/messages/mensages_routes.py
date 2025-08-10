
import json
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

# Importaciones locales
from database import get_db
from models.message import Message
from app.utilities.utilities_messages import extract_message_data, is_message_for_profesor_forta, save_message_to_db, init_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Inicializar DB al arrancar
init_database()

def save_message_background(message_data: dict, db: Session):
    """Función para guardar mensaje en background task"""
    try:
        save_message_to_db(message_data, db)
    except Exception as e:
        logger.error(f"Error en background task: {e}")

@router.post("/webhook/teamwork")
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
        
        logger.info(f"Webhook recibido: {payload.get('event')} - Object: {payload.get('objectType')}")
        
        # Filtrar solo eventos de mensajes/comentarios
        relevant_events = [
            'message.created',
            'comment.created', 
            'post.created',
            'message.updated',
            'comment.updated'
        ]
        
        event_type = payload.get('event', '')
        if event_type not in relevant_events:
            return {"status": "ignored", "reason": "not a message event"}
        
        # Extraer datos del mensaje
        message_data = extract_message_data(payload)
        
        # Verificar si el mensaje es para el profesor forta
        content = message_data.get('content', '')
        mentions = payload.get('data', {}).get('mentions', [])
        
        if is_message_for_profesor_forta(content, mentions):
            # Guardar directamente (no en background para evitar problemas con la sesión)
            try:
                save_message_to_db(message_data, db)
                logger.info(f"Mensaje para Profesor Forta guardado: {content[:100]}...")
            except Exception as e:
                logger.error(f"Error guardando mensaje: {e}")
                # Continuar aunque falle el guardado
            
            return {
                "status": "processed",
                "message": "Mensaje para Profesor Forta guardado",
                "event": event_type,
                "message_preview": content[:100]
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


@router.get("/messages")
async def get_messages(limit: int = 50, db: Session = Depends(get_db)):
    """Endpoint para consultar los mensajes guardados"""
    try:
        # Obtener mensajes ordenados por fecha de recepción descendente
        messages_query = db.query(Message).order_by(Message.received_at.desc()).limit(limit)
        messages = messages_query.all()
        
        # Convertir a diccionario para la respuesta
        result_messages = []
        for message in messages:
            result_messages.append({
                "teamwork_id": message.teamwork_id,
                "event_type": message.event_type,
                "project_id": message.project_id,
                "content": message.message_content,
                "author_name": message.author_name,
                "author_email": message.author_email,
                "created_at": message.created_at,
                "received_at": message.received_at.isoformat() if message.received_at else None
            })
        
        return {"messages": result_messages, "total": len(result_messages)}
        
    except Exception as e:
        logger.error(f"Error al obtener mensajes: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


@router.get("/messages/{teamwork_id}")
async def get_message_by_id(teamwork_id: int, db: Session = Depends(get_db)):
    """Obtener un mensaje específico por su ID de Teamwork"""
    try:
        message = db.query(Message).filter(Message.teamwork_id == teamwork_id).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="Mensaje no encontrado")
        
        return {
            "teamwork_id": message.teamwork_id,
            "event_type": message.event_type,
            "project_id": message.project_id,
            "content": message.message_content,
            "author_name": message.author_name,
            "author_email": message.author_email,
            "created_at": message.created_at,
            "received_at": message.received_at.isoformat() if message.received_at else None,
            "raw_payload": message.get_raw_payload()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener mensaje {teamwork_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")