# Genera las gráficas del README a partir del dataset limpio
# Se ejecuta desde la carpeta py/: python generar_figuras.py

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# colores: superficie, textos y series
SUPERFICIE = '#fcfcfb'
TEXTO = '#0b0b0b'
TEXTO_SEC = '#52514e'
GRID = '#e4e3df'
AZUL, NARANJA, AQUA = '#2a78d6', '#eb6834', '#1baf7a'

plt.rcParams.update({
    'figure.facecolor': SUPERFICIE,
    'axes.facecolor': SUPERFICIE,
    'axes.edgecolor': GRID,
    'axes.labelcolor': TEXTO_SEC,
    'axes.titlecolor': TEXTO,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'axes.titlelocation': 'left',
    'xtick.color': TEXTO_SEC,
    'ytick.color': TEXTO_SEC,
    'font.size': 10.5,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

# cargar dataset limpio
df = pd.read_csv('../data/clean/diabetes_risk_clean.csv')
orden_actividad = ['Sedentary', 'Moderate', 'Active']
etiquetas_actividad = ['Sedentario', 'Moderado', 'Activo']
orden_imc = ['Bajo peso', 'Normal', 'Sobrepeso', 'Obesidad']


def pct_high(serie):
    # porcentaje de pacientes con riesgo alto
    return (serie == 'High').mean() * 100


def guardar(fig, nombre):
    fig.savefig(f'../figures/{nombre}', dpi=160, bbox_inches='tight')
    plt.close(fig)
    print('guardada:', nombre)


# 1. riesgo alto por nivel de actividad física
pct_act = df.groupby('physical_activity_level')['diabetes_risk'].apply(pct_high).reindex(orden_actividad)
fig, ax = plt.subplots(figsize=(7, 4))
barras = ax.bar(etiquetas_actividad, pct_act.values, color=AZUL, width=0.55, edgecolor=SUPERFICIE, linewidth=2)
for barra, valor in zip(barras, pct_act.values):
    ax.text(barra.get_x() + barra.get_width() / 2, valor + 0.4, f'{valor:.1f}%', ha='center', va='bottom', color=TEXTO)
ax.set_title('Riesgo alto de diabetes por nivel de actividad física')
ax.set_ylabel('Pacientes con riesgo alto (%)')
ax.set_ylim(0, 25)
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
guardar(fig, '01_riesgo_alto_por_actividad.png')

# 2. riesgo alto por categoría de IMC y actividad física
pct_imc_act = (
    df.groupby(['categoria_imc', 'physical_activity_level'])['diabetes_risk']
    .apply(pct_high).unstack().reindex(index=orden_imc, columns=orden_actividad)
)
fig, ax = plt.subplots(figsize=(8, 4.5))
x = np.arange(len(orden_imc))
ancho = 0.26
for j, (nivel, etiqueta, color) in enumerate(zip(orden_actividad, etiquetas_actividad, [AZUL, NARANJA, AQUA])):
    ax.bar(x + (j - 1) * ancho, pct_imc_act[nivel].values, width=ancho, color=color,
           edgecolor=SUPERFICIE, linewidth=2, label=etiqueta)
ax.set_xticks(x, orden_imc)
ax.set_title('Riesgo alto por categoría de IMC y nivel de actividad física')
ax.set_ylabel('Pacientes con riesgo alto (%)')
ax.set_xlabel('Categoría de IMC (puntos de corte OMS para población asiática)')
ax.yaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
leyenda = ax.legend(title='Actividad física', frameon=False, loc='upper left', labelcolor=TEXTO)
leyenda.get_title().set_color(TEXTO_SEC)
guardar(fig, '02_riesgo_alto_por_imc_y_actividad.png')


# 3. tamaño del efecto de las pruebas t de Welch (d de Cohen)
def d_cohen(a, b):
    return (a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)


def ic_d(a, b, d):
    # intervalo de confianza del 95% aproximado para d
    n1, n2 = len(a), len(b)
    ee = np.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))
    return d - 1.96 * ee, d + 1.96 * ee


comparaciones = []
bmi_riesgo = lambda datos, nivel: datos.loc[datos['diabetes_risk'] == nivel, 'bmi']
comparaciones.append(('IMC: sedentarios contra activos',
                      df.loc[df['physical_activity_level'] == 'Sedentary', 'bmi'],
                      df.loc[df['physical_activity_level'] == 'Active', 'bmi']))
comparaciones.append(('IMC: riesgo alto contra bajo (todos)', bmi_riesgo(df, 'High'), bmi_riesgo(df, 'Low')))
for nivel, etiqueta in zip(orden_actividad, ['sedentarios', 'moderados', 'activos']):
    sub = df[df['physical_activity_level'] == nivel]
    comparaciones.append((f'IMC: riesgo alto contra bajo ({etiqueta})', bmi_riesgo(sub, 'High'), bmi_riesgo(sub, 'Low')))

filas = []
for nombre, a, b in comparaciones:
    d = d_cohen(a, b)
    bajo, alto = ic_d(a, b, d)
    p = stats.ttest_ind(a, b, equal_var=False).pvalue
    filas.append((nombre, d, bajo, alto, p))

fig, ax = plt.subplots(figsize=(8, 4))
y = np.arange(len(filas))[::-1]
for yi, (nombre, d, bajo, alto, p) in zip(y, filas):
    ax.plot([bajo, alto], [yi, yi], color=AZUL, linewidth=2)
    ax.plot(d, yi, 'o', color=AZUL, markersize=8, markeredgecolor=SUPERFICIE, markeredgewidth=2)
    ax.text(alto + 0.04, yi, f'{d:.2f}', va='center', color=TEXTO)
for umbral, texto in [(0.2, 'pequeño'), (0.5, 'mediano'), (0.8, 'grande')]:
    ax.axvline(umbral, color=GRID, linewidth=1, linestyle='--', zorder=0)
    ax.text(umbral, len(filas) - 0.35, texto, ha='center', color=TEXTO_SEC, fontsize=9)
ax.set_yticks(y, [f[0] for f in filas])
ax.set_xlim(0, 1.6)
ax.set_ylim(-0.6, len(filas) - 0.1)
ax.set_xlabel('d de Cohen (prueba t de Welch, IC 95%)')
ax.set_title('Tamaño del efecto de las diferencias de IMC')
guardar(fig, '03_tamano_efecto_pruebas_t.png')

# 4. fuerza de asociación de cada factor con el riesgo (V de Cramér)
def v_cramer(columna, datos):
    tabla = pd.crosstab(datos[columna], datos['diabetes_risk'])
    chi2, p, gl, _ = stats.chi2_contingency(tabla)
    return np.sqrt(chi2 / tabla.values.sum() / (min(tabla.shape) - 1)), p


factores = {
    'Categoría de IMC': ('categoria_imc', df),
    'Grupo de edad': ('grupo_edad', df),
    'Antecedentes familiares': ('family_history_diabetes', df),
    'Actividad física': ('physical_activity_level', df),
    'Tabaquismo': ('smoking_status', df[df['smoking_status'] != 'Sin dato']),
    'Tipo de dieta': ('diet_type', df),
    'Género': ('gender', df),
}
resultados = sorted(((nombre, *v_cramer(col, datos)) for nombre, (col, datos) in factores.items()), key=lambda r: r[1])
fig, ax = plt.subplots(figsize=(7.5, 4))
nombres = [r[0] for r in resultados]
valores = [r[1] for r in resultados]
barras = ax.barh(nombres, valores, color=AZUL, height=0.6, edgecolor=SUPERFICIE, linewidth=2)
for barra, (nombre, v, p) in zip(barras, resultados):
    marca = '' if p < 0.05 else '  (no significativo)'
    ax.text(v + 0.004, barra.get_y() + barra.get_height() / 2, f'{v:.3f}{marca}', va='center', color=TEXTO)
ax.set_xlim(0, max(valores) * 1.45)
ax.set_xlabel('V de Cramér (chi cuadrado contra riesgo de diabetes)')
ax.set_title('Qué tan asociado está cada factor con el riesgo')
ax.xaxis.grid(True, color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
guardar(fig, '04_asociacion_factores_riesgo.png')

# imprimir tablas de apoyo para el README
print(pct_act.round(1))
print(pct_imc_act.round(1))
for f in filas:
    print(f[0], round(f[1], 3), 'p =', f'{f[4]:.2e}')
for r in resultados:
    print(r[0], round(r[1], 3), f'{r[2]:.2e}')
