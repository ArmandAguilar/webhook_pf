from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base
import json


class MessageReplay(Base):
    __tablename__ = "messages_replay"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer)
    author_name = Column(String(200))
    post_id = Column(Integer)
    teamwork_id = Column(Integer)
    post_body = Column(Text)
    created_at = Column(DateTime) 