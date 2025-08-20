# scripts/load_complex_assets.py

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Obtener el directorio padre (la raíz del proyecto) y añadirlo al path de Python
# Esto permite importar módulos de la raíz como 'models'
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

from models import Activo # Importa el modelo Activo
from utils.database import Base # Importa Base desde utils.database

# Configuración de la base de datos (asegúrate que sea la misma que en utils/database.py)
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://edilzon:edilzonpass@localhost/streamlit_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def load_assets_data():
    db = SessionLocal()
    try:
        # --- PRECAUCIÓN: Descomenta la siguiente línea solo si quieres borrar TODOS los activos existentes
        # --- cada vez que ejecutes este script y empezar de cero.
        # db.query(Activo).delete() 
        # db.commit()
        # print("Activos existentes eliminados (si los había).")

        # Verifica si ya existen activos para evitar duplicados en cada ejecución del script
        if db.query(Activo).count() > 0:
            print("Ya existen activos en la base de datos. Saltando la carga de datos de ejemplo para evitar duplicados.")
            return

        print("Iniciando la carga de la taxonomía compleja de activos. Esto puede tomar varios minutos...")
        
        # Diccionarios para guardar IDs de padres y facilitar la creación de hijos
        sectors = {}
        areas = {} 
        ubicaciones_principales = {} 
        racks = {}
        contenedores = {}

        # --- FUNCIÓN AUXILIAR PARA CREAR CONTENIDO DE CONTENEDORES ---
        def create_container_content(db_session, parent_id, plataforma_nombre_prefix, contenedor_base_nombre):
            swd_cont_familia = Activo(nombre='SW Distribución', tipo='Familia SW Distribución', parent_id=parent_id)
            db_session.add(swd_cont_familia)
            db_session.flush()
            swd_cont_tag = f'{plataforma_nombre_prefix}-{contenedor_base_nombre}-SD01' # Solo 1 por contenedor
            swd_cont_equipo = Activo(nombre=swd_cont_tag, tipo='Equipo', descripcion=f'Switch de Distribución en {contenedor_base_nombre}', parent_id=swd_cont_familia.id)
            db_session.add(swd_cont_equipo)

            minero_cont_familia = Activo(nombre='Minero', tipo='Familia Minero', parent_id=parent_id)
            db_session.add(minero_cont_familia)
            db_session.flush()
            for k_minero_cont in range(1, 171): # 170 Mineros por Contenedor
                minero_cont_nombre = f'M{k_minero_cont:03d}'
                minero_cont_tag = f'{plataforma_nombre_prefix}-{contenedor_base_nombre}-{minero_cont_nombre}'
                minero_cont_equipo = Activo(nombre=minero_cont_tag, tipo='Equipo', descripcion=f'Minero {minero_cont_tag}', parent_id=minero_cont_familia.id)
                db_session.add(minero_cont_equipo)

        # --- FUNCIÓN AUXILIAR PARA CREAR CONTENIDO DE WAREHOUSE ---
        def create_warehouse_content(db_session, wh_id, wh_base_nombre):
            # Switch de Distribución (4 por Warehouse)
            swd_wh_familia = Activo(nombre='SW Distribución', tipo='Familia SW Distribución', parent_id=wh_id)
            db_session.add(swd_wh_familia)
            db_session.flush()
            for k_swd_wh in range(1, 5): # 4 SWD por WH
                swd_wh_tag = f'{wh_base_nombre}-SD{k_swd_wh:02d}'
                swd_wh_equipo = Activo(nombre=swd_wh_tag, tipo='Equipo', descripcion=f'Switch de Distribución {k_swd_wh} en {wh_base_nombre}', parent_id=swd_wh_familia.id)
                db_session.add(swd_wh_equipo)

            # Racks dentro de cada WH (NIVEL 4)
            for j in range(1, 17): # 16 Racks por WH
                rack_nombre = f'R{j:02d}'
                rack = Activo(nombre=rack_nombre, tipo='Rack', descripcion=f'Rack {rack_nombre} en {wh_base_nombre}', parent_id=wh_id)
                db_session.add(rack)
                db_session.flush()
                
                # --- FAMILIAS DE EQUIPOS DENTRO DEL RACK (NIVEL 5) ---
                # Familia PDU (12 unidades por Rack)
                pdu_familia = Activo(nombre='PDU', tipo='Familia PDU', parent_id=rack.id)
                db_session.add(pdu_familia)
                db_session.flush()
                for k_pdu in range(1, 13): # 12 PDUs por Rack
                    pdu_tag = f'{wh_base_nombre}-{rack_nombre}-P{k_pdu:02d}'
                    pdu_equipo = Activo(nombre=pdu_tag, tipo='Equipo', descripcion=f'PDU {k_pdu} en {rack_nombre}', parent_id=pdu_familia.id)
                    db_session.add(pdu_equipo)

                # Familia SW Acceso (4 por Rack)
                swa_familia = Activo(nombre='SW Acceso', tipo='Familia SW Acceso', parent_id=rack.id)
                db_session.add(swa_familia)
                db_session.flush()
                for k_swa in range(1, 5): # 4 SW Acceso por Rack
                    swa_tag = f'{wh_base_nombre}-{rack_nombre}-SA{k_swa:02d}'
                    swa_equipo = Activo(nombre=swa_tag, tipo='Equipo', descripcion=f'Switch de Acceso {k_swa} en {rack_nombre}', parent_id=swa_familia.id)
                    db_session.add(swa_equipo)

                # Familia Minero (180 por Rack)
                minero_rack_familia = Activo(nombre='Minero', tipo='Familia Minero', parent_id=rack.id)
                db_session.add(minero_rack_familia)
                db_session.flush()
                for k_minero_rack in range(1, 181): # 180 Mineros por Rack
                    minero_rack_tag = f'{wh_base_nombre}-{rack_nombre}-M{k_minero_rack:03d}'
                    minero_rack_equipo = Activo(nombre=minero_rack_tag, tipo='Equipo', descripcion=f'Minero {minero_rack_tag}', parent_id=minero_rack_familia.id)
                    db_session.add(minero_rack_equipo)

        # --- FUNCIÓN AUXILIAR PARA CREAR ESTANTES ---
        def create_shelves_content(db_session, parent_id, facility_name):
            for i in range(1, 11): # 10 Estantes
                shelf_name = f'Estante {i:02d}'
                shelf = Activo(nombre=shelf_name, tipo='Estante', descripcion=f'Estante {i} en {facility_name}', parent_id=parent_id)
                db_session.add(shelf)
                # No flush aquí, se hace al final del bucle de estantes.
                
                # Opcional: Podrías añadir equipos de prueba a los estantes si quieres
                # equipo_ejemplo = Activo(nombre=f'{facility_name}-{shelf_name}-ITEM01', tipo='Equipo', descripcion='Item de prueba', parent_id=shelf.id)
                # db_session.add(equipo_ejemplo)

        # --- FIN FUNCIONES AUXILIARES ---


        # --- SECTORES PRINCIPALES ---
        hsv_sector = Activo(nombre='HSV', tipo='HIVE SITE VALENZUELA', descripcion='HIVE SITE VALENZUELA')
        hsy_sector = Activo(nombre='HSY', tipo='HIVE SITE YGUAZU', descripcion='HIVE SITE YGUAZU')
        
        # Nuevos sectores para InventarioItem
        deposito_sector = Activo(nombre='Depósito', tipo='Centro de Almacenamiento', descripcion='Ubicación principal de depósito de inventario')
        laboratorio_sector = Activo(nombre='Laboratorio', tipo='Centro de Pruebas', descripcion='Ubicación principal de laboratorio de inventario')


        db.add_all([hsv_sector, hsy_sector, deposito_sector, laboratorio_sector])
        db.flush() 
        sectors['HSV'] = hsv_sector.id
        sectors['HSY'] = hsy_sector.id
        sectors['Depósito'] = deposito_sector.id
        sectors['Laboratorio'] = laboratorio_sector.id

        print(f"Creado: {hsv_sector.nombre}, {hsy_sector.nombre}, {deposito_sector.nombre}, {laboratorio_sector.nombre}")


        # --- Contenido para Sector HSV (Solo Contenedores) ---
        h_area_hsv = Activo(nombre='H', tipo='Tipo de Área', descripcion='Área de Hydro/Contenedores HSV', parent_id=sectors['HSV'])
        db.add(h_area_hsv)
        db.flush()
        areas['H_HSV'] = h_area_hsv.id
        print(f"Creado: {h_area_hsv.nombre} para HSV")

        plataforma_hsv = Activo(nombre='P01', tipo='Ubicación Principal', descripcion='Plataforma HSV (Contenedores)', parent_id=areas['H_HSV'])
        db.add(plataforma_hsv)
        db.flush()
        print(f"Creado: {plataforma_hsv.nombre} para HSV")

        contenedor_total_count_hsv = 0
        for i in range(1, 101): # 100 Contenedores
            contenedor_total_count_hsv += 1
            contenedor_nombre = f'C{contenedor_total_count_hsv:03d}'
            contenedor = Activo(nombre=contenedor_nombre, tipo='Contenedor', descripcion=f'Contenedor {contenedor_nombre} en HSV', parent_id=plataforma_hsv.id)
            db.add(contenedor)
            db.flush()
            create_container_content(db, contenedor.id, 'P01-HSV', contenedor_nombre) 
        print(f"Creados 100 contenedores para HSV")


        # --- Contenido para Sector HSY (Contenedores y Warehouses) ---
        w_area_hsy = Activo(nombre='W', tipo='Tipo de Área', descripcion='Área de Warehouses HSY', parent_id=sectors['HSY'])
        h_area_hsy = Activo(nombre='H', tipo='Tipo de Área', descripcion='Área de Hydro/Contenedores HSY', parent_id=sectors['HSY'])
        db.add_all([w_area_hsy, h_area_hsy])
        db.flush()
        areas['W_HSY'] = w_area_hsy.id
        areas['H_HSY'] = h_area_hsy.id
        print(f"Creado: {w_area_hsy.nombre}, {h_area_hsy.nombre} para HSY")

        # Warehouses HSY
        for i in range(1, 11): # 10 WHs
            wh_nombre = f'W{i:02d}'
            wh = Activo(nombre=wh_nombre, tipo='Ubicación Principal', descripcion=f'Warehouse {wh_nombre} HSY', parent_id=areas['W_HSY'])
            db.add(wh)
            db.flush()
            create_warehouse_content(db, wh.id, wh_nombre) 
            print(f"Creado: {wh.nombre} para HSY")

        # Plataformas HSY (Hydro)
        plataforma_total_count_hsy = 0
        contenedores_por_plataforma_hsy = [32, 32, 32, 14]
        for i in range(1, 5): # 4 Plataformas
            plataforma_nombre = f'P{i:02d}'
            plataforma = Activo(nombre=plataforma_nombre, tipo='Ubicación Principal', descripcion=f'Plataforma Hydro {plataforma_nombre} HSY', parent_id=areas['H_HSY'])
            db.add(plataforma)
            db.flush()
            
            num_contenedores_current_platform = contenedores_por_plataforma_hsy[i-1]
            for j in range(1, num_contenedores_current_platform + 1):
                plataforma_total_count_hsy += 1
                contenedor_nombre = f'C{plataforma_total_count_hsy:03d}' # Numeración global
                contenedor = Activo(nombre=contenedor_nombre, tipo='Contenedor', descripcion=f'Contenedor {contenedor_nombre} en {plataforma_nombre} HSY', parent_id=plataforma.id)
                db.add(contenedor)
                db.flush()
                create_container_content(db, contenedor.id, plataforma_nombre, contenedor_nombre) 
            print(f"Creado: {plataforma.nombre} para HSY con {num_contenedores_current_platform} contenedores")
        

        # --- Contenido para Sector Depósito ---
        create_shelves_content(db, sectors['Depósito'], 'Depósito')
        print(f"Creados 10 estantes para Depósito")

        # --- Contenido para Sector Laboratorio ---
        create_shelves_content(db, sectors['Laboratorio'], 'Laboratorio')
        print(f"Creados 10 estantes para Laboratorio")


        db.commit()
        print("¡Carga de datos de activos finalizada exitosamente!")

    except Exception as e:
        db.rollback()
        print(f"Error al cargar datos de activos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_assets_data()
