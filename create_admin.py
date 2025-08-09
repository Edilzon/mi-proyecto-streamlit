from utils.database import SessionLocal
from utils.models import Usuario
from utils.auth import hash_password

db = SessionLocal()

def create_admin_user():
    username = "edilzon"  # Tu nombre de usuario
    password = "edilzon"  # Tu contraseña

    # Verifica si el usuario ya existe
    existing_user = db.query(Usuario).filter_by(nombre_usuario=username).first()
    if existing_user:
        print(f"El usuario '{username}' ya existe.")
        return

    # Crea el usuario si no existe
    hashed_password = hash_password(password)
    admin_user = Usuario(nombre_usuario=username, password_hash=hashed_password, rol="admin")
    db.add(admin_user)
    db.commit()
    print(f"Usuario '{username}' creado exitosamente.")

if __name__ == "__main__":
    create_admin_user()
    db.close()