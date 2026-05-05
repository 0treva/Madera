from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import numpy_financial as npf
import pandas as pd


@dataclass
class ScenarioInputs:
    price_delta: float = 0.0
    volume_delta: float = 0.0
    wood_delta: float = 0.0
    mdf_delta: float = 0.0
    tax_rate: float = 0.40
    discount_rate: float = 0.20
    wood_weight_in_cogs: float = 0.41
    mdf_weight_in_cogs: float = 0.198


def npv(discount_rate: float, cash_flows: Iterable[float]) -> float:
    values = list(cash_flows)
    if not values:
        return 0.0
    initial = values[0]
    future = values[1:]
    return float(initial + sum(cf / ((1 + discount_rate) ** i) for i, cf in enumerate(future, start=1)))


def irr(cash_flows: Iterable[float]) -> float | None:
    values = list(cash_flows)
    if len(values) < 2 or not any(v < 0 for v in values) or not any(v > 0 for v in values):
        return None
    result = npf.irr(values)
    if result is None or isinstance(result, complex) or math.isnan(float(result)):
        return None
    return float(result)


def decision_label(project_npv: float, project_irr: float | None, discount_rate: float, liquidity: float | None = None) -> tuple[str, str]:
    if project_irr is None:
        return "Revisar", "No se pudo calcular una TIR válida con los flujos actuales."
    if project_npv > 0 and project_irr > discount_rate and (liquidity is None or liquidity >= 1):
        return "Aceptar", "El VAN es positivo, la TIR supera la tasa de descuento y la liquidez no muestra alerta crítica."
    if project_npv > 0 and project_irr > discount_rate:
        return "Revisar", "El proyecto genera valor, pero conviene revisar liquidez, capital de trabajo y sensibilidad."
    return "Rechazar o ajustar", "El VAN o la TIR no cumplen el criterio mínimo de aceptación."


def build_scenario_cash_flow(statement: pd.DataFrame, base_cash_flow: pd.DataFrame, inputs: ScenarioInputs) -> pd.DataFrame:
    if statement.empty:
        out = base_cash_flow.copy()
        multiplier = 1 + 0.65 * inputs.price_delta + 0.55 * inputs.volume_delta - 0.15 * inputs.wood_delta - 0.10 * inputs.mdf_delta
        out["Flujo de caja"] = out.apply(
            lambda row: row["Flujo de caja"] if row["Año"] == 0 else row["Flujo de caja"] * multiplier,
            axis=1,
        )
        out["Flujo acumulado"] = out["Flujo de caja"].cumsum()
        return out

    df = statement.copy()
    cogs_material_multiplier = 1 + (inputs.wood_weight_in_cogs * inputs.wood_delta) + (inputs.mdf_weight_in_cogs * inputs.mdf_delta)
    df["Ventas ajustadas"] = df["Ventas"].fillna(0) * (1 + inputs.price_delta) * (1 + inputs.volume_delta)
    df["Costo ventas ajustado"] = df["Costos de ventas"].fillna(0) * (1 + inputs.volume_delta) * cogs_material_multiplier
    df["Gastos administrativos ajustados"] = df["Gastos administrativos"].fillna(0)
    df["Gastos ventas ajustados"] = df["Gastos de ventas"].fillna(0) * (1 + inputs.volume_delta * 0.35)
    df["Depreciación"] = df["Depreciación"].fillna(0)
    df["UAII ajustada"] = (
        df["Ventas ajustadas"]
        - df["Costo ventas ajustado"]
        - df["Gastos administrativos ajustados"]
        - df["Gastos ventas ajustados"]
    )
    df["Utilidad antes impuestos"] = df["UAII ajustada"] - df["Depreciación"]
    df["Impuestos ajustados"] = df["Utilidad antes impuestos"].clip(lower=0) * inputs.tax_rate
    df["Flujo operativo ajustado"] = df["Utilidad antes impuestos"] - df["Impuestos ajustados"] + df["Depreciación"]

    initial_row = base_cash_flow.loc[base_cash_flow["Año"] == 0]
    initial_investment = float(initial_row["Flujo de caja"].iloc[0]) if not initial_row.empty else -7266800.0
    result = pd.DataFrame({
        "Año": [0] + df["Año"].astype(int).tolist(),
        "Flujo de caja": [initial_investment] + df["Flujo operativo ajustado"].astype(float).tolist(),
    })
    result["Flujo acumulado"] = result["Flujo de caja"].cumsum()
    return result


def build_tornado(statement: pd.DataFrame, base_cash_flow: pd.DataFrame, inputs: ScenarioInputs, variation: float = 0.10) -> pd.DataFrame:
    variables = {
        "Precio de venta": "price_delta",
        "Producción": "volume_delta",
        "Madera": "wood_delta",
        "MDF": "mdf_delta",
    }
    rows = []
    base_npv = npv(inputs.discount_rate, base_cash_flow["Flujo de caja"])
    for label, attr in variables.items():
        low_inputs = ScenarioInputs(**inputs.__dict__)
        high_inputs = ScenarioInputs(**inputs.__dict__)
        setattr(low_inputs, attr, -variation)
        setattr(high_inputs, attr, variation)
        low_cf = build_scenario_cash_flow(statement, base_cash_flow, low_inputs)
        high_cf = build_scenario_cash_flow(statement, base_cash_flow, high_inputs)
        low_npv = npv(inputs.discount_rate, low_cf["Flujo de caja"])
        high_npv = npv(inputs.discount_rate, high_cf["Flujo de caja"])
        rows.append({
            "Variable": label,
            "VAN bajo": low_npv,
            "VAN alto": high_npv,
            "Impacto absoluto": max(abs(low_npv - base_npv), abs(high_npv - base_npv)),
        })
    return pd.DataFrame(rows).sort_values("Impacto absoluto", ascending=True)
