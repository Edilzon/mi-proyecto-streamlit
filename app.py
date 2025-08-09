import streamlit as st
import pandas as pd

# Usamos session_state para mantener el estado del usuario (logueado o no)
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def show_login_page():
    st.title("Sistema de Gestión")
    st.header("Por favor, inicia sesión para continuar.")

    username = st.text_input("Usuario")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar Sesión"):
        # Aquí es donde iría la lógica de autenticación real
        # Por ahora, usaremos una credencial de prueba
        if username == "admin" and password == "12345":
            st.session_state['authenticated'] = True
            st.success("¡Inicio de sesión exitoso!")
            # Esto recarga la página y mostrará el contenido principal
            st.rerun()
        else:
            st.error("Usuario o contraseña incorrectos.")

def show_main_app():
    # Aquí irá el contenido principal de la aplicación
    st.title("Bienvenido al Panel de Control")
    st.sidebar.title("Menú")

    # Botón para cerrar sesión
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['authenticated'] = False
        st.rerun()
    
    st.write("---")
    st.write("¡Aquí irán tus dashboards, órdenes de trabajo e inventario!")

# Lógica principal de la aplicación
# Si el usuario no está autenticado, muestra la página de login
if not st.session_state['authenticated']:
    show_login_page()
else:
    show_main_app()