from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.orm import declarative_base
from datetime import datetime

Base = declarative_base()

class Usuario(Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True, index=True)
    nombre_usuario = Column(String, unique=True, index=True)
    password_hash = Column(String)
    rol = Column(String, default='ejecutor') # Roles: admin, supervisor, ejecutor
    is_activo = Column(Boolean, default=True)
    ordenes_asignadas = relationship("OrdenTrabajo", back_populates="asignado_a")

class OrdenTrabajo(Base):
    __tablename__ = 'ordenes_trabajo'
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String)
    descripcion = Column(Text)
    estado = Column(String, default='generada') # Estados: generada, aprobada, asignada, en_progreso, completada, informada
    prioridad = Column(String, default='media')
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_limite = Column(DateTime)
    asignado_a_id = Column(Integer, ForeignKey('usuarios.id'))

    asignado_a = relationship("Usuario", back_populates="ordenes_asignadas")

class Inventario(Base):
    __tablename__ = 'inventario'
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, unique=True, index=True)
    descripcion = Column(Text)
    cantidad = Column(Integer)
    ubicacion = Column(String)
    precio_unidad = Column(Float)
    fecha_alta = Column(DateTime, default=datetime.utcnow)