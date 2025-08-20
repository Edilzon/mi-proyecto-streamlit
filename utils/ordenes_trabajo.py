# utils/ordenes_trabajo.py

from sqlalchemy.orm import Session
from sqlalchemy import func, inspect
from datetime import datetime
from models import OrdenTrabajo, Usuario, Activo, ItemOrden, Producto
from utils.database import get_db

# Constante para el número inicial de órdenes
INITIAL_ORDER_NUMBER = 10000

def get_next_order_number(db: Session) -> str:
    """
    Genera el siguiente número de orden de trabajo.
    Busca el último número de orden y le suma 1. Si no hay órdenes, usa INITIAL_ORDER_NUMBER.
    """
    last_order = db.query(OrdenTrabajo).order_by(OrdenTrabajo.id.desc()).first()
    if last_order and last_order.numero_orden.isdigit():
        next_num = int(last_order.numero_orden) + 1
    else:
        next_num = INITIAL_ORDER_NUMBER
    return str(next_num)

def create_orden_trabajo(
    db: Session,
    titulo: str,
    descripcion: str,
    estado: str,
    criticidad: str,
    fecha_limite: datetime,
    ubicacion_id: int,
    generado_por_id: int,
    asignado_a_id: int = None,
    items_orden: list = None
):
    """
    Crea una nueva orden de trabajo con todos los campos.
    """
    numero_orden = get_next_order_number(db)

    new_orden = OrdenTrabajo(
        numero_orden=numero_orden,
        titulo=titulo,
        descripcion=descripcion,
        estado=estado,
        criticidad=criticidad,
        fecha_limite=fecha_limite,
        ubicacion_id=ubicacion_id,
        generado_por_id=generado_por_id,
        asignado_a_id=asignado_a_id,
        fecha_creacion=datetime.utcnow()
    )
    
    db.add(new_orden)
    db.flush() 

    if items_orden:
        for item_data in items_orden:
            producto = db.query(Producto).filter(Producto.id == item_data["producto_id"]).first()
            if not producto:
                raise ValueError(f"Producto con ID {item_data['producto_id']} no encontrado.")
            
            item = ItemOrden(
                orden_id=new_orden.id,
                producto_id=item_data["producto_id"],
                nombre_item=item_data.get("nombre_item", producto.nombre),
                cantidad=item_data["cantidad"],
                precio_unitario_actual=producto.precio_unitario
            )
            db.add(item)
    
    db.commit()
    db.refresh(new_orden)
    return new_orden

def get_ordenes_trabajo(db: Session, estado: str = None):
    """
    Obtiene todas las órdenes de trabajo, opcionalmente filtradas por estado.
    """
    query = db.query(OrdenTrabajo).order_by(OrdenTrabajo.fecha_creacion.desc())
    if estado:
        query = query.filter(OrdenTrabajo.estado == estado)
    return query.all()

def update_orden_estado(db: Session, orden_id: int, new_estado: str):
    """
    Actualiza el estado de una orden de trabajo.
    """
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id == orden_id).first()
    if orden:
        orden.estado = new_estado
        orden.fecha_actualizacion = datetime.utcnow()
        db.commit()
        db.refresh(orden)
        return orden
    return None

def get_usuarios_por_rol(db: Session, rol: str = None):
    """
    Obtiene usuarios, opcionalmente filtrados por rol.
    """
    query = db.query(Usuario).filter(Usuario.is_activo == True)
    if rol:
        query = query.filter(Usuario.rol == rol)
    return query.all()

def assign_orden_to_user(db: Session, orden_id: int, user_id: int):
    """
    Asigna una orden de trabajo a un usuario.
    """
    orden = db.query(OrdenTrabajo).filter(OrdenTrabajo.id == orden_id).first()
    if orden:
        orden.asignado_a_id = user_id
        db.commit()
        db.refresh(orden)
        return orden
    return None

# Funciones para la jerarquía de Activos
def create_activo(db: Session, nombre: str, tipo: str, descripcion: str = None, parent_id: int = None):
    """
    Crea un nuevo activo (ubicación) en la base de datos.
    """
    new_activo = Activo(nombre=nombre, tipo=tipo, descripcion=descripcion, parent_id=parent_id)
    db.add(new_activo)
    db.commit()
    db.refresh(new_activo)
    return new_activo

def get_activos(db: Session, parent_id: int = None, for_module: str = None):
    """
    Obtiene activos, opcionalmente filtrados por su padre y por el módulo que los solicita.
    - for_module: 'ordenes' para excluir ubicaciones de inventario de nivel superior.
                  'inventario' para incluir solo ubicaciones de inventario de nivel superior.
    """
    query = db.query(Activo)

    if parent_id is not None:
        query = query.filter(Activo.parent_id == parent_id)
    else:
        query = query.filter(Activo.parent_id == None) 
        
        if for_module == 'ordenes':
            query = query.filter(
                Activo.tipo.notin_(['Centro de Almacenamiento', 'Centro de Pruebas', 'Estante']) # Excluir estantes también
            )
        elif for_module == 'inventario':
            query = query.filter(
                Activo.tipo.in_(['Centro de Almacenamiento', 'Centro de Pruebas'])
            )
            
    return query.order_by(Activo.nombre).all()

def get_activo_by_id(db: Session, activo_id: int):
    """
    Obtiene un activo por su ID.
    """
    return db.query(Activo).filter(Activo.id == activo_id).first()

def get_activo_full_path(db: Session, activo_id: int):
    """
    Obtiene la ruta completa de un activo (ej: Planta A > Almacén 1 > Rack 2).
    """
    path_parts = []
    current_activo = get_activo_by_id(db, activo_id)
    while current_activo:
        path_parts.insert(0, current_activo.nombre)
        current_activo = current_activo.parent
    return " > ".join(path_parts)

def find_activos_by_name_or_tag(db: Session, query_string: str, parent_id: int = None, activo_type: str = None) -> list[Activo]:
    """
    Busca activos por su nombre o tag (coincidencia parcial e insensible a mayúsculas/minúsculas).
    Opcionalmente, puede filtrar por parent_id y/o tipo de activo.
    Retorna una lista de Activo objects.
    """
    if not query_string:
        return []
    
    query = db.query(Activo).filter(Activo.nombre.ilike(f'%{query_string}%'))
    
    if parent_id is not None:
        query = query.filter(Activo.parent_id == parent_id)
    
    if activo_type:
        query = query.filter(Activo.tipo == activo_type)

    return query.limit(20).all()

def get_all_descendant_activo_ids(db: Session, parent_id: int) -> list[int]:
    """
    Obtiene una lista de todos los IDs de activos descendientes (incluyendo el parent_id)
    dada una ubicación padre.
    """
    if parent_id is None:
        return []

    descendants_ids = set()
    queue = [parent_id] # Usamos una cola para búsqueda en anchura

    while queue:
        current_id = queue.pop(0)
        if current_id not in descendants_ids:
            descendants_ids.add(current_id)
            # Encuentra hijos directos
            children = db.query(Activo.id).filter(Activo.parent_id == current_id).all()
            for child_id_tuple in children:
                queue.append(child_id_tuple[0])
    return list(descendants_ids)
