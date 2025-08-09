import streamlit as st
from sqlalchemy.orm import Session
from utils.database import get_db
from utils.ordenes_trabajo import create_orden_trabajo, get_ordenes_trabajo, update_orden_estado
import pandas as pd
from datetime import datetime

def show_ordenes_page():
    st.title("📋 Gestión de Órdenes de Trabajo")

    st.write("---")

    # Muestra un formulario para crear una nueva orden de trabajo
    st.header("Crear Nueva Orden")
    with st.form("create_orden_form"):
        titulo = st.text_input("Título de la Orden")
        descripcion = st.text_area("Descripción")
        fecha_limite = st.date_input("Fecha Límite")
        submitted = st.form_submit_button("Crear Orden")
        
        if submitted:
            # Lógica para guardar en la base de datos
            db: Session = next(get_db())
            try:
                create_orden_trabajo(db, titulo, descripcion, datetime.combine(fecha_limite, datetime.min.time()))
                st.success("Orden de trabajo creada exitosamente!")
            finally:
                db.close()

    st.write("---")

    # Muestra las órdenes de trabajo existentes
    st.header("Órdenes de Trabajo Existentes")
    db: Session = next(get_db())
    try:
        ordenes = get_ordenes_trabajo(db)
        df_ordenes = pd.DataFrame([o.__dict__ for o in ordenes])
        if not df_ordenes.empty:
            st.dataframe(df_ordenes)
        else:
            st.info("No hay órdenes de trabajo registradas.")
    finally:
        db.close()

    st.write("---")

    # Muestra un formulario para aprobar o asignar órdenes (opcional)
    st.header("Actualizar Estado de Orden")
    orden_id = st.number_input("ID de la Orden", min_value=1)
    nuevo_estado = st.selectbox("Nuevo Estado", options=['generada', 'aprobada', 'asignada', 'en_progreso', 'completada', 'informada'])
    if st.button("Actualizar Estado"):
        db: Session = next(get_db())
        try:
            update_orden_estado(db, orden_id, nuevo_estado)
            st.success(f"Estado de la orden #{orden_id} actualizado a '{nuevo_estado}'")
            st.experimental_rerun()
        finally:
            db.close()