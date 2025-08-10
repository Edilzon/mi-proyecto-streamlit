# utils/reports.py

from sqlalchemy.orm import Session
from sqlalchemy import func
from models import Inventario, OrdenTrabajo, Usuario, Producto # Asegúrate de importar Producto también

def get_inventario_stats(db: Session):
    """
    Obtiene el total de items en inventario y el valor total.
    """
    total_items = db.query(func.sum(Inventario.cantidad)).scalar()
    total_items = total_items if total_items is not None else 0
    total_value = total_value if total_value is not None else 0

    return total_items, total_value

def get_ordenes_by_status_count(db: Session):
    """
    Cuenta el número de órdenes por estado.
    """
    return db.query(OrdenTrabajo.estado, func.count(OrdenTrabajo.id)). \
            group_by(OrdenTrabajo.estado).all()

def get_users_with_most_orders(db: Session, limit: int = 5):
    """
    Obtiene los usuarios con más órdenes asignadas.
    """
    return db.query(Usuario.nombre_usuario, func.count(OrdenTrabajo.id)). \
            join(OrdenTrabajo, Usuario.id == OrdenTrabajo.asignado_a_id). \
            group_by(Usuario.nombre_usuario). \
            order_by(func.count(OrdenTrabajo.id).desc()). \
            limit(limit).all()

