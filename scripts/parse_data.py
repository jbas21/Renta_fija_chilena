'''Extraer datos del DB y procesarlos para análisis'''

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import os
import plot_curve

# Ruta a la base de datos (ajusta según tu archivo)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
db_path = os.path.join(BASE_DIR, 'DB', 'fixed_income.db')  # Archivo de base de datos SQLite

def connect_db(query, db_path):
        try:
            conn = sqlite3.connect(db_path)# Conectar a la base de datos
            # Ejecutar consulta y cargar en DataFrame
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df

        except sqlite3.Error as e:
            print(f"Error al conectar a la base de datos: {e}")
        finally:
             conn.close()
         





#ejemplo consulta SQL para obtener datos de rendimiento y duración
'''SELECT *, MAX(date)
FROM fixed_income 
WHERE (ticker LIKE 'BCHIC%' 
   OR ticker LIKE 'UCHI%' 
   OR ticker LIKE 'FUCHI%')
  AND date >= date('now', '-1 month')
GROUP BY ticker;

SELECT*
FROM fixed_income 
WHERE ticker IN ('BCHICA1015', 'BSTD150216','BCHICM1215');

  SELECT 
        f.date, 
        f.ticker,
        b.clasif_riesgo_1, -- Nombre exacto según tu esquema
        b.moneda,
		f.yield_val,
		f.duration
    FROM fixed_income f
    INNER JOIN bonos b ON f.ticker = b.ticker
    WHERE f.date = (SELECT MAX(f2.date) FROM fixed_income f2 WHERE f2.ticker = f.ticker)
        AND f.date >= date('now', '-1 month')
        AND b.clasif_riesgo_1 = 'AAA' 
        AND b.moneda = 'UF'
		AND f.family = 'BB'
    ORDER BY f.date DESC, f.ticker ASC;
'''


# Consulta SQL (ejemplo: obtener rendimientos por duración para una fecha específica)
query = """
SELECT *, MAX(date)
FROM fixed_income 
WHERE (ticker LIKE 'BTU%'
    OR ticker LIKE 'BCU%'
   )
  AND date >= date('now', '-1 month')
GROUP BY ticker;
"""


df = connect_db(query, db_path)

plot_curve.grafico_yield(df)


df = df[df['duration'] != 0]
yield_consulta = df['yield_val'].mean()
print(f'yield promedio: {yield_consulta}')

df_intervalo = df[(df['duration'] >= 3) & (df['duration'] <= 4)]
promedio_yield = df_intervalo['yield_val'].mean()
print(f'yield promedio (3-4 años): {promedio_yield}')

df_simulacion = plot_curve.simulacion_precio(df,-0.02)
print(df_simulacion)



# Llamar a la función curva con los datos procesados
plot_curve.curva(df)
