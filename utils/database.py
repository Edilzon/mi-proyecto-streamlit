# utils/database.py

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .base_model import Base 

from utils.auth import pwd_context 
# Importa todos los modelos aquí para que se registren con Base.metadata una sola vez.
# Si tienes más modelos (por ejemplo, Producto, Orden), impórtalos también aquí.
import models # <--- ¡IMPORTANTE! Importa models aquí

# Asegúrate de que esta URL sea la correcta y simple
# Reemplaza 'tu_contraseña' con la contraseña real que asignaste a edilzon
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://edilzon:edilzonpass@localhost/streamlit_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    print("Creando tablas de la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas.")

def create_admin_user():
    # Ya no necesitas importar Usuario aquí, porque 'models' ya se importó arriba.
    # from models import Usuario # <--- ELIMINA O COMENTA ESTA LÍNEA
    
    # Asegúrate de que Usuario esté disponible. Si models se importó arriba, ya lo está.
    # Necesitarás accederlo como models.Usuario o reimportarlo localmente si es estrictamente necesario,
    # pero para evitar la doble definición, es mejor confiar en la importación global.
    
    # Para acceder a la clase Usuario después de la importación global de 'models':
    from models import Usuario # Mantén esta línea si models.py está en la raíz del proyecto
                               # y necesitas la clase Usuario directamente en este ámbito.
                               # SQLAlchemy ya habrá registrado la tabla a través de la primera importación.
    
    db_session = SessionLocal() 
    try:
        print("Creando usuario administrador...")
        admin_user = db_session.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
        if not admin_user:
            hashed_password = pwd_context.hash("admin")
            new_admin = Usuario(nombre_usuario="admin", password_hash=hashed_password, rol="admin")
            db_session.add(new_admin)
            db_session.commit()
            print("Usuario administrador creado.")
        else:
            print("El usuario administrador ya existe.")
    except Exception as e:
        print(f"Error al crear el usuario administrador: {e}")
        db_session.rollback()
    finally:
        db_session.close()

def init_db():
    create_tables()
    create_admin_user()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
