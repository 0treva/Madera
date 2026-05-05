# Dashboard Ejecutivo de Inversión

Prototipo web en Python para visualizar y analizar el simulador de inversión de la asignatura Economía Financiera.

## 1. Qué incluye

- Lectura automática del Excel del simulador.
- KPIs: VAN, TIR, inversión inicial, liquidez inmediata y margen neto.
- Gráfico de flujo de caja anual.
- Gráfico de recuperación acumulada de la inversión.
- Composición de costos y gastos.
- Matriz de sensibilidad por TIR.
- Gráfico tornado para medir impacto sobre VAN.
- Escenarios base, optimista, pesimista y personalizado.

## 2. Estructura

```text
simulador_inversion_dashboard/
├── app.py
├── requirements.txt
├── schema.sql
├── README.md
├── data/
│   └── Simulador (marcos de madera personalizados).xlsx
└── src/
    ├── excel_loader.py
    ├── financial_model.py
    └── visualization.py
```

## 3. Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

En Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 4. Ejecución

```bash
streamlit run app.py
```

El navegador abrirá normalmente:

```text
http://localhost:8501
```

## 5. Flujo recomendado de desarrollo

1. Validar que el Excel se carga correctamente.
2. Confirmar que los KPIs coinciden con el modelo original.
3. Ajustar los pesos de sensibilidad para madera y MDF según la estructura real de costos.
4. Agregar formularios de captura si se desea reemplazar el Excel.
5. Migrar a PostgreSQL usando `schema.sql` si se desea guardar proyectos y escenarios.

## 6. Notas financieras

El VAN se calcula con la inversión inicial en Año 0 y los flujos futuros descontados. La TIR se calcula con la serie completa de flujos. Los escenarios personalizados recalculan el flujo operativo aproximando el efecto de precio, producción, madera y MDF sobre ventas y costos.
