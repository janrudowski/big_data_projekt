"""Pobieranie i przygotowanie danych pogodowych z API Open-Meteo."""

from datetime import date

import pandas as pd
import requests
import streamlit as st

API_URL = "https://archive-api.open-meteo.com/v1/archive"

# Współrzędne największych polskich miast
MIASTA = {
    "Warszawa": (52.2297, 21.0122),
    "Kraków": (50.0647, 19.9450),
    "Wrocław": (51.1079, 17.0385),
    "Poznań": (52.4064, 16.9252),
    "Gdańsk": (54.3520, 18.6466),
    "Łódź": (51.7592, 19.4560),
    "Katowice": (50.2649, 19.0238),
    "Lublin": (51.2465, 22.5684),
    "Białystok": (53.1325, 23.1688),
    "Szczecin": (53.4285, 14.5528),
}

ZMIENNE_DZIENNE = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
]

NAZWY_KOLUMN = {
    "time": "data",
    "temperature_2m_mean": "temp_srednia",
    "temperature_2m_max": "temp_max",
    "temperature_2m_min": "temp_min",
    "precipitation_sum": "opady_mm",
    "wind_speed_10m_max": "wiatr_max_kmh",
}

PORY_ROKU = {
    12: "zima", 1: "zima", 2: "zima",
    3: "wiosna", 4: "wiosna", 5: "wiosna",
    6: "lato", 7: "lato", 8: "lato",
    9: "jesień", 10: "jesień", 11: "jesień",
}


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def pobierz_miasto(miasto: str, start: date, koniec: date) -> pd.DataFrame:
    """Pobiera dzienne dane pogodowe dla jednego miasta z API Open-Meteo."""
    lat, lon = MIASTA[miasto]
    odpowiedz = requests.get(
        API_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "start_date": start.isoformat(),
            "end_date": koniec.isoformat(),
            "daily": ",".join(ZMIENNE_DZIENNE),
            "timezone": "Europe/Warsaw",
        },
        timeout=30,
    )
    odpowiedz.raise_for_status()
    dane = odpowiedz.json()

    if "daily" not in dane:
        raise ValueError(f"Brak danych dziennych w odpowiedzi API dla miasta {miasto}")

    df = pd.DataFrame(dane["daily"]).rename(columns=NAZWY_KOLUMN)
    df["miasto"] = miasto
    df["latitude"] = lat
    df["longitude"] = lon
    return df


def pobierz_dane(miasta: list[str], start: date, koniec: date) -> pd.DataFrame:
    """Pobiera i łączy dane dla wybranych miast."""
    czesci = [pobierz_miasto(m, start, koniec) for m in miasta]
    return pd.concat(czesci, ignore_index=True)


def wyczysc_dane(df: pd.DataFrame) -> pd.DataFrame:
    """Czyszczenie i przygotowanie danych.

    - konwersja typów (data -> datetime),
    - uzupełnienie braków interpolacją w obrębie miasta,
    - usunięcie wierszy, których nie dało się uzupełnić,
    - kolumny pochodne: amplituda, rok, miesiąc, pora roku, dzień deszczowy.
    """
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])

    kolumny_liczbowe = ["temp_srednia", "temp_max", "temp_min", "opady_mm", "wiatr_max_kmh"]
    df[kolumny_liczbowe] = df[kolumny_liczbowe].astype(float)

    # Braki (np. najświeższe dni bez pomiarów) interpolujemy per miasto,
    # a to czego nie da się uzupełnić — odrzucamy.
    df = df.sort_values(["miasto", "data"])
    df[kolumny_liczbowe] = df.groupby("miasto")[kolumny_liczbowe].transform(
        lambda s: s.interpolate(limit=3)
    )
    df = df.dropna(subset=kolumny_liczbowe).reset_index(drop=True)

    # Kolumny pochodne
    df["amplituda_c"] = (df["temp_max"] - df["temp_min"]).round(1)
    df["rok"] = df["data"].dt.year
    df["miesiac"] = df["data"].dt.strftime("%Y-%m")
    df["nr_miesiaca"] = df["data"].dt.month
    df["pora_roku"] = df["nr_miesiaca"].map(PORY_ROKU)
    df["dzien_deszczowy"] = df["opady_mm"] >= 1.0

    return df
