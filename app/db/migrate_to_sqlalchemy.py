#!/usr/bin/env python3
"""
Script para migrar de SQLite directo a SQLAlchemy
Ejecutar una sola vez después de actualizar el código
"""

import sqlite3
import os
from app.db.database import engine, SessionLocal
from app.models.database.message import Message, Base

def migrate_existing_data():
    """Migra datos existentes de la tabla antigua a SQLAlchemy"""
    
    # 1. Crear las nuevas tablas con SQLAlchemy
    print("📦 Creando tablas con SQLAlchemy...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas")
    
    # 2. Verificar si existe la base de datos antigua
    old_db_path = "teamwork_messages.db"
    if not os.path.exists(old_db_path):
        print("ℹ️ No hay base de datos anterior, iniciando desde cero")
        return
    
    # 3. Conectar a la base de datos antigua
    print("🔄 Conectando a la base de datos existente...")
    old_conn = sqlite3.connect(old_db_path)
    old_cursor = old_conn.cursor()
    
    # 4. Verificar si existe la tabla messages antigua
    old_cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='messages'
    """)
    
    if not old_cursor.fetchone():
        print("ℹ️ No hay tabla 'messages' anterior")
        old_conn.close()
        return
    
    # 5. Obtener datos de la tabla antigua
    print("📊 Obteniendo datos existentes...")
    old_cursor.execute("""
        SELECT teamwork_id, event_type, project_id, message_content, 
               author_name, author_email, created_at, raw_payload
        FROM messages
    """)
    
    old_data = old_cursor.fetchall()
    old_conn.close()
    
    if not old_data:
        print("ℹ️ No hay datos para migrar")
        return
    
    # 6. Insertar datos en las nuevas tablas usando SQLAlchemy
    print(f"🚀 Migrando {len(old_data)} registros...")
    db = SessionLocal()
    
    try:
        migrated_count = 0
        
        for row in old_data:
            # Verificar si ya existe (evitar duplicados)
            existing = db.query(Message).filter(
                Message.teamwork_id == row[0]
            ).first()
            
            if existing:
                print(f"⚠️ Mensaje {row[0]} ya existe, omitiendo...")
                continue
            
            # Crear nuevo registro
            new_message = Message(
                teamwork_id=row[0],
                event_type=row[1],
                project_id=row[2],
                message_content=row[3],
                author_name=row[4],
                author_email=row[5],
                created_at=row[6],
                raw_payload=row[7]  # Ya viene como JSON string
            )
            
            db.add(new_message)
            migrated_count += 1
        
        # Confirmar cambios
        db.commit()
        print(f"✅ Migración completada: {migrated_count} registros migrados")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error durante la migración: {e}")
        raise
        
    finally:
        db.close()

def verify_migration():
    """Verificar que la migración fue exitosa"""
    print("\n🔍 Verificando migración...")
    
    db = SessionLocal()
    try:
        # Contar registros
        count = db.query(Message).count()
        print(f"📊 Total de mensajes en la nueva base: {count}")
        
        # Mostrar algunos registros
        if count > 0:
            latest = db.query(Message).order_by(Message.received_at.desc()).limit(3).all()
            print("📝 Últimos mensajes:")
            for msg in latest:
                print(f"  - ID: {msg.teamwork_id} | Autor: {msg.author_name} | Evento: {msg.event_type}")
                
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Iniciando migración a SQLAlchemy...")
    print("=" * 50)
    
    try:
        migrate_existing_data()
        verify_migration()
        print("\n🎉 ¡Migración completada exitosamente!")
        print("💡 Ya puedes usar tu aplicación con SQLAlchemy")
        
    except Exception as e:
        print(f"\n❌ Error en la migración: {e}")
        print("🔧 Revisa el error y vuelve a intentar")