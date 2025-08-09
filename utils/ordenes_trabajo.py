from sqlalchemy.orm import Session
from .models import OrdenTrabajo
from datetime import datetime

def create_orden_trabajo(db: Session, titulo: str, descripcion: str, fecha_limite: datetime):
    """Crea una nueva orden de trabajo."""
    db_orden = OrdenTrabajo(
        titulo=titulo,
        descripcion=descripcion,
        fecha_limite=fecha_limite
    )
    db.add(db_orden)
    db.commit()
    db.refresh(db_orden)
    return db_orden

def get_ordenes_trabajo(db: Session):
    """Obtiene todas las órdenes de trabajo."""
    return db.query(OrdenTrabajo).all()

def update_orden_estado(db: Session, orden_id: int, nuevo_estado: str):
    """Actualiza el estado de una orden de trabajo."""
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id == orden_id).first()
    if orden:
        orden.estado = nuevo_estado
        db.commit()
        db.refresh(orden)
    return orden