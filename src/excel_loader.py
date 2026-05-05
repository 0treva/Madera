from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

DEFAULT_EXCEL_PATH = Path("data") / "Simulador (marcos de madera personalizados).xlsx"


def normalize_text(value: Any) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value).strip().lower()


def read_sheet(path_or_buffer, sheet_name: str) -> pd.DataFrame:
    return pd.read_excel(path_or_buffer, sheet_name=sheet_name, header=None, engine="openpyxl")


def find_row(df: pd.DataFrame, text: str) -> int | None:
    needle = normalize_text(text)
    for idx, row in df.iterrows():
        joined = " | ".join(normalize_text(v) for v in row.values)
        if needle in joined:
            return int(idx)
    return None


def find_row_first_col(df: pd.DataFrame, text: str, exact: bool = False, require_numeric_after: bool = False) -> int | None:
    needle = normalize_text(text)
    fallback = None
    for idx, value in df.iloc[:, 0].items():
        cell = normalize_text(value)
        matched = cell == needle if exact else needle in cell
        if matched:
            if require_numeric_after:
                nums = numeric_values_after_label(df, int(idx), start_col=1)
                if nums:
                    return int(idx)
                fallback = int(idx)
            else:
                return int(idx)
    return fallback


def numeric_values_after_label(df: pd.DataFrame, row_idx: int, start_col: int = 1) -> list[float]:
    values = []
    for value in df.iloc[row_idx, start_col:].tolist():
        if pd.isna(value):
            continue
        try:
            values.append(float(value))
        except (TypeError, ValueError):
            continue
    return values


def value_near_label(df: pd.DataFrame, label: str, max_scan: int = 6) -> float | None:
    needle = normalize_text(label)
    for r in range(df.shape[0]):
        for c in range(df.shape[1]):
            if needle in normalize_text(df.iat[r, c]):
                for j in range(c + 1, min(c + max_scan + 1, df.shape[1])):
                    value = df.iat[r, j]
                    if pd.notna(value):
                        try:
                            return float(value)
                        except (TypeError, ValueError):
                            pass
    return None


def load_cash_flow(path_or_buffer) -> pd.DataFrame:
    df = read_sheet(path_or_buffer, "FC e Ix")
    row_idx = find_row_first_col(df, "Flujo de caja del proyecto", exact=True, require_numeric_after=True)
    if row_idx is None:
        raise ValueError("No encontré la fila 'Flujo de caja del proyecto' en la hoja FC e Ix.")
    values = numeric_values_after_label(df, row_idx, start_col=1)
    cash_flow = pd.DataFrame({"Año": list(range(len(values))), "Flujo de caja": values})
    cash_flow["Flujo acumulado"] = cash_flow["Flujo de caja"].cumsum()
    return cash_flow


def load_income_statement(path_or_buffer) -> pd.DataFrame:
    df = read_sheet(path_or_buffer, "FC e Ix")
    rows = {
        "Ventas": "Ventas",
        "Costos de ventas": "Costos de ventas",
        "Utilidad bruta": "Utilidad bruta",
        "Gastos administrativos": "Gastos administrativos",
        "Gastos de ventas": "Gastos de ventas",
        "Gastos financieros": "Gastos financieros",
        "Depreciación": "Depreciación de activos",
        "Impuestos": "Impuestos a la utilidad",
        "Utilidad neta": "Utilidad (perdida) neta",
    }
    parsed: dict[str, list[float]] = {}
    for output_name, excel_label in rows.items():
        row_idx = find_row_first_col(df, excel_label)
        if row_idx is not None:
            values = numeric_values_after_label(df, row_idx, start_col=2)
            parsed[output_name] = values
    if not parsed:
        return pd.DataFrame()
    max_len = max(len(v) for v in parsed.values())
    result = pd.DataFrame({"Año": list(range(1, max_len + 1))})
    for name, values in parsed.items():
        padded = values + [np.nan] * (max_len - len(values))
        result[name] = padded
    return result


def load_financial_indicators(path_or_buffer) -> dict[str, float | None]:
    fc = read_sheet(path_or_buffer, "FC e Ix")
    rf = read_sheet(path_or_buffer, "RF")
    indicators = {
        "VAN": value_near_label(fc, "Valor Actual Neto"),
        "TIR": value_near_label(fc, "Tasa Interna de Retorno"),
        "Tasa de descuento": value_near_label(fc, "Tasa de Descuento"),
        "Tasa impositiva": value_near_label(fc, "Tasa impositiva"),
    }
    year_row = 2
    latest_col = None
    for c in range(2, rf.shape[1]):
        if pd.notna(rf.iat[year_row, c]):
            latest_col = c
    def ratio(label: str) -> float | None:
        row = find_row(rf, label)
        if row is None or latest_col is None:
            return None
        try:
            return float(rf.iat[row, latest_col])
        except (TypeError, ValueError):
            return None
    indicators.update({
        "Liquidez inmediata": ratio("liquidez inmediata"),
        "Margen neto": ratio("Margen de utilidad neta"),
        "ROA": ratio("Rendimiento sobre los activos totales"),
        "ROE": ratio("Rendimiento sobre el capital contable"),
        "Razón circulante": ratio("Razón circulante"),
        "Rotación activos totales": ratio("Rotación de activos totales"),
    })
    return indicators


def load_sensitivity(path_or_buffer) -> pd.DataFrame:
    df = read_sheet(path_or_buffer, "Sens")
    rows = []
    for r in range(df.shape[0] - 3):
        variable = df.iat[r, 1] if df.shape[1] > 1 else None
        marker = df.iat[r, 2] if df.shape[1] > 2 else None
        if pd.notna(variable) and "variación" in normalize_text(marker):
            for c in [2, 3, 4]:
                scenario = df.iat[r + 1, c]
                factor = df.iat[r + 2, c]
                tir_value = df.iat[r + 3, c]
                if pd.notna(scenario) and pd.notna(factor) and pd.notna(tir_value):
                    rows.append({
                        "Variable": str(variable).strip(),
                        "Escenario": str(scenario).strip(),
                        "Factor": float(factor),
                        "Cambio (%)": (float(factor) - 1) * 100,
                        "TIR": float(tir_value),
                    })
    return pd.DataFrame(rows)


def load_project_data(path_or_buffer=DEFAULT_EXCEL_PATH) -> dict[str, Any]:
    return {
        "cash_flow": load_cash_flow(path_or_buffer),
        "statement": load_income_statement(path_or_buffer),
        "indicators": load_financial_indicators(path_or_buffer),
        "sensitivity": load_sensitivity(path_or_buffer),
    }
