# Klimat polskich miast

Interaktywny dashboard analityczny w Streamlit porównujący pogodę w 10
największych polskich miastach: temperatury, opady, wiatr, amplitudy dobowe
i sezonowość.

**Działająca aplikacja:** https://TODO.streamlit.app *(link po deploymencie)*

## Co robi aplikacja

- pobiera dzienne dane pogodowe (temperatura min/max/średnia, suma opadów,
  maksymalny wiatr) dla wybranych miast i zakresu dat,
- czyści je i wzbogaca (interpolacja braków, amplituda dobowa, pory roku,
  dni deszczowe),
- pokazuje KPI oraz 7 typów wykresów: liniowy, słupkowy, scatter, histogram,
  boxplot, mapę i heatmapę,
- reaguje na 4 filtry: wybór miast (multiselect), zakres dat (date_input),
  metrykę trendu (selectbox) i okno wygładzania (slider).

## Źródło danych

[Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
— darmowe, bez klucza API. Dane pomiarowe od 2015 roku, aktualizowane z ok.
tygodniowym opóźnieniem. Odpowiedzi są cachowane przez `@st.cache_data`
(24 h), więc aplikacja nie odpytuje API przy każdym przeładowaniu.

## Uruchomienie lokalne

```bash
git clone https://github.com/janrudowski/big_data_projekt.git
cd big_data_projekt
pip install -r requirements.txt
streamlit run app.py
```

## Struktura projektu

```
app.py           # layout, filtry, KPI, zakładki
src/data.py      # pobieranie z API + czyszczenie i kolumny pochodne
src/charts.py    # funkcje budujące wykresy plotly (zwracają go.Figure)
```
