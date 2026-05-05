from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def cash_flow_bar(df: pd.DataFrame):
    fig = px.bar(df, x="Año", y="Flujo de caja", title="Flujo de caja anual")
    fig.add_hline(y=0, line_dash="dash")
    fig.update_layout(yaxis_title="Monto", xaxis_title="Año", margin=dict(l=20, r=20, t=50, b=20))
    return fig


def cumulative_line(df: pd.DataFrame):
    fig = px.line(df, x="Año", y="Flujo acumulado", markers=True, title="Recuperación acumulada de la inversión")
    fig.add_hline(y=0, line_dash="dash")
    fig.update_layout(yaxis_title="Monto acumulado", xaxis_title="Año", margin=dict(l=20, r=20, t=50, b=20))
    return fig


def cost_composition(statement: pd.DataFrame, year: int = 1):
    if statement.empty:
        return go.Figure()
    row = statement.loc[statement["Año"] == year]
    if row.empty:
        row = statement.head(1)
    row = row.iloc[0]
    values = {
        "Costos de ventas": row.get("Costos de ventas", 0),
        "Gastos administrativos": row.get("Gastos administrativos", 0),
        "Gastos de ventas": row.get("Gastos de ventas", 0),
        "Gastos financieros": row.get("Gastos financieros", 0),
        "Impuestos": row.get("Impuestos", 0),
    }
    data = pd.DataFrame({"Categoría": list(values.keys()), "Monto": list(values.values())})
    fig = px.pie(data, names="Categoría", values="Monto", hole=0.45, title=f"Composición de costos y gastos — Año {int(row['Año'])}")
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig


def sensitivity_heatmap(df: pd.DataFrame):
    if df.empty:
        return go.Figure()
    fig = px.density_heatmap(
        df,
        x="Escenario",
        y="Variable",
        z="TIR",
        text_auto=".1%",
        title="Matriz de sensibilidad: impacto en TIR",
    )
    fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    return fig


def tornado_chart(df: pd.DataFrame):
    if df.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(y=df["Variable"], x=df["VAN bajo"], orientation="h", name="Escenario bajo"))
    fig.add_trace(go.Bar(y=df["Variable"], x=df["VAN alto"], orientation="h", name="Escenario alto"))
    fig.update_layout(title="Gráfico tornado: impacto sobre el VAN", xaxis_title="VAN", yaxis_title="Variable", barmode="overlay", margin=dict(l=20, r=20, t=50, b=20))
    return fig
