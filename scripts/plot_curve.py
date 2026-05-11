import os
from matplotlib import ticker
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize
import numpy as np



def curva(df, output_dir=None):
     # Filtrar valores atípicos (ajustar según tus datos)
    data = df[np.abs(df['yield_val'] - df['yield_val'].mean()) <= (df['yield_val'].std())]
    if 'ticker' in data.columns:
        data = data.sort_values(by=['ticker', 'duration'])
        plot_kwargs = {'data': data, 'x': 'duration', 'y': 'yield_val', 'marker': 'o', 'hue': 'ticker'}
    else:
        data = data.sort_values(by='duration')
        plot_kwargs = {'data': data, 'x': 'duration', 'y': 'yield_val', 'marker': 'o'}

    plt.figure(figsize=(12, 6))
    sns.lineplot(**plot_kwargs)

    plt.title('Curva de Precios')
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        fig1_path = os.path.join(output_dir, 'curva_precios.png')
        plt.savefig(fig1_path, dpi=150, bbox_inches='tight')
        print(f'Curva de precios guardada en: {fig1_path}')
    plt.show()

    ## Nelson-Siegel
    def nelson_siegel(t, b0, b1, b2, tau):
        # Evitar división por cero
        if tau <= 0: return np.ones_like(t) * 1e6 
        
        term1 = (1 - np.exp(-t/tau)) / (t/tau)
        term2 = term1 - np.exp(-t/tau)
        
        return b0 + (b1 * term1) + (b2 * term2)

    # Función de error
    def objective(params, t, y):
        return np.sum((nelson_siegel(t, *params) - y)**2)


    # Estimación inicial: [b0, b1, b2, tau]
    init_params = [data['yield_val'].iloc[-1], data['yield_val'].iloc[0]-data['yield_val'].iloc[-1], 0, 1.0]

    # Optimización
    res = minimize(objective, init_params, args=(data['duration'], data['yield_val']))
    b0_opt, b1_opt, b2_opt, tau_opt = res.x

    print(f"Parámetros optimizados: beta0={b0_opt:.4f}, beta1={b1_opt:.4f}, beta2={b2_opt:.4f}, tau={tau_opt:.4f}")

    t_curva = np.linspace(0.1, 30, 100)
    y_ajustada = nelson_siegel(t_curva, b0_opt, b1_opt, b2_opt, tau_opt)

    plt.figure(figsize=(10, 6))
    plt.scatter(data['duration'], data['yield_val'], color='red', label='Tasas de Mercado')
    plt.plot(t_curva, y_ajustada, label='Curva Nelson-Siegel', color='blue')
    plt.title('Ajuste de Curva de Rendimiento (Nelson-Siegel)')
    plt.xlabel('Duracion (años)')
    plt.ylabel('Tasa de Interés (%)')
    plt.legend()
    plt.grid(True)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        fig2_path = os.path.join(output_dir, 'curva_nelson_siegel.png')
        plt.savefig(fig2_path, dpi=150, bbox_inches='tight')
        print(f'Curva Nelson-Siegel guardada en: {fig2_path}')
    plt.show()

    return y_ajustada

def simulacion_precio(df, r=0.01):
    """Calcula el precio simulado para cada fila, soportando múltiples tickers."""
    required_cols = {'duration', 'yield_val', 'convexity'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Faltan columnas requeridas: {missing}")

    data = df.copy()
    data['delta Precio'] = data['yield_val'] - r * data['duration'] + (data['convexity'] *(r**2)) / 2
    return data

def grafico_yield(df, output_dir=None):
    data = df.copy()
    if 'ticker' in data.columns:
        data = data.sort_values(by=['ticker', 'date'])
        plot_kwargs = {'data': data, 'x': 'date', 'y': 'yield_val', 'marker': 'o', 'hue': 'ticker'}
    else:
        data = data.sort_values(by='date')
        plot_kwargs = {'data': data, 'x': 'date', 'y': 'yield_val', 'marker': 'o'}

    plt.figure(figsize=(12, 6))
    sns.lineplot(**plot_kwargs)
    plt.title('Simulación de Yield')
    plt.xlabel('Duración (años)')
    plt.ylabel('Yield (%)')
    plt.grid(True)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'grafico_yield.png')
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f'Gráfico de yield guardado en: {output_file}')
    plt.show()

def boxplot(df, output_dir=None):
    if 'yield_val' not in df.columns:
        raise ValueError("Falta la columna 'yield_val' en el DataFrame")

    data = df.copy()
    data = data.dropna(subset=['yield_val'])

    plt.figure(figsize=(12, 6))
    if 'ticker' in data.columns:
        sns.boxplot(data=data, x='yield_val', y='ticker', orient='h')
        plt.title('Boxplot de yield_val por ticker')
        plt.xlabel('yield_val')
        plt.ylabel('ticker')
    else:
        plt.boxplot(data['yield_val'], vert=False)
        plt.title('Boxplot de yield_val')
        plt.xlabel('yield_val')

    plt.grid(axis='x', linestyle='--', alpha=0.5)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'boxplot_yield_val.png')
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f'Boxplot guardado en: {output_file}')

    plt.show()

def grafico_circular(df, output_dir=None):
    if 'ticker' not in df.columns:
        raise ValueError("Falta la columna 'ticker' en el DataFrame")

    data = df.copy()
    data = data.dropna(subset=['ticker'])
    counts = data['ticker'].value_counts()

    plt.figure(figsize=(8, 8))
    plt.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=140)
    plt.title('Distribución de Tickers')
    plt.axis('equal')

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'grafico_circular_tickers.png')
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f'Gráfico circular guardado en: {output_file}')

    plt.show()

