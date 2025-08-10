# modules/ordenes.py

import streamlit as st
from sqlalchemy.orm import Session
from datetime import datetime
from utils.database import get_db
from utils.ordenes_trabajo import (
    create_orden_trabajo, get_ordenes_trabajo, update_orden_estado,
    get_usuarios_por_rol, assign_orden_to_user, get_next_order_number,
    get_activos, get_activo_full_path, get_activo_by_id,
    find_activos_by_name_or_tag # Mantenemos la importación por si se usa en otro lugar o para futuras expansiones
)
from models import Usuario, Activo, OrdenTrabajo, ItemOrden, Producto

# Opciones de Criticidad
CRITICIDAD_OPTIONS = ["Emergencial", "Urgente", "Alto", "Medio", "Bajo"]

def show_ordenes_page():
    st.title("⚙️ Órdenes de Trabajo")

    tab1, tab2 = st.tabs(["Crear Nueva Orden", "Ver Todas las Órdenes"])

    with tab1:
        st.header("Crear Nueva Orden de Trabajo")

        db: Session = next(get_db())
        try:
            next_order_num = get_next_order_number(db)
            st.info(f"**Número de Orden:** `{next_order_num}` (Generado automáticamente)")

            generado_por_username = st.session_state.get('username', 'Desconocido')
            generado_por_id = st.session_state.get('user_id')
            st.write(f"**Generado por:** {generado_por_username}")

            titulo = st.text_input("Título de la Orden", help="Título corto que describe la tarea.")
            descripcion = st.text_area("Descripción Detallada", help="Detalles completos de la tarea a realizar.")
            criticidad = st.selectbox("Criticidad", CRITICIDAD_OPTIONS, help="Nivel de urgencia o impacto de la orden.")
            fecha_limite = st.date_input("Fecha Límite (opcional)", value=None, help="Fecha en la que la tarea debería estar completada.")
            fecha_limite_dt = datetime.combine(fecha_limite, datetime.min.time()) if fecha_limite else None

            st.subheader("Seleccionar Ubicación del Activo")

            # --- Eliminar inicialización de variables de estado del buscador de mineros aquí ---
            # if 'minero_search_query' not in st.session_state: st.session_state.minero_search_query = ""
            # if 'minero_search_results' not in st.session_state: st.session_state.minero_search_results = []
            # if 'selected_minero_id' not in st.session_state: st.session_state.selected_minero_id = None
            # if 'minero_search_active' not in st.session_state: st.session_state.minero_search_active = False

            current_parent_id_for_loop = None # Rastrea el ID del padre para el nivel actual del selector
            
            # --- SELECCIÓN JERÁRQUICA (Cascading Selectboxes) ---
            level = 0
            while True:
                level_key = f'level_{level}'
                
                current_level_activos = get_activos(db, parent_id=current_parent_id_for_loop)

                if not current_level_activos:
                    # Si no hay más hijos, la selección final es el último current_parent_id_for_loop
                    st.session_state.final_selected_activo_id = current_parent_id_for_loop
                    break

                options_labels = ["--- Selecciona ---"] + [f"{a.nombre} ({a.tipo})" for a in current_level_activos]
                options_ids = [None] + [a.id for a in current_level_activos]

                default_index = 0
                if level_key in st.session_state.hierarchy_selection and st.session_state.hierarchy_selection[level_key] is not None:
                    try:
                        default_index = options_ids.index(st.session_state.hierarchy_selection[level_key])
                    except ValueError:
                        default_index = 0

                selected_display_label = st.selectbox(
                    f"Nivel {level + 1} de Ubicación (Jerarquía)",
                    options=options_labels,
                    index=default_index,
                    key=f"ubicacion_select_level_{level}_hierarchical",
                    help=f"Selecciona un activo en el nivel {level + 1} de la jerarquía."
                )
                
                actual_selected_id = options_ids[options_labels.index(selected_display_label)] if selected_display_label != "--- Selecciona ---" else None

                if actual_selected_id != st.session_state.hierarchy_selection.get(level_key):
                    st.session_state.hierarchy_selection[level_key] = actual_selected_id
                    keys_to_delete = [k for k in st.session_state.hierarchy_selection if int(k.split('_')[1]) > level]
                    for k in keys_to_delete:
                        del st.session_state.hierarchy_selection[k]
                    
                    st.session_state.final_selected_activo_id = actual_selected_id # Actualizar el ID final
                    st.rerun() 

                if actual_selected_id is None:
                    st.session_state.final_selected_activo_id = None
                    break 
                
                current_parent_id_for_loop = actual_selected_id
                level += 1
            
            # --- FIN LÓGICA DE SELECCIÓN DE UBICACIÓN ---

            # El ID final seleccionado proviene de st.session_state.final_selected_activo_id
            selected_activo_id = st.session_state.final_selected_activo_id

            # Mostrar la ruta completa y el activo final si aplica
            if selected_activo_id:
                activo_seleccionado_obj = get_activo_by_id(db, selected_activo_id)
                if activo_seleccionado_obj:
                    # Si el activo es un "Minero", separamos la ubicación de la ruta
                    if activo_seleccionado_obj.tipo == "Minero":
                        ubicacion_path = get_activo_full_path(db, activo_seleccionado_obj.parent_id) if activo_seleccionado_obj.parent_id else "N/A"
                        st.write(f"Ubicación: **{ubicacion_path}**")
                        st.write(f"Activo Final: **{activo_seleccionado_obj.nombre}**")
                    else:
                        # Si es un nivel superior, toda la ruta es la ubicación
                        full_path_display = get_activo_full_path(db, selected_activo_id)
                        st.write(f"Ubicación: **{full_path_display}**")
                        st.write("Activo Final: N/A (Ubicación de nivel superior seleccionada)")
                else:
                    st.warning("Ubicación seleccionada no encontrada en la base de datos.")
            else:
                st.warning("Por favor, selecciona una ubicación para la orden.")


            st.subheader("Items de la Orden (Opcional)")
            st.info("La lógica para añadir ítems a la orden se implementará más adelante.")
            items_para_orden = [] 

            if st.button("Crear Orden de Trabajo"):
                if not titulo or not descripcion or not criticidad or not selected_activo_id or not generado_por_id:
                    st.error("Por favor, completa todos los campos obligatorios (Título, Descripción, Criticidad, Ubicación, Generado Por).")
                else:
                    try:
                        nueva_orden = create_orden_trabajo(
                            db=db,
                            titulo=titulo,
                            descripcion=descripcion,
                            estado="Pendiente",
                            criticidad=criticidad,
                            fecha_limite=fecha_limite_dt,
                            ubicacion_id=selected_activo_id,
                            generado_por_id=generado_por_id,
                            asignado_a_id=None,
                            items_orden=[]
                        )
                        st.success(f"Orden de Trabajo '{nueva_orden.numero_orden}' creada con éxito!")
                        
                        # Resetear la selección jerárquica y el formulario después de crear
                        st.session_state.hierarchy_selection = {}
                        st.session_state.final_selected_activo_id = None
                        # Eliminar reseteo de variables de búsqueda de mineros
                        # st.session_state.minero_search_query = ""
                        # st.session_state.minero_search_results = []
                        # st.session_state.selected_minero_id = None
                        # st.session_state.minero_search_active = False
                        st.rerun() 
                    except Exception as e:
                        st.error(f"Error al crear la orden de trabajo: {e}")

        except Exception as e:
            st.error(f"Error al cargar la página de creación de órdenes: {e}")
        finally:
            db.close()

    with tab2:
        st.header("Órdenes de Trabajo Existentes")
        db: Session = next(get_db())
        try:
            ordenes = get_ordenes_trabajo(db)
            if ordenes:
                st.write("Lista de todas las órdenes de trabajo:")
                for orden in ordenes:
                    st.markdown(f"**Orden #{orden.numero_orden} - {orden.titulo}**")
                    st.write(f"  Estado: {orden.estado} | Criticidad: {orden.criticidad}")
                    
                    if orden.ubicacion_id:
                        activo_orden = get_activo_by_id(db, orden.ubicacion_id)
                        if activo_orden and activo_orden.tipo == "Minero":
                            ubicacion_path = get_activo_full_path(db, activo_orden.parent_id) if activo_orden.parent_id else "N/A"
                            st.write(f"  Ubicación: **{ubicacion_path}**")
                            st.write(f"  Activo Final: **{activo_orden.nombre}**")
                        else:
                            ubicacion_path = get_activo_full_path(db, orden.ubicacion_id)
                            st.write(f"  Ubicación: **{ubicacion_path}**")
                            st.write("  Activo Final: N/A (Ubicación de nivel superior)")
                    
                    st.write(f"  Generada por: {orden.generado_por.nombre_usuario if orden.generado_por else 'N/A'}")
                    st.write(f"  Fecha Límite: {orden.fecha_limite.strftime('%Y-%m-%d') if orden.fecha_limite else 'N/A'}")
                    st.markdown("---")
            else:
                st.info("No hay órdenes de trabajo registradas.")
        finally:
            db.close()
