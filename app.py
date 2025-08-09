import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from utils.database import get_db
from utils.auth import get_user_by_username, verify_password
from pages.ordenes import show_ordenes_page
from pages.inventario import show_inventario_page
# Usamos session_state para mantener el estado del usuario (logueado o no)
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def show_login_page():
    st.title("Sistema de Gestión")
    st.header("Por favor, inicia sesión para continuar.")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        # Obtiene la sesión de la base de datos de forma explícita
        db = next(get_db())

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
            # Asegúrate de cerrar la sesión de la base de datos
            db.close()

def show_main_app():
    st.sidebar.title(f"Bienvenido, {st.session_state['username']}")
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
        st.title("📊 Informes y Estadísticas")
        st.write("Esta sección aún no está implementada.")

# Lógica principal de la aplicación
# Si el usuario no está autenticado, muestra la página de login
if not st.session_state['authenticated']:
    show_login_page()
else:
    show_main_app()