from sqlalchemy.orm import Session
from sqlalchemy import select
from models import Inventario, Producto
from utils.database import get_db
from datetime import datetime

def create_item(db: Session, nombre: str, descripcion: str, cantidad: int, ubicacion: str, precio_unidad: float):
    """Crea un nuevo artículo en el inventario."""
    db_item = Inventario(
        nombre=nombre,
        descripcion=descripcion,
        cantidad=cantidad,
        ubicacion=ubicacion,
        precio_unidad=precio_unidad
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def get_items(db: Session):
    """Obtiene todos los artículos del inventario."""
    return db.scalars(select(Inventario)).all()

def update_item_quantity(db: Session, item_id: int, nueva_cantidad: int):
    """Actualiza la cantidad de un artículo existente."""
    item = db.query(Inventario).filter(Inventario.id == item_id).first()
    if item:
        item.cantidad = nueva_cantidad
        db.commit()
        db.refresh(item)
    return item