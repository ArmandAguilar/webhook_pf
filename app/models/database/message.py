from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base
import json


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    teamwork_id = Column(Integer, unique=True, index=True)
    project_id = Column(Integer)
    author_id = Column(Integer)
    author_name = Column(String(200))
    author_email = Column(String(200))
    created_at = Column(DateTime) 
    received_at = Column(DateTime, server_default=func.now())
    message_content = Column(Text)

class MessageReplay(Base):
    __tablename__ = "messages_replay"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer)
    author_name = Column(String(200))
    post_id = Column(Integer)
    teamwork_id = Column(Integer)
    post_body = Column(Text)
    created_at = Column(DateTime)

class Comments(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    autor_id = Column(Integer)
    autor_name = Column(String(200))
    projectId = Column(Integer)
    objectId = Column(Integer)
    objectType = Column(String(200))
    dateCreated = Column(DateTime)
    body = Column(Text)

class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    id_task = Column(Integer)
    taskListId = Column(Integer)
    task_name = Column(String(200))
    id_project = Column(Integer)
    project_name = Column(String(200))
    id_usuario = Column(Integer)
    name_usuario = Column(String(200))
    description = Column(Text)
    dateCreated = Column(DateTime)