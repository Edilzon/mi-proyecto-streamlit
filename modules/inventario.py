# modules/inventario.py

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from utils.database import get_db
from utils.ordenes_trabajo import get_activos, get_activo_full_path, get_activo_by_id
from utils.inventario_db import get_next_item_number, create_inventory_item, get_inventory_items, get_inventory_item_by_id, get_inventory_item_by_serial_or_number
from models import Producto, Usuario, InventarioItem 

# Opciones para el tipo de ítem
ITEM_TYPES = ["Minero", "Cooler", "CB", "Fuente", "Conectores", "Carcaza", "Otro"]
ESTADO_FUNCIONAMIENTO_OPTIONS = ["Funcionando", "No Funcionando"]

# Define un límite de seguridad para la profundidad de la jerarquía
MAX_HIERARCHY_DEPTH = 10 

def show_inventario_page():
    st.title("📦 Gestión de Inventario")

    tab1, tab2, tab3 = st.tabs(["Dar de alta Item", "Ver Inventario", "Actualizar Item"])

    with tab1:
        st.header("Dar de alta Nuevo Item")

        db: Session = next(get_db())
        try:
            next_item_num = get_next_item_number(db)
            st.info(f"**Número de Item:** `{next_item_num}` (Generado automáticamente)")

            dado_de_alta_por_username = st.session_state.get('username', 'Desconocido')
            dado_de_alta_por_id = st.session_state.get('user_id')
            st.write(f"**Dado de alta por:** {dado_de_alta_por_username}")

            tipo_item = st.selectbox("Tipo de Item", ITEM_TYPES, help="Categoría del item.")
            
            numero_serie = st.text_input("Número de Serie", help="Introduce o escanea el número de serie único del item.", key="numero_serie_input", value=st.session_state.get("numero_serie_input", ""))
            
            descripcion_breve = st.text_input("Descripción Breve", help="Una descripción corta del item (ej: 'Minero Antminer S19 Pro').")
            descripcion_detallada = st.text_area("Descripción Detallada", help="Información completa sobre el item, su estado físico, etc.")
            estado_funcionamiento = st.selectbox("Estado de Funcionamiento", ESTADO_FUNCIONAMIENTO_OPTIONS, help="Indica si el item está funcionando correctamente o no.")

            fecha_alta = st.date_input("Fecha de Alta", value=datetime.today(), help="Fecha en que el item fue dado de alta.")
            
            cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1, help="Cantidad de unidades de este item (usualmente 1 para items individuales).")
            precio_estimado_usd = st.number_input("Precio Estimado (USD)", min_value=0.0, value=1.0, step=0.01, format="%.2f", help="Precio estimado del item en dólares. Opcional.")

            st.subheader("Seleccionar Ubicación del Item")

            if 'inventory_hierarchy_selection' not in st.session_state:
                st.session_state.inventory_hierarchy_selection = {}
            if 'inventory_final_selected_activo_id' not in st.session_state:
                st.session_state.inventory_final_selected_activo_id = None
            
            selected_ubicacion_id = None
            current_parent_id_inventory_loop = None
            level_inventory = 0

            while True:
                # Rompe el bucle si se excede la profundidad máxima para evitar infinitos selectbox
                if level_inventory >= MAX_HIERARCHY_DEPTH:
                    st.warning(f"Se alcanzó la profundidad máxima de ubicación ({MAX_HIERARCHY_DEPTH} niveles).")
                    break

                level_key_inventory = f'inventory_level_{level_inventory}'
                
                current_level_activos_inventory = get_activos(db, parent_id=current_parent_id_inventory_loop, for_module='inventario')

                if not current_level_activos_inventory:
                    st.session_state.inventory_final_selected_activo_id = current_parent_id_inventory_loop
                    break

                options_labels_inventory = ["--- Selecciona ---"] + \
                                         [f"{a.nombre} ({a.tipo})" for a in current_level_activos_inventory]
                options_ids_inventory = [None] + [a.id for a in current_level_activos_inventory]

                default_index_inventory = 0
                if level_key_inventory in st.session_state.inventory_hierarchy_selection and \
                   st.session_state.inventory_hierarchy_selection[level_key_inventory] is not None:
                    try:
                        default_index_inventory = options_ids_inventory.index(
                            st.session_state.inventory_hierarchy_selection[level_key_inventory]
                        )
                    except ValueError:
                        default_index_inventory = 0

                selected_display_label_inventory = st.selectbox(
                    f"Nivel {level_inventory + 1} de Ubicación",
                    options=options_labels_inventory,
                    index=default_index_inventory,
                    key=f"inventory_ubicacion_select_level_{level_inventory}",
                    help=f"Selecciona la ubicación del item en el nivel {level_inventory + 1}."
                )
                
                actual_selected_id_inventory = options_ids_inventory[options_labels_inventory.index(selected_display_label_inventory)] if selected_display_label_inventory != "--- Selecciona ---" else None

                if actual_selected_id_inventory != st.session_state.inventory_hierarchy_selection.get(level_key_inventory):
                    st.session_state.inventory_hierarchy_selection[level_key_inventory] = actual_selected_id_inventory
                    keys_to_delete_inventory = []
                    for k in st.session_state.inventory_hierarchy_selection.keys():
                        if k.startswith('inventory_level_'):
                            try:
                                current_level_num = int(k.split('_')[2])
                                if current_level_num > level_inventory:
                                    keys_to_delete_inventory.append(k)
                            except (ValueError, IndexError):
                                continue

                    for k in keys_to_delete_inventory:
                        del st.session_state.inventory_hierarchy_selection[k]
                    
                    st.session_state.inventory_final_selected_activo_id = actual_selected_id_inventory
                    st.rerun()

                if actual_selected_id_inventory is None:
                    st.session_state.inventory_final_selected_activo_id = None
                    break
                
                current_parent_id_inventory_loop = actual_selected_id_inventory
                level_inventory += 1
            
            selected_ubicacion_id = st.session_state.inventory_final_selected_activo_id

            if selected_ubicacion_id:
                full_path_display_inventory = get_activo_full_path(db, selected_ubicacion_id)
                st.write(f"Ubicación seleccionada: **{full_path_display_inventory}**")
            else:
                st.warning("Por favor, selecciona una ubicación para el item.")

            productos = db.query(Producto).all()
            producto_options = {p.nombre: p.id for p in productos}
            selected_product_name = st.selectbox(
                "Asociar a Producto (Opcional):",
                options=["--- Ninguno ---"] + list(producto_options.keys()),
                help="Asocia este item a un tipo de producto existente."
            )
            producto_asociado_id = producto_options.get(selected_product_name)

            if st.button("Dar de alta Item"):
                if not tipo_item or not numero_serie or not dado_de_alta_por_id or not selected_ubicacion_id or \
                   not descripcion_breve or not descripcion_detallada or not estado_funcionamiento:
                    st.error("Por favor, completa todos los campos obligatorios (Tipo de Item, Número de Serie, Descripción Breve, Descripción Detallada, Estado de Funcionamiento, Ubicación).")
                else:
                    try:
                        new_inventory_item = create_inventory_item(
                            db=db,
                            tipo_item=tipo_item,
                            numero_serie=numero_serie,
                            descripcion_breve=descripcion_breve,
                            descripcion_detallada=descripcion_detallada,
                            estado_funcionamiento=estado_funcionamiento,
                            cantidad=cantidad,
                            dado_de_alta_por_id=dado_de_alta_por_id,
                            ubicacion_id=selected_ubicacion_id,
                            precio_estimado_usd=precio_estimado_usd,
                            producto_asociado_id=producto_asociado_id
                        )
                        st.success(f"Item {new_inventory_item.numero_item} '{new_inventory_item.numero_serie}' dado de alta exitosamente!")
                        
                        st.session_state.inventory_hierarchy_selection = {}
                        st.session_state.inventory_final_selected_activo_id = None
                        
                        st.rerun() 

                    except Exception as e:
                        st.error(f"Error al dar de alta el item: {e}")
                        if "duplicate key value violates unique constraint" in str(e).lower() and "numero_serie" in str(e).lower():
                            st.error("Error: El número de serie ingresado ya existe. Por favor, introduce uno único.")
                        elif "duplicate key value violates unique constraint" in str(e).lower() and "numero_item" in str(e).lower():
                             st.error("Error: El número de item generado ya existe. Intenta de nuevo o contacta a soporte.")

        except Exception as e:
            st.error(f"Error al cargar la página de alta de items: {e}")
        finally:
            db.close()

    with tab2:
        st.header("Ver Inventario")
        db: Session = next(get_db())
        try:
            # --- SECCIÓN DE FILTROS ---
            st.subheader("Filtros de Inventario")
            col_filter1, col_filter2 = st.columns(2)

            with col_filter1:
                item_number_filter = st.text_input("Filtrar por Número de Item:", key="filter_item_number", help="Introduce un número de item o parte de él.")
                # Si el filtro por número de ítem cambia, resetear la selección de ubicación
                if "last_item_number_filter_value" not in st.session_state:
                    st.session_state.last_item_number_filter_value = ""
                if item_number_filter != st.session_state.last_item_number_filter_value:
                    st.session_state.last_item_number_filter_value = item_number_filter
                    st.session_state.view_inventory_hierarchy_selection = {}
                    st.session_state.view_inventory_final_selected_activo_id = None
                    st.rerun()

            with col_filter2:
                # --- Filtro Jerárquico de Ubicación ---
                if 'view_inventory_hierarchy_selection' not in st.session_state:
                    st.session_state.view_inventory_hierarchy_selection = {}
                if 'view_inventory_final_selected_activo_id' not in st.session_state:
                    st.session_state.view_inventory_final_selected_activo_id = None
                
                current_parent_id_view_inventory = None
                level_view_inventory = 0
                
                selected_view_location_id = None

                while True:
                    # Rompe el bucle si se excede la profundidad máxima para evitar infinitos selectbox
                    if level_view_inventory >= MAX_HIERARCHY_DEPTH:
                        st.warning(f"Se alcanzó la profundidad máxima de ubicación ({MAX_HIERARCHY_DEPTH} niveles) para el filtro.")
                        break

                    view_level_key = f'view_inventory_level_{level_view_inventory}'
                    
                    current_view_level_activos = get_activos(db, parent_id=current_parent_id_view_inventory, for_module='inventario')

                    if not current_view_level_activos:
                        selected_view_location_id = current_parent_id_view_inventory
                        break

                    view_options_labels = ["--- Selecciona Ubicación ---"] + \
                                            [f"{a.nombre} ({a.tipo})" for a in current_view_level_activos]
                    view_options_ids = [None] + [a.id for a in current_view_level_activos]

                    default_view_index = 0
                    if view_level_key in st.session_state.view_inventory_hierarchy_selection and \
                       st.session_state.view_inventory_hierarchy_selection[view_level_key] is not None:
                        try:
                            default_view_index = view_options_ids.index(
                                st.session_state.view_inventory_hierarchy_selection[view_level_key]
                            )
                        except ValueError:
                            default_view_index = 0

                    selected_view_display_label = st.selectbox(
                        f"Ubicación (Nivel {level_view_inventory + 1}):",
                        options=view_options_labels,
                        index=default_view_index,
                        key=f"view_inventory_ubicacion_select_level_{level_view_inventory}",
                        help=f"Filtra por ubicación en el nivel {level_view_inventory + 1}."
                    )
                    
                    actual_selected_view_id = view_options_ids[view_options_labels.index(selected_view_display_label)] if selected_view_display_label != "--- Selecciona Ubicación ---" else None

                    if actual_selected_view_id != st.session_state.view_inventory_hierarchy_selection.get(view_level_key):
                        st.session_state.view_inventory_hierarchy_selection[view_level_key] = actual_selected_view_id
                        keys_to_delete_view = []
                        for k in st.session_state.view_inventory_hierarchy_selection.keys():
                            if k.startswith('view_inventory_level_'):
                                try:
                                    current_level_num = int(k.split('_')[2])
                                    if current_level_num > level_view_inventory:
                                        keys_to_delete_view.append(k)
                                except (ValueError, IndexError):
                                    continue

                        for k in keys_to_delete_view:
                            del st.session_state.view_inventory_hierarchy_selection[k]
                        
                        st.session_state.view_inventory_final_selected_activo_id = actual_selected_view_id
                        st.rerun()

                    # Si se selecciona "--- Selecciona Ubicación ---" en cualquier nivel, romper el bucle.
                    if actual_selected_view_id is None:
                        st.session_state.view_inventory_final_selected_activo_id = None
                        break
                    
                    current_parent_id_view_inventory = actual_selected_view_id
                    level_view_inventory += 1
                
                selected_view_location_id = st.session_state.view_inventory_final_selected_activo_id
                if selected_view_location_id:
                    st.info(f"Filtro de ubicación activo: {get_activo_full_path(db, selected_view_location_id)}")
            st.markdown("---")


            items = get_inventory_items(db, 
                                        item_number_filter=item_number_filter if item_number_filter else None, 
                                        location_id_filter=selected_view_location_id)

            if items:
                st.write("Lista de Items en Inventario:")
                
                item_data = []
                for item in items:
                    ubicacion_path = get_activo_full_path(db, item.ubicacion_id) if item.ubicacion_id else "N/A"
                    item_data.append({
                        "ID": item.id,
                        "Número Item": item.numero_item,
                        "Tipo": item.tipo_item,
                        "Número de Serie": item.numero_serie,
                        "Estado": item.estado_funcionamiento,
                        "Ubicación": ubicacion_path,
                        "Fecha de Alta": item.fecha_alta.strftime('%Y-%m-%d %H:%M')
                    })
                
                df_items = pd.DataFrame(item_data)
                
                st.dataframe(df_items, use_container_width=True, hide_index=True)

                st.markdown("---")
                st.subheader("Ver Detalles de Item")
                st.info("Introduce el Número de Serie o Número de Item para ver los detalles completos de un item.")
                detail_search_input = st.text_input("Número de Serie o Número de Item:", key="detail_search_input")
                
                if detail_search_input:
                    item_to_show = get_inventory_item_by_serial_or_number(db, detail_search_input)
                    if item_to_show:
                        st.write(f"**Detalles del Item: {item_to_show.numero_item}**")
                        st.write(f"**Tipo:** {item_to_show.tipo_item}")
                        st.write(f"**Número de Serie:** {item_to_show.numero_serie}")
                        st.write(f"**Descripción Breve:** {item_to_show.descripcion_breve}")
                        st.write(f"**Descripción Detallada:** {item_to_show.descripcion_detallada}")
                        st.write(f"**Estado de Funcionamiento:** {item_to_show.estado_funcionamiento}")
                        st.write(f"**Fecha de Alta:** {item_to_show.fecha_alta.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.write(f"**Cantidad:** {item_to_show.cantidad}")
                        st.write(f"**Precio Estimado (USD):** ${item_to_show.precio_estimado_usd:.2f}")
                        
                        alta_por_user = db.query(Usuario).get(item_to_show.dado_de_alta_por_id)
                        st.write(f"**Dado de alta por:** {alta_por_user.nombre_usuario if alta_por_user else 'N/A'}")
                        
                        ubicacion_item_path = get_activo_full_path(db, item_to_show.ubicacion_id)
                        st.write(f"**Ubicación:** {ubicacion_item_path}")

                        if item_to_show.producto_asociado:
                            st.write(f"**Producto Asociado:** {item_to_show.producto_asociado.nombre}")
                    else:
                        st.warning("Item no encontrado con el Número de Serie o Número de Item proporcionado.")
                else:
                    st.info("Ingresa un número de serie o número de item para ver los detalles de un item.")

            else:
                st.info("No hay ítems registrados en el inventario o no coinciden con los filtros aplicados.")
        finally:
            db.close()

    with tab3:
        st.header("Actualizar Item (En Desarrollo)")
        st.info("La funcionalidad para actualizar ítems se implementará en una futura versión.")
