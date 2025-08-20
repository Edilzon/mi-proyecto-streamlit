# utils/inventario_db.py

from sqlalchemy.orm import Session
from datetime import datetime
from models import InventarioItem, Usuario, Activo, Producto
from utils.ordenes_trabajo import get_all_descendant_activo_ids

# Número inicial para la secuencia de ítems
INITIAL_ITEM_NUMBER = 200000

def get_next_item_number(db: Session) -> str:
    """
    Genera el siguiente número de ítem de inventario.
    Busca el último número de ítem y le suma 1. Si no hay ítems, usa INITIAL_ITEM_NUMBER.
    """
    last_item = db.query(InventarioItem).order_by(InventarioItem.id.desc()).first()
    if last_item and last_item.numero_item.isdigit():
        next_num = int(last_item.numero_item) + 1
    else:
        next_num = INITIAL_ITEM_NUMBER
    return str(next_num)

def create_inventory_item(
    db: Session,
    tipo_item: str,
    numero_serie: str,
    descripcion_breve: str,
    descripcion_detallada: str,
    estado_funcionamiento: str,
    cantidad: int,
    dado_de_alta_por_id: int,
    ubicacion_id: int,
    precio_estimado_usd: float = 1.0,
    producto_asociado_id: int = None
):
    """
    Crea un nuevo ítem individual en el inventario.
    """
    next_item_num = get_next_item_number(db)

    new_item = InventarioItem(
        numero_item=next_item_num,
        tipo_item=tipo_item,
        numero_serie=numero_serie,
        descripcion_breve=descripcion_breve,
        descripcion_detallada=descripcion_detallada,
        estado_funcionamiento=estado_funcionamiento,
        fecha_alta=datetime.utcnow(),
        cantidad=cantidad,
        precio_estimado_usd=precio_estimado_usd,
        dado_de_alta_por_id=dado_de_alta_por_id,
        ubicacion_id=ubicacion_id,
        producto_asociado_id=producto_asociado_id
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item

def get_inventory_items(db: Session, item_number_filter: str = None, location_id_filter: int = None):
    """
    Obtiene todos los ítems individuales del inventario, con opciones de filtrado.
    - item_number_filter: Filtra por el número de item (coincidencia parcial).
    - location_id_filter: Filtra por la ubicación y todos sus descendientes.
    """
    query = db.query(InventarioItem).order_by(InventarioItem.fecha_alta.desc())

    if item_number_filter:
        query = query.filter(InventarioItem.numero_item.ilike(f'%{item_number_filter}%'))

    if location_id_filter:
        descendant_ids = get_all_descendant_activo_ids(db, location_id_filter)
        if descendant_ids:
            query = query.filter(InventarioItem.ubicacion_id.in_(descendant_ids))
        else:
            return []

    return query.all()

def get_inventory_item_by_id(db: Session, item_id: int):
    """
    Obtiene un ítem individual del inventario por su ID.
    """
    return db.query(InventarioItem).filter(InventarioItem.id == item_id).first()

def get_inventory_item_by_serial_or_number(db: Session, search_query: str):
    """
    Obtiene un ítem individual del inventario por su número de serie o número de item.
    """
    item = db.query(InventarioItem).filter(InventarioItem.numero_serie == search_query).first()
    if item:
        return item
    item = db.query(InventarioItem).filter(InventarioItem.numero_item == search_query).first()
    return item