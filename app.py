"""Klimat polskich miast — dashboard analityczny.

Dane: Open-Meteo Historical Weather API (bez klucza).
Uruchomienie lokalne: streamlit run app.py
"""

from datetime import date, timedelta

import requests
import streamlit as st

from src import charts, data

st.set_page_config(
    page_title="Klimat polskich miast",
    page_icon="🌤️",
    layout="wide",
)

DZIS = date.today()
MAKS_DATA = DZIS - timedelta(days=7)  # archiwum ma kilka dni opóźnienia
DOMYSLNY_START = MAKS_DATA - timedelta(days=365 * 2)

# ---------------------------------------------------------------------------
# Sidebar — filtry
# ---------------------------------------------------------------------------

st.sidebar.title("🌤️ Filtry")

miasta = st.sidebar.multiselect(
    "Miasta",
    options=list(data.MIASTA),
    default=["Warszawa", "Kraków", "Gdańsk", "Wrocław", "Białystok"],
)

zakres = st.sidebar.date_input(
    "Zakres dat",
    value=(DOMYSLNY_START, MAKS_DATA),
    min_value=date(2015, 1, 1),
    max_value=MAKS_DATA,
)

metryka = st.sidebar.selectbox(
    "Metryka na wykresie trendu",
    options=["temp_srednia", "temp_max", "temp_min", "opady_mm", "wiatr_max_kmh"],
    format_func=lambda k: charts.ETYKIETY[k],
)

okno = st.sidebar.slider(
    "Wygładzanie trendu (dni średniej kroczącej)", 1, 60, 14,
    help="1 = surowe dane dzienne, większe wartości pokazują trend sezonowy",
)

st.sidebar.caption(
    "Dane: [Open-Meteo](https://open-meteo.com) — historyczne pomiary dzienne, "
    "odświeżane raz na dobę."
)

if not miasta:
    st.info("⬅️ Wybierz przynajmniej jedno miasto w panelu bocznym.")
    st.stop()

if len(zakres) != 2:
    st.info("⬅️ Wybierz pełny zakres dat (od–do).")
    st.stop()

start, koniec = zakres

# ---------------------------------------------------------------------------
# Pobranie i przygotowanie danych
# ---------------------------------------------------------------------------

try:
    with st.spinner("Pobieram dane z Open-Meteo..."):
        df = data.wyczysc_dane(data.pobierz_dane(miasta, start, koniec))
except (requests.RequestException, ValueError) as blad:
    st.error(f"Nie udało się pobrać danych z API Open-Meteo: {blad}")
    st.stop()

# ---------------------------------------------------------------------------
# Nagłówek i KPI
# ---------------------------------------------------------------------------

st.title("Klimat polskich miast")
st.markdown(
    f"Analiza dziennych danych pogodowych dla **{len(miasta)} miast** "
    f"w okresie **{start:%d.%m.%Y} – {koniec:%d.%m.%Y}** "
    f"({len(df):,} obserwacji).".replace(",", " ")
)

srednie_temp = df.groupby("miasto")["temp_srednia"].mean()
najcieplejsze = srednie_temp.idxmax()
opady_suma = df.groupby("miasto")["opady_mm"].sum()
rekord_wiatru = df.loc[df["wiatr_max_kmh"].idxmax()]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Średnia temperatura", f"{df['temp_srednia'].mean():.1f} °C")
k2.metric("Najcieplejsze miasto", najcieplejsze,
          f"{srednie_temp.max():.1f} °C")
k3.metric("Udział dni deszczowych", f"{df['dzien_deszczowy'].mean():.0%}",
          help="Dni z opadem ≥ 1 mm")
k4.metric("Rekord wiatru", f"{rekord_wiatru['wiatr_max_kmh']:.0f} km/h",
          f"{rekord_wiatru['miasto']}, {rekord_wiatru['data']:%d.%m.%Y}",
          delta_color="off")

# ---------------------------------------------------------------------------
# Zakładki z wykresami
# ---------------------------------------------------------------------------

tab_trendy, tab_rozklady, tab_mapa = st.tabs(
    ["📈 Trendy", "📊 Rozkłady i zależności", "🗺️ Mapa i sezonowość"]
)

with tab_trendy:
    st.plotly_chart(charts.wykres_liniowy(df, metryka, okno), width="stretch")
    st.caption(
        "Wyraźny cykl roczny temperatur jest wspólny dla wszystkich miast — "
        "różnice między nimi są znacznie mniejsze niż zmienność sezonowa. "
        "Zwiększ wygładzanie, żeby porównać miasta bez szumu dziennego."
    )

    st.plotly_chart(charts.wykres_slupkowy_opadow(df), width="stretch")
    st.caption(
        "Suma opadów potrafi różnić się między miastami o kilkadziesiąt procent — "
        "południe kraju (Kraków, Katowice) jest zwykle wyraźnie mokrzejsze od centrum."
    )

with tab_rozklady:
    kol1, kol2 = st.columns(2)
    with kol1:
        st.plotly_chart(charts.histogram_temperatur(df), width="stretch")
        st.caption(
            "Rozkład temperatur jest dwumodalny: osobne zgrupowanie dni zimowych "
            "wokół 0 °C i letnich wokół 18–20 °C."
        )
    with kol2:
        st.plotly_chart(charts.boxplot_amplitudy(df), width="stretch")
        st.caption(
            "Największe wahania dobowe temperatury występują wiosną i latem; "
            "zimą chmury i krótki dzień spłaszczają amplitudę."
        )

    st.plotly_chart(charts.wykres_scatter(df), width="stretch")
    st.caption(
        "Najsilniejsze wiatry przypadają na chłodną część roku (jesień i zima) — "
        "to sezon niżów atlantyckich; upalne dni są zwykle bezwietrzne."
    )

with tab_mapa:
    st.plotly_chart(charts.mapa_miast(df), width="stretch")
    st.caption(
        "Gradient temperatur biegnie z południowego zachodu (najcieplejszy Wrocław) "
        "na północny wschód (najchłodniejszy Białystok)."
    )

    st.plotly_chart(charts.heatmapa_miesieczna(df), width="stretch")
    st.caption(
        "Heatmapa pokazuje sezonowość i jednocześnie stały ranking miast — "
        "kolejność od najcieplejszych do najchłodniejszych utrzymuje się "
        "przez większość miesięcy."
    )

st.divider()
st.caption(
    "Źródło danych: Open-Meteo Historical Weather API · "
    "Kod: [github.com/janrudowski/big_data_projekt]"
    "(https://github.com/janrudowski/big_data_projekt)"
)
