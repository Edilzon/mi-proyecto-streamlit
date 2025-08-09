from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .models import Base  # Importamos la base declarativa de models.py

# Configuración de la conexión a la base de datos
DATABASE_URL = "postgresql://streamlit_user:edilzon@localhost:5432/streamlit_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Función para obtener una sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Función para crear todas las tablas en la base de datos."""
    Base.metadata.create_all(bind=engine)