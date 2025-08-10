# modules/informes.py

import streamlit as st
from sqlalchemy.orm import Session
from utils.database import get_db
# ¡CAMBIA ESTA LÍNEA!
# De: from utils.reports import get_ordenes_by_estado, get_inventario_stats
# A:
from utils.reports import get_ordenes_by_status_count, get_inventario_stats # <-- ¡Así es como debe quedar!

# ... el resto de tu código para informes.py ...

def show_reports_page():
    st.title("📊 Informes y Analíticas")

    db: Session = next(get_db())
    try:
        # Llama a la función corregida
        ordenes_por_estado = get_ordenes_by_status_count(db) # <-- Asegúrate de usar el nombre correcto aquí también
        st.subheader("Órdenes por Estado")
        st.table(ordenes_por_estado)

        total_items, total_value = get_inventario_stats(db)
        st.subheader("Estadísticas de Inventario")
        st.write(f"Total de Items en Inventario: **{total_items}**")
        st.write(f"Valor Total del Inventario: **${total_value:,.2f}**")
        
        # ... otras llamadas a funciones de informes ...

    except Exception as e:
        st.error(f"Error al cargar los informes: {e}")
    finally:
        db.close()