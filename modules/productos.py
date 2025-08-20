# modules/productos.py

import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from utils.database import get_db
from models import Producto # Importamos el modelo Producto

def show_productos_page():
    st.title("🏷️ Gestión de Productos")

    tab1, tab2 = st.tabs(["Dar de alta Producto", "Ver Productos"])

    with tab1:
        st.header("Dar de alta Nuevo Producto")

        db: Session = next(get_db())
        try:
            nombre = st.text_input("Nombre del Producto", help="Nombre único del tipo de producto (ej: 'Minero Antminer S19 Pro', 'Cooler 120mm').")
            descripcion = st.text_area("Descripción del Producto", help="Descripción detallada del tipo de producto.")
            precio_unitario = st.number_input("Precio Unitario (USD)", min_value=0.0, value=0.0, step=0.01, format="%.2f", help="Precio estándar por unidad de este producto.")

            if st.button("Guardar Producto"):
                if not nombre or not descripcion:
                    st.error("Por favor, completa todos los campos obligatorios (Nombre y Descripción).")
                elif precio_unitario is None: # Manejar el caso de que el number_input sea None
                    st.error("Por favor, introduce un precio unitario válido.")
                else:
                    try:
                        # Verificar si el producto ya existe
                        existing_product = db.query(Producto).filter(Producto.nombre == nombre).first()
                        if existing_product:
                            st.warning(f"El producto con nombre '{nombre}' ya existe. No se ha guardado.")
                        else:
                            new_product = Producto(
                                nombre=nombre,
                                descripcion=descripcion,
                                precio_unitario=precio_unitario
                            )
                            db.add(new_product)
                            db.commit()
                            st.success(f"Producto '{new_product.nombre}' dado de alta exitosamente!")
                            st.rerun() # Recargar la página para limpiar el formulario
                    except Exception as e:
                        st.error(f"Error al dar de alta el producto: {e}")
        except Exception as e:
            st.error(f"Error al cargar la página de alta de productos: {e}")
        finally:
            db.close()

    with tab2:
        st.header("Productos Existentes")
        db: Session = next(get_db())
        try:
            productos = db.query(Producto).order_by(Producto.nombre).all()
            if productos:
                st.write("Lista de Productos Registrados:")
                product_data = []
                for prod in productos:
                    product_data.append({
                        "ID": prod.id,
                        "Nombre": prod.nombre,
                        "Descripción": prod.descripcion,
                        "Precio Unitario (USD)": f"${prod.precio_unitario:.2f}"
                    })
                
                df_products = pd.DataFrame(product_data)
                st.dataframe(df_products, use_container_width=True, hide_index=True)
            else:
                st.info("No hay productos registrados. Por favor, da de alta algunos productos en la pestaña 'Dar de alta Producto'.")
        except Exception as e:
            st.error(f"Error al cargar la lista de productos: {e}")
        finally:
            db.close()