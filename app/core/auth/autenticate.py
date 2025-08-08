import os
import re
import logging
from jose import JWTError, jwt
from passlib.context import CryptContext
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, time, timedelta, timezone
from typing import List,Optional
from bson.objectid import ObjectId

from fastapi import Depends, HTTPException, status, APIRouter, Request, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Union, Optional


from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, GetJsonSchemaHandler, SerializationInfo
from pydantic_core import core_schema


router = APIRouter()

# Own Libs

import sqlite3
from .api_key_auth import get_api_key, verify_api_key, get_api_key_user,UserModel,DB_PATH,ShowUserModel


# ================= Routes ========================

def generar_password(password: str) -> str:
    secret_key = "tu_clave_secreta_muy_segura"
    
    ahora_utc = datetime.now(timezone.utc)
    expiracion = ahora_utc + timedelta(days=365)

    payload = {
        "password": password,
        "exp": expiracion,
        "iat": ahora_utc
    }

    algorithm = "HS256"
    token_firmado = jwt.encode(payload, secret_key, algorithm=algorithm)
    return token_firmado

@router.post('/user/add', response_description='Add new user', response_model=UserModel,tags=['Users'])
async def create_user(user: UserModel):
    try:
        # Validate role
        if not re.match("admin|dev|produccion", user.role):
            raise HTTPException(status_code=400, detail="Invalid role. Must be 'admin', 'dev', or 'produccion'")
        
        # Hash the password
        api_key = generar_password(user.api_keys)
        
        # Create user data dictionary
        user_data = {
            'user_name': user.user_name,
            'role': user.role,
            'is_active': 'true',
            'created_at': datetime.now(timezone.utc).isoformat(),
            'last_login': datetime.now(timezone.utc).isoformat(),
            'api_keys': api_key
        }
        
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute('SELECT 1 FROM api_keys WHERE user_name = ?',(user.user_name,))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=400, 
                        detail=f"User with username {user.user_name} already exists"
                    )
                
                # Insert the new user
                cursor.execute('''
                    INSERT INTO api_keys (
                        user_name, role, is_active, 
                        created_at, last_login, api_key
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    user_data['user_name'],
                    user_data['role'],
                    user_data['is_active'],
                    user_data['created_at'],
                    user_data['last_login'],
                    user_data['api_keys']
                ))
                conn.commit()
                
                # Get the created user
                cursor.execute(
                    'SELECT * FROM api_keys WHERE id = ?',
                    (cursor.lastrowid,)
                )
                created_user = cursor.fetchone()
                
                if not created_user:
                    raise HTTPException(
                        status_code=500, 
                        detail="Failed to retrieve created user"
                    )
                
                # Map SQLite row to dictionary
                user_dict = {
                    'user_id': created_user[0],  # id
                    'user_name': created_user[1],
                    'role': created_user[2],
                    'is_active': created_user[3],
                    'created_at': created_user[4],
                    'last_login': created_user[5],
                    'api_keys': '*****************'  # Don't return the hashed password
                }
                
                return JSONResponse(
                    status_code=status.HTTP_201_CREATED,
                    content=jsonable_encoder(user_dict)
                )
                
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Database error occurred"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the user"
        )

    raise HTTPException(status_code=406, detail="User role not acceptable")
