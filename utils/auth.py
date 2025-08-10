# utils/auth.py

from sqlalchemy.orm import Session
from passlib.context import CryptContext
# Comentar o eliminar esta línea si ya se importa en database.py y se accede globalmente
# Si models.py está en la raíz del proyecto, déjala si es necesaria para otras funciones aquí.
from models import Usuario 

# Define el contexto de hash
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str):
    return db.query(Usuario).filter(Usuario.nombre_usuario == username).first()

# La función create_admin_user fue movida a utils/database.py
