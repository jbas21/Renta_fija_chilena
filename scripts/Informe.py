'''Informe mensual de comportamiento de bonos del mercado chileno'''

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
db_path = os.path.join(BASE_DIR, 'DB', 'fixed_income.db')


def connect_db(query):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# ── Datos del último mes con metadata ────────────────────────────────────────
query = """
SELECT
    f.date,
    f.ticker,
    f.quote,
    f.yield_val,
    f.duration,
    f.convexity,
    b.emisor,
    b.clasif_riesgo_1,
    b.moneda,
    b.Sector
FROM fixed_income f
INNER JOIN bonos b ON f.ticker = b.ticker
WHERE f.date >= date('now', '-1 month')
  AND f.yield_val IS NOT NULL AND f.yield_val != 0
  AND f.duration  IS NOT NULL AND f.duration  != 0
  AND f.family NOT LIKE 'LH'
  AND f.family NOT LIKE 'BFT'
  AND f.family NOT LIKE 'PDBC'
  AND f.family NOT LIKE 'BVL'
  AND f.family NOT LIKE 'CERO'
  AND f.family NOT LIKE 'IF'
  
ORDER BY f.date, f.ticker
"""

df = connect_db(query)
df['date'] = pd.to_datetime(df['date'])

fecha_inicio = df['date'].min()
fecha_fin    = df['date'].max()
monedas      = sorted(df['moneda'].dropna().unique())

# ── Cambios inicio → fin por bono ────────────────────────────────────────────
def snapshot(fecha, sufijo):
    return (df[df['date'] == fecha]
            [['ticker', 'yield_val', 'quote', 'duration']]
            .rename(columns={c: f'{c}_{sufijo}' for c in ['yield_val', 'quote', 'duration']}))

cambios = snapshot(fecha_inicio, 'ini').merge(snapshot(fecha_fin, 'fin'), on='ticker')
meta    = df[['ticker', 'emisor', 'clasif_riesgo_1', 'moneda', 'Sector']].drop_duplicates('ticker')
cambios = cambios.merge(meta, on='ticker')
cambios['Δyield_bps']  = (cambios['yield_val_fin'] - cambios['yield_val_ini']) * 100
cambios['Δprecio_pct'] = (cambios['quote_fin'] - cambios['quote_ini']) / cambios['quote_ini'] * 100

fecha_limpia = str(fecha_fin)[:10]
nombre_informe = f'reporte_{fecha_limpia}.xlsx'
path = os.path.join(BASE_DIR, 'outputs', nombre_informe)
cambios.to_excel(path, index=False, sheet_name='Datos')

# ── Consola ───────────────────────────────────────────────────────────────────
sep = "=" * 68
print(sep)
print("          INFORME MENSUAL DE BONOS — MERCADO CHILENO")
print(f"  Período : {fecha_inicio.strftime('%d/%m/%Y')} → {fecha_fin.strftime('%d/%m/%Y')}")
print(f"  Universo: {df['ticker'].nunique()} bonos  |  Monedas: {', '.join(monedas)}")
print(sep)

cols_show = ['ticker', 'emisor', 'clasif_riesgo_1', 'Δyield_bps', 'Δprecio_pct']



for moneda in monedas:
    cm = cambios[cambios['moneda'] == moneda]
    dm = df[df['moneda'] == moneda]
    if cm.empty:
        continue

    print(f"\n{'─'*68}")
    print(f"  MONEDA: {moneda}  ({cm['ticker'].nunique()} bonos)")
    print(f"{'─'*68}")

    y_ini = cm['yield_val_ini'].mean()
    y_fin = cm['yield_val_fin'].mean()
    delta = (y_fin - y_ini) * 100
    print(f"  Yield promedio: {y_ini:.2f}% → {y_fin:.2f}%  "
          f"({'↑' if delta > 0 else '↓'}{abs(delta):.1f} bps)")

    print(f"\n  Por clasificación de riesgo (bps):")
    print(cm.groupby('clasif_riesgo_1')['Δyield_bps']
            .agg(Promedio='mean', Mínimo='min', Máximo='max', N='count')
            .round(1).to_string())

    print(f"\n  Por sector (bps):")
    print(cm.groupby('Sector')['Δyield_bps']
            .agg(Promedio='mean', Mínimo='min', Máximo='max', N='count')
            .round(1).to_string())

    print(f"\n  Top 5 mayor alza de yield:")
    print(cm.nlargest(5, 'Δyield_bps')[cols_show].to_string(index=False))

    print(f"\n  Top 5 mayor baja de yield:")
    print(cm.nsmallest(5, 'Δyield_bps')[cols_show].to_string(index=False))

# ── Gráficos ──────────────────────────────────────────────────────────────────
sns.set_theme(style='whitegrid', palette='tab10')

# Una fila de gráficos por moneda: [evolución yield | scatter duration-yield | cambio por sector]
n_mon = len(monedas)
fig, axes = plt.subplots(n_mon, 3, figsize=(18, 5 * n_mon), squeeze=False)
fig.suptitle(
    f"Informe Mensual de Bonos Chilenos\n"
    f"{fecha_inicio.strftime('%d/%m/%Y')} — {fecha_fin.strftime('%d/%m/%Y')}",
    fontsize=13, fontweight='bold'
)

for row, moneda in enumerate(monedas):
    dm     = df[df['moneda'] == moneda]
    cm     = cambios[cambios['moneda'] == moneda]
    df_fin = dm[dm['date'] == fecha_fin]

    # --- Col 0: Evolución yield por clasificación ---
    ax = axes[row, 0]
    yt = dm.groupby(['date', 'clasif_riesgo_1'])['yield_val'].mean().reset_index()
    for rating, grp in yt.groupby('clasif_riesgo_1'):
        ax.plot(grp['date'], grp['yield_val'], marker='o', markersize=3, label=rating)
    ax.set_title(f'[{moneda}] Yield por Clasificación')
    ax.set_ylabel('Yield (%)')
    ax.legend(fontsize=7)
    ax.tick_params(axis='x', rotation=25)

    # --- Col 1: Duration vs Yield al cierre ---
    ax = axes[row, 1]
    ratings = sorted(df_fin['clasif_riesgo_1'].dropna().unique())
    palette = sns.color_palette('tab10', len(ratings))
    for rating, color in zip(ratings, palette):
        sub = df_fin[df_fin['clasif_riesgo_1'] == rating]
        ax.scatter(sub['duration'], sub['yield_val'], label=rating,
                   alpha=0.65, s=35, color=color)
    ax.set_title(f'[{moneda}] Duration vs Yield ({fecha_fin.strftime("%d/%m/%Y")})')
    ax.set_xlabel('Duration (años)')
    ax.set_ylabel('Yield (%)')
    ax.legend(fontsize=7)

    # --- Col 2: Cambio yield por sector (bps) ---
    ax = axes[row, 2]
    if not cm.empty and 'Sector' in cm.columns:
        cambio_sector = cm.groupby('Sector')['Δyield_bps'].mean().sort_values()
        colors = ['#d62728' if x > 0 else '#2ca02c' for x in cambio_sector]
        cambio_sector.plot(kind='barh', ax=ax, color=colors)
        ax.axvline(0, color='black', linewidth=0.8)
        for bar, val in zip(ax.patches, cambio_sector):
            ax.text(val + (0.3 if val >= 0 else -0.3),
                    bar.get_y() + bar.get_height() / 2,
                    f'{val:+.1f}', va='center',
                    ha='left' if val >= 0 else 'right', fontsize=8)
    ax.set_title(f'[{moneda}] Variación Yield por Sector (bps)')
    ax.set_xlabel('bps')

plt.tight_layout(rect=[0, 0, 1, 0.96])
output_path = os.path.join(BASE_DIR,'outputs','informe_mensual.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight')
plt.show()

print(f"\n{sep}")
print(f"  Gráfico guardado en: {output_path}")
print(sep)
