import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from utils.database import get_db, init_db
from utils.auth import get_user_by_username, verify_password
from modules.ordenes import show_ordenes_page
from modules.inventario import show_inventario_page
from modules.informes import show_reports_page

# --- Inicialización de variables de session_state (TOP-LEVEL en app.py) ---
# Se inicializan aquí para asegurar que estén presentes desde el inicio de la aplicación
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state['db_initialized'] = True
    print("Base de datos y usuario admin inicializados (primera carga).")

if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

# Inicialización de variables para la selección de ubicación jerárquica
if 'hierarchy_selection' not in st.session_state:
    st.session_state.hierarchy_selection = {}
if 'final_selected_activo_id' not in st.session_state:
    st.session_state.final_selected_activo_id = None
# --- FIN Inicialización de variables de session_state ---


def show_login_page():
    st.title("Sistema de Gestión")
    st.header("Por favor, inicia sesión para continuar.")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        db: Session = next(get_db())
        try:
            user = get_user_by_username(db, username)
            if user and verify_password(password, user.password_hash):
                st.session_state['authenticated'] = True
                st.session_state['user_id'] = user.id
                st.session_state['username'] = user.nombre_usuario
                st.session_state['user_role'] = user.rol
                st.success(f"¡Inicio de sesión exitoso! Bienvenido, {user.nombre_usuario}")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")
        finally:
            db.close()

def show_main_app():
    st.sidebar.title("Menú")
    st.sidebar.write(f"Bienvenido, {st.session_state['username']}")
    st.sidebar.write(f"Rol: {st.session_state['user_role']}")

    page = st.sidebar.radio("Navegación", ["Panel de Control", "Órdenes de Trabajo", "Inventario", "Informes"])

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.clear()
        st.rerun()

    if page == "Panel de Control":
        st.title("🏠 Panel de Control")
        st.write("¡Aquí irán tus dashboards y resúmenes!")
    elif page == "Órdenes de Trabajo":
        show_ordenes_page()
    elif page == "Inventario":
        show_inventario_page()
    elif page == "Informes":
        show_reports_page()

if not st.session_state['authenticated']:
    show_login_page()
else:
    show_main_app()
