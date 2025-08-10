# scripts/load_complex_assets.py

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
        # Verifica si ya existen activos para evitar duplicados en cada ejecución del script
        if db.query(Activo).count() > 0:
            print("Ya existen activos en la base de datos. Saltando la carga de datos de ejemplo para evitar duplicados.")
            return

        print("Iniciando la carga de la taxonomía compleja de activos. Esto puede tomar unos minutos...")
        
        # Diccionarios para guardar IDs de padres y facilitar la creación de hijos
        sectors = {}
        areas = {} # W o H
        ubicaciones_principales = {} # W01-W10, P01-P04
        racks = {}
        contenedores = {}

        # --- NIVEL 1: SH (Sector Principal) ---
        sh_sector = Activo(nombre='HSY', tipo='HIVE SITE YGUAZU', descripcion='Sector principal de operaciones')
        db.add(sh_sector)
        db.flush() 
        sectors['SH'] = sh_sector.id
        print(f"Creado: {sh_sector.nombre}")

        # --- NIVEL 2: W (Tipo Área) y H (Tipo Área) ---
        w_area = Activo(nombre='W', tipo='Áereo', descripcion='Sector Áereos', parent_id=sectors['SH'])
        h_area = Activo(nombre='H', tipo='Hidrocontenedor', descripcion='Sector Hidrocontenedores', parent_id=sectors['SH'])
        db.add_all([w_area, h_area])
        db.flush()
        areas['W'] = w_area.id
        areas['H'] = h_area.id
        print(f"Creado: {w_area.nombre}, {h_area.nombre}")

        # --- NIVEL 3: W01-W10 (Ubicación Principal) y P01-P04 (Ubicación Principal) ---
        # WHs (Warehouses)
        for i in range(1, 11): # 10 WHs
            wh_nombre = f'W{i:02d}'
            wh = Activo(nombre=wh_nombre, tipo='Warehouse', descripcion=f'Warehouse {wh_nombre}', parent_id=areas['W'])
            db.add(wh)
            db.flush()
            ubicaciones_principales[wh_nombre] = wh.id
            print(f"Creado: {wh.nombre}")

            # Racks dentro de cada WH (NIVEL 4)
            for j in range(1, 17): # 16 Racks por WH
                rack_nombre = f'R{j:02d}'
                rack = Activo(nombre=rack_nombre, tipo='Rack', descripcion=f'Rack {rack_nombre} en {wh_nombre}', parent_id=wh.id)
                db.add(rack)
                db.flush()
                racks[f'{wh_nombre}-{rack_nombre}'] = rack.id

                # Mineros dentro de cada Rack (NIVEL 5)
                for k in range(1, 181): # 180 Mineros por Rack
                    minero_nombre = f'M{k:03d}'
                    minero_tag = f'{wh_nombre}-{rack_nombre}-{minero_nombre}'
                    minero = Activo(nombre=minero_tag, tipo='Minero', descripcion=f'Minero {minero_tag}', parent_id=rack.id)
                    db.add(minero)
                print(f"Creados 180 mineros en {wh_nombre}-{rack_nombre}")

        # Plataformas (Hydro)
        plataforma_count = 0
        contenedor_total_count = 0
        contenedores_por_plataforma = [32, 32, 32, 14] # 4 Plataformas

        for i in range(1, 5): # 4 Plataformas
            plataforma_nombre = f'P{i:02d}'
            plataforma = Activo(nombre=plataforma_nombre, tipo='Plataforma', descripcion=f'Plataforma hidrocontenedores {plataforma_nombre}', parent_id=areas['H'])
            db.add(plataforma)
            db.flush()
            ubicaciones_principales[plataforma_nombre] = plataforma.id
            print(f"Creado: {plataforma.nombre}")

            # Contenedores dentro de cada Plataforma (NIVEL 4)
            num_contenedores_current_platform = contenedores_por_plataforma[i-1]
            for j in range(1, num_contenedores_current_platform + 1):
                contenedor_total_count += 1
                contenedor_nombre = f'C{contenedor_total_count:03d}' # Numeración global del 1 al 110
                contenedor = Activo(nombre=contenedor_nombre, tipo='Contenedor', descripcion=f'Contenedor {contenedor_nombre} en {plataforma_nombre}', parent_id=plataforma.id)
                db.add(contenedor)
                db.flush()
                contenedores[f'{plataforma_nombre}-{contenedor_nombre}'] = contenedor.id
                # print(f"Creado: {plataforma_nombre}-{contenedor.nombre}") # Comentado

                # Mineros dentro de cada Contenedor (NIVEL 5)
                for k in range(1, 171): # 170 Mineros por Contenedor
                    minero_nombre = f'M{k:03d}'
                    minero_tag = f'{plataforma_nombre}-{contenedor_nombre}-{minero_nombre}'
                    minero = Activo(nombre=minero_tag, tipo='Minero', descripcion=f'Minero {minero_tag}', parent_id=contenedor.id)
                    db.add(minero)
                print(f"Creados 170 mineros en {plataforma_nombre}-{contenedor_nombre}")

        db.commit()
        print("¡Carga de datos de activos finalizada exitosamente!")

    except Exception as e:
        db.rollback()
        print(f"Error al cargar datos de activos: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    load_assets_data()
