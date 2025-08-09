import bcrypt
from sqlalchemy.orm import Session
from .models import Usuario

def hash_password(password: str) -> str:
    """Hashea una contraseña."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con una hasheada."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def get_user_by_username(db: Session, username: str):
    """Obtiene un usuario de la base de datos por su nombre de usuario."""
    return db.query(Usuario).filter(Usuario.nombre_usuario == username).first()