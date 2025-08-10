# models.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from utils.base_model import Base 

# Modelo para la tabla de Usuarios
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(String, default="usuario") 
    is_activo = Column(Boolean, default=True)

    ordenes_asignadas = relationship(
        "OrdenTrabajo", 
        back_populates="asignado_a", 
        foreign_keys="OrdenTrabajo.asignado_a_id" 
    )
    
    ordenes_generadas = relationship( 
        "OrdenTrabajo", 
        back_populates="generado_por", 
        foreign_keys="OrdenTrabajo.generado_por_id" 
    )

# Modelo para la tabla de Productos
class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True, nullable=False)
    descripcion = Column(String)
    precio_unitario = Column(Float, nullable=False) 
    
    inventario = relationship("Inventario", back_populates="producto", uselist=False)

# Modelo para la tabla de Inventario
class Inventario(Base):
    __tablename__ = "inventario"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), unique=True, nullable=False)
    cantidad = Column(Integer, default=0, nullable=False)
    ultima_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    producto = relationship("Producto", back_populates="inventario")

# Modelo para la tabla de Activos (ubicaciones)
class Activo(Base):
    __tablename__ = "activos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False) 
    tipo = Column(String) 
    descripcion = Column(String)
    parent_id = Column(Integer, ForeignKey("activos.id"), nullable=True)

    # Relación de hijos (un Activo puede tener muchos hijos)
    # remote_side debe apuntar a la columna en el 'otro lado' de la relación
    # Los hijos tienen un parent_id que apunta al id de este activo.
    children = relationship(
        "Activo", 
        back_populates="parent", 
        remote_side=lambda: Activo.parent_id # <--- ¡IMPORTANTE! Usar lambda para evaluación tardía
    )
    
    # Relación de padre (un Activo solo tiene un padre)
    # remote_side debe apuntar a la columna en el 'otro lado' de la relación
    # El padre tiene un id que es apuntado por el parent_id de este activo.
    parent = relationship(
        "Activo", 
        back_populates="children", 
        remote_side=lambda: Activo.id # <--- ¡IMPORTANTE! Usar lambda para evaluación tardía
    )

    ordenes_trabajo = relationship("OrdenTrabajo", back_populates="ubicacion")

# Modelo para la tabla de Órdenes de Trabajo
class OrdenTrabajo(Base):
    __tablename__ = "ordenes_trabajo"

    id = Column(Integer, primary_key=True, index=True)
    numero_orden = Column(String, unique=True, nullable=False)
    titulo = Column(String, nullable=False)
    descripcion = Column(String)
    estado = Column(String, default="Pendiente") 
    criticidad = Column(String, nullable=False) 
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_limite = Column(DateTime, nullable=True)
    
    ubicacion_id = Column(Integer, ForeignKey("activos.id"), nullable=False)
    ubicacion = relationship("Activo", back_populates="ordenes_trabajo")

    asignado_a_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    asignado_a = relationship(
        "Usuario", 
        foreign_keys=[asignado_a_id], 
        back_populates="ordenes_asignadas"
    )

    generado_por_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False) 
    generado_por = relationship(
        "Usuario", 
        foreign_keys=[generado_por_id], 
        back_populates="ordenes_generadas" 
    )

    items = relationship("ItemOrden", back_populates="orden")

# Modelo para los Items de una Orden de Trabajo
class ItemOrden(Base):
    __tablename__ = "items_orden"

    id = Column(Integer, primary_key=True, index=True)
    orden_id = Column(Integer, ForeignKey("ordenes_trabajo.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=True) 
    nombre_item = Column(String, nullable=False) 
    cantidad = Column(Integer, nullable=False)
    precio_unitario_actual = Column(Float, nullable=False) 
    
    orden = relationship("OrdenTrabajo", back_populates="items")
    producto = relationship("Producto") 
