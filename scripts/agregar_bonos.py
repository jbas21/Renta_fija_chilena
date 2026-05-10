import sqlite3
import pandas as pd
import os
import time

# https://www.cmfchile.cl/institucional/estadisticas/valores_clasificaciones_asignadas.php
def agregar_bonos():
        # Función para limpiar valores numéricos
        def clean_numeric(value):
            if isinstance(value, str):
                value = value.replace(',', '.').replace('%', '')
            try:
                return float(value)
            except ValueError:
                return value

        # Rutas
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        BASE_DIR = os.path.dirname(SCRIPT_DIR)
        db_path = os.path.join(BASE_DIR, 'DB', 'fixed_income.db')
        excel_path = os.path.join(BASE_DIR, 'Bonos', 'Bonos.xlsx')

        # Conectar a la base de datos
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Crear tabla 'bonos' si no existe
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bonos (
            ticker TEXT,
            isin TEXT,
            emisor TEXT,
            tipo_instrumento TEXT,
            fuente_emisor TEXT,
            clasif_riesgo_1 TEXT,
            moneda TEXT,
            Sector TEXT,           
            family TEXT,
            group_col TEXT,
            UNIQUE(ticker)
        )
        ''')

        # Leer el Excel
        df_bonos = pd.read_excel(excel_path)

        # Insertar datos
        for _, row in df_bonos.iterrows():
            cursor.execute('''
            INSERT OR IGNORE INTO bonos (ticker, isin, emisor, tipo_instrumento, fuente_emisor, clasif_riesgo_1, moneda, Sector, family, group_col)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                row['Ticker'],
                row['ISIN'],
                row['Emisor'],
                row['Tipo_Instrumento'],
                row['Fuente_Emisor'],
                row['Clasif_Riesgo_1'],
                row['Moneda'],
                row['Sector'],
                row['Family'],
                row['Group']
            ))

        conn.commit()
        conn.close()

        print("Tabla 'bonos' agregada exitosamente a fixed_income.db.")

