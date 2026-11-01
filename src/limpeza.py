"""Pipeline de limpeza do Food Delivery Dataset (Kaggle - Gaurav Malik)."""
from __future__ import annotations

import numpy as np
import pandas as pd

RAIO_TERRA_KM = 6371.0

MAPA_COLUNAS = {
    "ID": "id_pedido",
    "Delivery_person_ID": "id_entregador",
    "Delivery_person_Age": "idade_entregador",
    "Delivery_person_Ratings": "nota_entregador",
    "Restaurant_latitude": "rest_lat",
    "Restaurant_longitude": "rest_lon",
    "Delivery_location_latitude": "dest_lat",
    "Delivery_location_longitude": "dest_lon",
    "Order_Date": "data_pedido",
    "Time_Orderd": "hora_pedido",
    "Time_Order_picked": "hora_coleta",
    "Weatherconditions": "clima",
    "Road_traffic_density": "transito",
    "Vehicle_condition": "condicao_veiculo",
    "Type_of_order": "tipo_pedido",
    "Type_of_vehicle": "tipo_veiculo",
    "multiple_deliveries": "entregas_multiplas",
    "Festival": "festival",
    "City": "tipo_cidade",
    "Time_taken(min)": "tempo_entrega_min",
}

TRADUCOES = {
    "clima": {"Sunny": "Ensolarado", "Cloudy": "Nublado", "Windy": "Ventania",
              "Fog": "Neblina", "Stormy": "Tempestade", "Sandstorms": "Tempestade de areia"},
    "transito": {"Low": "Baixo", "Medium": "Médio", "High": "Alto", "Jam": "Congestionado"},
    "tipo_pedido": {"Snack": "Lanche", "Meal": "Refeição", "Drinks": "Bebidas", "Buffet": "Buffet"},
    "tipo_veiculo": {"motorcycle": "Moto", "scooter": "Scooter",
                     "electric_scooter": "Scooter elétrica", "bicycle": "Bicicleta"},
    "festival": {"No": "Não", "Yes": "Sim"},
    "tipo_cidade": {"Metropolitian": "Metropolitana", "Urban": "Urbana", "Semi-Urban": "Semiurbana"},
}

ORDEM_TRANSITO = ["Baixo", "Médio", "Alto", "Congestionado"]


def carregar_bruto(caminho: str) -> pd.DataFrame:
    return pd.read_csv(caminho, dtype=str)


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * RAIO_TERRA_KM * np.arcsin(np.sqrt(a))


def _padronizar_texto(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for c in df.columns:
        df[c] = df[c].str.strip().replace({"NaN": np.nan, "": np.nan})
    return df


def _corrigir_tipos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["tempo_entrega_min"] = df["tempo_entrega_min"].str.extract(r"(\d+)", expand=False).astype(float)
    df["clima"] = df["clima"].str.replace("conditions", "", regex=False).str.strip().replace({"NaN": np.nan})
    for c in ["idade_entregador", "nota_entregador", "rest_lat", "rest_lon", "dest_lat", "dest_lon",
              "condicao_veiculo", "entregas_multiplas"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["data_pedido"] = pd.to_datetime(df["data_pedido"], format="%d-%m-%Y")
    return df


def _montar_horarios(df: pd.DataFrame) -> pd.DataFrame:
    """Cria timestamps de pedido/coleta tratando pedidos que atravessam a meia-noite."""
    df = df.copy()
    pedido = pd.to_timedelta(df["hora_pedido"], errors="coerce")
    coleta = pd.to_timedelta(df["hora_coleta"], errors="coerce")
    df["ts_pedido"] = df["data_pedido"] + pedido
    df["ts_coleta"] = df["data_pedido"] + coleta
    virou_dia = df["ts_coleta"] < df["ts_pedido"]
    df.loc[virou_dia, "ts_coleta"] += pd.Timedelta(days=1)
    df["tempo_preparo_min"] = (df["ts_coleta"] - df["ts_pedido"]).dt.total_seconds() / 60
    df["hora_do_dia"] = df["ts_pedido"].dt.hour.astype("Int64")
    df["dia_semana"] = df["data_pedido"].dt.dayofweek
    return df


def _tratar_coordenadas(df: pd.DataFrame) -> pd.DataFrame:
    """Latitudes negativas são erro de sinal (Índia fica no hemisfério norte);
    coordenadas zeradas ou muito pequenas são inválidas."""
    df = df.copy()
    for c in ["rest_lat", "rest_lon", "dest_lat", "dest_lon"]:
        df[c] = df[c].abs()
    invalida = (df["rest_lat"] < 1) | (df["rest_lon"] < 1)
    df.loc[invalida, ["rest_lat", "rest_lon", "dest_lat", "dest_lon"]] = np.nan
    df["distancia_km"] = haversine_km(df["rest_lat"], df["rest_lon"], df["dest_lat"], df["dest_lon"])
    return df


def _derivar_cidade(df: pd.DataFrame) -> pd.DataFrame:
    """O código da cidade está embutido no ID do entregador (ex.: INDORES13DEL02 -> INDO)."""
    df = df.copy()
    df["cidade"] = df["id_entregador"].str.extract(r"^([A-Z]+)RES", expand=False)
    return df


def _remover_inconsistencias(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    log = {}
    # Registros com nota 6 (escala é 1-5) ou idade 15 (abaixo da idade legal): perfis de teste
    teste = (df["nota_entregador"] > 5) | (df["idade_entregador"] < 18)
    log["perfis_teste_removidos"] = int(teste.sum())
    df = df[~teste].copy()
    return df, log


def _traduzir(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col, mapa in TRADUCOES.items():
        df[col] = df[col].map(mapa)
    df["transito"] = pd.Categorical(df["transito"], categories=ORDEM_TRANSITO, ordered=True)
    return df


def limpar(df_bruto: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = df_bruto.rename(columns=MAPA_COLUNAS)
    df = _padronizar_texto(df)
    df = _corrigir_tipos(df)
    df = _montar_horarios(df)
    df = _tratar_coordenadas(df)
    df = _derivar_cidade(df)
    df, log = _remover_inconsistencias(df)
    df = _traduzir(df)
    df["entregas_multiplas"] = df["entregas_multiplas"].astype("Int64")
    df["condicao_veiculo"] = df["condicao_veiculo"].astype("Int64")
    return df.reset_index(drop=True), log
