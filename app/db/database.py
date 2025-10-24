from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from pathlib import Path

# Ruta a la base de datos SQLite (usando ruta relativa)
base_dir = Path(__file__).resolve().parent.parent.parent  # Navega hasta la raíz del proyecto
path_db = base_dir / "develop_db" / "teamwork_messages.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{path_db.absolute()}"

# Crear el engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Solo necesario para SQLite
)

# Crear SessionLocal para las sesiones de la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()

# Dependency para obtener la sesión de la base de datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()