import os
import sqlite3
from pathlib import Path
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from bson import ObjectId
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, GetJsonSchemaHandler, SerializationInfo
from pydantic_core import core_schema
# ================= Model ========================

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, _handler: GetJsonSchemaHandler) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema()
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler) -> dict:
        return {"type": "string"}

    @classmethod
    def __get_pydantic_serializer__(cls, _) -> callable:
        def serializer(obj, info: SerializationInfo):
            return str(obj)
        return serializer

class UserModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_name: str
    role: str
    is_active: str
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    api_keys: str

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "user_name": "john@someone.com",
                "role": "simple mortal",
                "is_active": "false",
                "created_at": "2021-12-17 21:27:40",
                "last_login": "2021-12-17 21:27:40",
                "api_keys": "fakehashedsecret",
            }
        }
    }


class ShowUserModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_name: Optional[str]
    role: Optional[str]
    is_active: Optional[str]
    created_at: Optional[datetime]
    last_login: Optional[datetime]
    api_keys: Optional[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {   
    ObjectId: str,
    PyObjectId: str  
}
        json_schema_extra = {
            "example": {
                "user_name": "John",
                "role": "simple mortal",
                "created_at": "2021-12-17 21:27:40",
                "last_login": "2021-12-17 21:27:40",
                "api_keys": "fakehashedsecret",
            }
        }

# Database file will be stored in the project root
DB_PATH = f"{str(Path(__file__).parent.parent.parent)}/db/api_keys.db"

# Create database and table if they don't exist
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_name TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            api_key TEXT NOT NULL UNIQUE)
        ''')
        conn.commit()

# Initialize the database when this module is imported
init_db()

# Header where the API key should be provided
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str) -> bool:
    """Verify if the provided API key is valid"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            sql=f"SELECT 1 FROM api_keys WHERE api_key = '{api_key}' AND is_active = 'true'"
            cursor.execute(sql)
            result = cursor.fetchone()
            if int(result[0]) == 1:
                return True
            else:
                return False
    except Exception as e:
        print(f"Error verifying API key: {e}")
        return False

def get_api_key_user(api_key: str) -> str:
    """Get the user ID associated with an API key"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_name FROM api_keys WHERE api_key = ?',
                (api_key,)
            )
            result = cursor.fetchone()
            return result[0] if result else None
    except Exception as e:
        print(f"Error getting API key user: {e}")
        return None

# This dependency can be used in FastAPI routes
async def get_api_key(api_key: str = Depends(API_KEY_HEADER)):
    if  verify_api_key(api_key) != True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key
