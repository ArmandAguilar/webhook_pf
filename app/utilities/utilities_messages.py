import json
import logging
from sqlalchemy.orm import Session
from models.message import Message
from database import engine, Base

logger = logging.getLogger(__name__)

def init_database():
    """Crear todas las tablas"""
    Base.metadata.create_all(bind=engine)

def save_message_to_db(message_data: dict, db: Session):
    """Guarda el mensaje en la base de datos usando SQLAlchemy"""
    try:
        # Verificar si ya existe el mensaje
        existing_message = db.query(Message).filter(
            Message.teamwork_id == message_data.get('teamwork_id')
        ).first()
        
        if existing_message:
            # Actualizar mensaje existente
            existing_message.event_type = message_data.get('event_type')
            existing_message.project_id = message_data.get('project_id')
            existing_message.message_content = message_data.get('content')
            existing_message.author_name = message_data.get('author_name')
            existing_message.author_email = message_data.get('author_email')
            existing_message.created_at = message_data.get('created_at')
            existing_message.set_raw_payload(message_data.get('raw_payload', {}))
            
            logger.info(f"Mensaje actualizado: ID {message_data.get('teamwork_id')}")
        else:
            # Crear nuevo mensaje
            new_message = Message(
                teamwork_id=message_data.get('teamwork_id'),
                event_type=message_data.get('event_type'),
                project_id=message_data.get('project_id'),
                message_content=message_data.get('content'),
                author_name=message_data.get('author_name'),
                author_email=message_data.get('author_email'),
                created_at=message_data.get('created_at')
            )
            new_message.set_raw_payload(message_data.get('raw_payload', {}))
            
            db.add(new_message)
            logger.info(f"Nuevo mensaje guardado: ID {message_data.get('teamwork_id')}")
        
        db.commit()
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error guardando mensaje: {e}")
        raise


def is_message_for_profesor_forta(content: str, mentions: list = None) -> bool:
    """Verifica si el mensaje está dirigido al profesor forta"""
    if not content:
        return False
    
    content_lower = content.lower()
    
    # Buscar menciones directas
    forta_mentions = [
        "@profesor forta",
        "@profesorforta", 
        "profesor forta",
        "@forta"
    ]
    
    # Verificar en el contenido
    for mention in forta_mentions:
        if mention in content_lower:
            return True
    
    # Verificar en las menciones (si las hay)
    if mentions:
        for mention in mentions:
            mention_text = str(mention).lower()
            if "forta" in mention_text or "profesor" in mention_text:
                return True
    
    return False

def extract_message_data(payload: dict) -> dict:
    """Extrae los datos relevantes del mensaje"""
    data = payload.get('data', {})
    
    # Diferentes estructuras según el tipo de evento
    message_content = ""
    author_name = ""
    author_email = ""
    created_at = ""
    teamwork_id = None
    
    if 'message' in data:
        message_data = data['message']
        message_content = message_data.get('body', '') or message_data.get('content', '')
        author_name = message_data.get('author', {}).get('firstName', '') + " " + message_data.get('author', {}).get('lastName', '')
        author_email = message_data.get('author', {}).get('emailAddress', '')
        created_at = message_data.get('createdOn', '') or message_data.get('dateCreated', '')
        teamwork_id = message_data.get('id')
    
    elif 'comment' in data:
        comment_data = data['comment']
        message_content = comment_data.get('body', '') or comment_data.get('content', '')
        author_name = comment_data.get('author', {}).get('firstName', '') + " " + comment_data.get('author', {}).get('lastName', '')
        author_email = comment_data.get('author', {}).get('emailAddress', '')
        created_at = comment_data.get('createdOn', '') or comment_data.get('dateCreated', '')
        teamwork_id = comment_data.get('id')
    
    # Fallback para otros tipos de contenido
    if not message_content and isinstance(data, dict):
        for key in ['body', 'content', 'description']:
            if key in data and data[key]:
                message_content = data[key]
                break
    
    return {
        'teamwork_id': teamwork_id or payload.get('objectId'),
        'event_type': payload.get('event'),
        'project_id': payload.get('projectId'),
        'content': message_content,
        'author_name': author_name.strip(),
        'author_email': author_email,
        'created_at': created_at,
        'raw_payload': payload
    }