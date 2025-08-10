from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base
import json

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    teamwork_id = Column(Integer, unique=True, index=True)
    event_type = Column(String(100))
    project_id = Column(Integer)
    message_content = Column(Text)
    author_name = Column(String(200))
    author_email = Column(String(200))
    created_at = Column(String(50))  # Mantengo como String porque viene así de Teamwork
    received_at = Column(DateTime, server_default=func.now())
    raw_payload = Column(Text)
    
    def set_raw_payload(self, payload_dict):
        """Convierte dict a JSON string para guardar"""
        self.raw_payload = json.dumps(payload_dict) if payload_dict else None
    
    def get_raw_payload(self):
        """Convierte JSON string de vuelta a dict"""
        return json.loads(self.raw_payload) if self.raw_payload else None