"""Wykresy plotly dla dashboardu pogodowego. Każda funkcja zwraca go.Figure."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

ETYKIETY = {
    "temp_srednia": "Temperatura średnia [°C]",
    "temp_max": "Temperatura maksymalna [°C]",
    "temp_min": "Temperatura minimalna [°C]",
    "opady_mm": "Opady [mm]",
    "wiatr_max_kmh": "Maks. wiatr [km/h]",
    "amplituda_c": "Amplituda dobowa [°C]",
    "miasto": "Miasto",
    "data": "Data",
    "pora_roku": "Pora roku",
    "miesiac": "Miesiąc",
}

KOLEJNOSC_POR = ["wiosna", "lato", "jesień", "zima"]


def wykres_liniowy(df: pd.DataFrame, metryka: str, okno: int) -> go.Figure:
    """Szereg czasowy wybranej metryki, wygładzony średnią kroczącą."""
    dane = df.sort_values("data").copy()
    dane["wartosc"] = dane.groupby("miasto")[metryka].transform(
        lambda s: s.rolling(okno, min_periods=1).mean()
    )
    tytul = ETYKIETY[metryka]
    fig = px.line(
        dane, x="data", y="wartosc", color="miasto",
        title=f"{tytul} — średnia krocząca {okno} dni",
        labels={"wartosc": tytul, **ETYKIETY},
    )
    return fig


def wykres_slupkowy_opadow(df: pd.DataFrame) -> go.Figure:
    """Suma opadów wg miasta, malejąco."""
    opady = (df.groupby("miasto", as_index=False)["opady_mm"].sum()
               .sort_values("opady_mm", ascending=False))
    fig = px.bar(
        opady, x="miasto", y="opady_mm",
        title="Łączna suma opadów w wybranym okresie",
        labels={"opady_mm": "Suma opadów [mm]", "miasto": "Miasto"},
    )
    return fig


def wykres_scatter(df: pd.DataFrame) -> go.Figure:
    """Zależność temperatury i wiatru, kolor wg pory roku."""
    fig = px.scatter(
        df, x="temp_srednia", y="wiatr_max_kmh",
        color="pora_roku", category_orders={"pora_roku": KOLEJNOSC_POR},
        hover_data=["miasto", "data"], opacity=0.5,
        title="Temperatura a maksymalny wiatr dobowy",
        labels=ETYKIETY,
    )
    return fig


def histogram_temperatur(df: pd.DataFrame) -> go.Figure:
    """Rozkład średnich temperatur dobowych."""
    fig = px.histogram(
        df, x="temp_srednia", color="miasto", nbins=60, barmode="overlay",
        title="Rozkład średnich temperatur dobowych",
        labels=ETYKIETY,
    )
    fig.update_layout(yaxis_title="Liczba dni")
    fig.update_traces(opacity=0.6)
    return fig


def boxplot_amplitudy(df: pd.DataFrame) -> go.Figure:
    """Amplituda dobowa temperatury wg pory roku."""
    fig = px.box(
        df, x="pora_roku", y="amplituda_c", color="pora_roku",
        category_orders={"pora_roku": KOLEJNOSC_POR},
        title="Amplituda dobowa temperatury wg pory roku",
        labels=ETYKIETY,
    )
    fig.update_layout(showlegend=False)
    return fig


def mapa_miast(df: pd.DataFrame) -> go.Figure:
    """Mapa miast: kolor — średnia temperatura, rozmiar — suma opadów."""
    miasta = (df.groupby("miasto", as_index=False)
                .agg(latitude=("latitude", "first"),
                     longitude=("longitude", "first"),
                     srednia_temp=("temp_srednia", "mean"),
                     suma_opadow=("opady_mm", "sum"),
                     maks_wiatr=("wiatr_max_kmh", "max"))
                .round(1))
    fig = px.scatter_map(
        miasta, lat="latitude", lon="longitude",
        color="srednia_temp", size="suma_opadow",
        hover_name="miasto",
        hover_data={"srednia_temp": True, "suma_opadow": True,
                    "maks_wiatr": True, "latitude": False, "longitude": False},
        color_continuous_scale="RdYlBu_r",
        zoom=5, height=600,
        title="Klimat miast: kolor — średnia temperatura, rozmiar — suma opadów",
        labels={"srednia_temp": "Śr. temperatura [°C]",
                "suma_opadow": "Suma opadów [mm]",
                "maks_wiatr": "Maks. wiatr [km/h]"},
    )
    return fig


def heatmapa_miesieczna(df: pd.DataFrame) -> go.Figure:
    """Heatmapa: średnia temperatura miasto x miesiąc."""
    tabela = (df.pivot_table(index="miasto", columns="miesiac",
                             values="temp_srednia", aggfunc="mean")
                .round(1))
    fig = px.imshow(
        tabela, aspect="auto", color_continuous_scale="RdYlBu_r",
        title="Średnia temperatura miesięczna [°C]",
        labels={"x": "Miesiąc", "y": "Miasto", "color": "Temp. [°C]"},
    )
    return fig
