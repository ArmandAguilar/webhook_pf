# Libs System
import os
import json
import base64
import binascii

# Libs FASTAPI
from typing import Optional
from fastapi import FastAPI, Depends, Request, HTTPException, status
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from dotenv import load_dotenv

#=============START ROUTE HERES=============#
from app.core.autheticate import autenticate

#=============END ROUTE HERES================#

load_dotenv()

app = FastAPI(swagger_static={})


# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="WEBHOOK PF",
        version="2.0.0",
        description="Power by Geminai",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {"url": "https://fortaingenieria.com/ind_content/uploads/2020/12/fortalogo2.png"}
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# ================ Authentication Middleware =======================
# ----------- Here authentication is based on basic scheme,
# ----------- another authentication, based on bearer scheme, is used throughout
# ---------- the application (as decribed in FastAPI oficial documentation)

@app.middleware('http')
async def authenticate(request: Request, call_next):

    # -------------------- Authentication basic scheme -----------------------------
    if "Authorization" in request.headers:
        auth = request.headers["Authorization"]
        try:
            scheme, credentials = auth.split()
            if scheme.lower() == 'basic':
                decoded = base64.b64decode(credentials).decode("ascii")
                username, _, password = decoded.partition(":")
                request.state.user = await autenticate.authenticate_user(username, password)
        except (ValueError, UnicodeDecodeError, binascii.Error):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid basic auth credentials"
            )

    response = await call_next(request)
    return response

# ================= Routers inclusion from src directory ===============
app.openapi = custom_openapi

#=============LOAD ROUTE HERES=============#
app.include_router(autenticate.router)


#=============END ROUTE HERES================#
