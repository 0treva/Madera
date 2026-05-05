from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st

from src.excel_loader import DEFAULT_EXCEL_PATH, load_project_data
from src.financial_model import ScenarioInputs, build_scenario_cash_flow, build_tornado, decision_label, irr, npv
from src.visualization import cash_flow_bar, cost_composition, cumulative_line, sensitivity_heatmap, tornado_chart

st.set_page_config(page_title="Dashboard Ejecutivo de Inversión", layout="wide")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    [data-testid="stMetricValue"] {font-size: 1.6rem;}
    .decision-box {padding: 1rem; border-radius: 0.8rem; background: #f6f8fa; border: 1px solid #e5e7eb;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Dashboard Ejecutivo del Proyecto de Inversión")
st.caption("Simulador de inversión: marcos de madera personalizados")

uploaded_file = st.sidebar.file_uploader("Cargar archivo Excel del simulador", type=["xlsx"])
source = BytesIO(uploaded_file.read()) if uploaded_file else DEFAULT_EXCEL_PATH

try:
    data = load_project_data(source)
except Exception as exc:
    st.error(f"No se pudo leer el archivo: {exc}")
    st.stop()

cash_flow_base = data["cash_flow"]
statement = data["statement"]
indicators = data["indicators"]
sensitivity = data["sensitivity"]

base_discount = indicators.get("Tasa de descuento") or 0.20
base_tax = indicators.get("Tasa impositiva") or 0.40

st.sidebar.header("Escenario")
scenario_name = st.sidebar.selectbox("Selecciona un escenario", ["Base", "Optimista", "Pesimista", "Personalizado"])

preset = {
    "Base": dict(price_delta=0.0, volume_delta=0.0, wood_delta=0.0, mdf_delta=0.0),
    "Optimista": dict(price_delta=0.08, volume_delta=0.08, wood_delta=-0.05, mdf_delta=-0.05),
    "Pesimista": dict(price_delta=-0.08, volume_delta=-0.08, wood_delta=0.08, mdf_delta=0.08),
    "Personalizado": dict(price_delta=0.0, volume_delta=0.0, wood_delta=0.0, mdf_delta=0.0),
}[scenario_name]

if scenario_name == "Personalizado":
    price_delta = st.sidebar.slider("Cambio en precio de venta", -0.25, 0.25, 0.0, 0.01)
    volume_delta = st.sidebar.slider("Cambio en producción", -0.25, 0.25, 0.0, 0.01)
    wood_delta = st.sidebar.slider("Cambio en costo de madera", -0.25, 0.25, 0.0, 0.01)
    mdf_delta = st.sidebar.slider("Cambio en costo de MDF", -0.25, 0.25, 0.0, 0.01)
else:
    price_delta = preset["price_delta"]
    volume_delta = preset["volume_delta"]
    wood_delta = preset["wood_delta"]
    mdf_delta = preset["mdf_delta"]
    st.sidebar.info("Usa 'Personalizado' para mover los supuestos manualmente.")

discount_rate = st.sidebar.number_input("Tasa de descuento", min_value=0.0, max_value=1.0, value=float(base_discount), step=0.01, format="%.2f")
tax_rate = st.sidebar.number_input("Tasa impositiva", min_value=0.0, max_value=1.0, value=float(base_tax), step=0.01, format="%.2f")

scenario_inputs = ScenarioInputs(
    price_delta=price_delta,
    volume_delta=volume_delta,
    wood_delta=wood_delta,
    mdf_delta=mdf_delta,
    tax_rate=tax_rate,
    discount_rate=discount_rate,
)

cash_flow = build_scenario_cash_flow(statement, cash_flow_base, scenario_inputs)
project_npv = npv(discount_rate, cash_flow["Flujo de caja"])
project_irr = irr(cash_flow["Flujo de caja"])
liquidity = indicators.get("Liquidez inmediata")
margin = indicators.get("Margen neto")
initial_investment = abs(float(cash_flow.loc[cash_flow["Año"] == 0, "Flujo de caja"].iloc[0]))
decision, decision_reason = decision_label(project_npv, project_irr, discount_rate, liquidity)

st.subheader("1. Indicadores ejecutivos")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("VAN", f"${project_npv:,.2f}")
col2.metric("TIR", "No válida" if project_irr is None else f"{project_irr:.2%}")
col3.metric("Inversión inicial", f"${initial_investment:,.2f}")
col4.metric("Liquidez inmediata", "N/D" if liquidity is None else f"{liquidity:.2f}x")
col5.metric("Margen neto", "N/D" if margin is None else f"{margin:.2%}")

st.markdown(f"""
<div class="decision-box">
<b>Decisión recomendada:</b> {decision}<br>
{decision_reason}<br>
<b>Escenario activo:</b> {scenario_name}. Precio: {price_delta:+.0%}, producción: {volume_delta:+.0%}, madera: {wood_delta:+.0%}, MDF: {mdf_delta:+.0%}.
</div>
""", unsafe_allow_html=True)

st.divider()
st.subheader("2. Flujo de caja y recuperación")
left, right = st.columns(2)
with left:
    st.plotly_chart(cash_flow_bar(cash_flow), use_container_width=True)
with right:
    st.plotly_chart(cumulative_line(cash_flow), use_container_width=True)

st.divider()
st.subheader("3. Costos y razones financieras")
left, right = st.columns([1.1, 0.9])
with left:
    selected_year = st.selectbox("Año para composición de costos", statement["Año"].astype(int).tolist() if not statement.empty else [1])
    st.plotly_chart(cost_composition(statement, int(selected_year)), use_container_width=True)
with right:
    ratios = pd.DataFrame([
        {"Razón": "Razón circulante", "Valor": indicators.get("Razón circulante")},
        {"Razón": "Liquidez inmediata", "Valor": indicators.get("Liquidez inmediata")},
        {"Razón": "Margen neto", "Valor": indicators.get("Margen neto")},
        {"Razón": "ROA", "Valor": indicators.get("ROA")},
        {"Razón": "ROE", "Valor": indicators.get("ROE")},
        {"Razón": "Rotación activos totales", "Valor": indicators.get("Rotación activos totales")},
    ]).dropna()
    st.dataframe(ratios, use_container_width=True, hide_index=True)

st.divider()
st.subheader("4. Sensibilidad")
left, right = st.columns(2)
with left:
    st.plotly_chart(sensitivity_heatmap(sensitivity), use_container_width=True)
with right:
    tornado = build_tornado(statement, cash_flow_base, scenario_inputs)
    st.plotly_chart(tornado_chart(tornado), use_container_width=True)

with st.expander("Ver datos de flujo de caja"):
    st.dataframe(cash_flow, use_container_width=True, hide_index=True)

st.divider()
st.subheader("5. Conclusión ejecutiva")
st.write(
    f"""
    Bajo el escenario **{scenario_name}**, el proyecto presenta un VAN de **${project_npv:,.2f}** y una TIR de
    **{'no válida' if project_irr is None else f'{project_irr:.2%}'}** frente a una tasa de descuento de **{discount_rate:.2%}**.
    La lectura ejecutiva es: **{decision}**. El análisis de sensibilidad permite observar cómo los cambios en precio,
    producción, madera y MDF modifican la rentabilidad del proyecto.
    """
)
