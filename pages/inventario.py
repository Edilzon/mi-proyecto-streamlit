import streamlit as st
from sqlalchemy.orm import Session
from utils.database import get_db
from utils.inventario_db import create_item, get_items, update_item_quantity
import pandas as pd

def show_inventario_page():
    st.title("📦 Gestión de Inventario")

    st.write("---")

    # Muestra un formulario para crear un nuevo artículo
    st.header("Dar de Alta Nuevo Artículo")
    with st.form("create_item_form"):
        nombre = st.text_input("Nombre del Artículo")
        descripcion = st.text_area("Descripción")
        cantidad = st.number_input("Cantidad Inicial", min_value=0)
        ubicacion = st.text_input("Ubicación")
        precio_unidad = st.number_input("Precio por Unidad", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Dar de Alta")
        
        if submitted:
            db: Session = next(get_db())
            try:
                create_item(db, nombre, descripcion, cantidad, ubicacion, precio_unidad)
                st.success("Artículo dado de alta exitosamente!")
            finally:
                db.close()

    st.write("---")

    # Muestra los artículos del inventario existentes
    st.header("Inventario Actual")
    db: Session = next(get_db())
    try:
        items = get_items(db)
        df_items = pd.DataFrame([i.__dict__ for i in items])
        if not df_items.empty:
            df_items = df_items.drop(columns=['_sa_instance_state']) # Limpia metadatos
            st.dataframe(df_items)
        else:
            st.info("No hay artículos en el inventario.")
    finally:
        db.close()

    st.write("---")

    # Muestra un formulario para actualizar la cantidad
    st.header("Actualizar Cantidad de Artículo")
    item_id = st.number_input("ID del Artículo", min_value=1)
    nueva_cantidad = st.number_input("Nueva Cantidad", min_value=0)
    if st.button("Actualizar Cantidad"):
        db: Session = next(get_db())
        try:
            update_item_quantity(db, item_id, nueva_cantidad)
            st.success(f"Cantidad del artículo #{item_id} actualizada a {nueva_cantidad}")
        finally:
            db.close()