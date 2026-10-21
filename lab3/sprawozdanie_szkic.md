# Lab 3 – Dane interferometryczne SAR: NMT Tatr z pary Sentinel-1

> Szkic. Fragmenty `[UZUPEŁNIJ: …]` wymagają wyników z SNAP/analizy.
> Wartości oznaczone „szac.” policzone z metadanych ASF przed pobraniem danych – zweryfikuj w Stack Overview.

## Dane

| | Master | Slave |
|---|---|---|
| Scena | `S1A_IW_SLC__1SDV_20160811T045259_…_24E3` | `S1A_IW_SLC__1SDV_20160823T045313_…_AB6B` |
| Data | 11.08.2016, 04:53 UTC | 23.08.2016, 04:53 UTC |
| Orbita abs. / względna | 12548 / 51 (descending) | 12723 / 51 (descending) |
| Subswath / burst (TOPSAR-Split) | IW1 / burst 6 | IW1 / burst 1 |
| Polaryzacja | VV | VV |

- Baseline czasowy: 12 dni. Baseline prostopadły: ok. 72 m (szac., ASF) → `[UZUPEŁNIJ: wartość ze Stack Overview]`.
- Ten sam burst terenowy `051_108178_IW1` (Rysy, Gerlach, Łomnica, Tatry Bielskie). Zachodnia część Tatr (Kasprowy, Giewont) leży już w IW2.
- Wysokość niejednoznaczności (zmiana wysokości odpowiadająca jednemu prążkowi 2π):
  h_a = λ·R·sin θ / (2·B⊥) ≈ 0.0555 m · 850 km · sin 34° / (2 · 72 m) ≈ **180 m** (szac.)
  → przy deniwelacji ~1800 m (Podhale ~700 m – Gerlach 2655 m) ok. 10 prążków na interferogramie.

## 1. Stack Overview – wybór master/slave
`[UZUPEŁNIJ: zrzut tabeli Stack Overview]`
Master wybrano jako scenę z 11.08.2016 (wcześniejsza; przy dwóch scenach Stack Overview wskazuje „optimal master” minimalizujący sumę baseline’ów – przy parze jest to wybór praktycznie symetryczny). Mały B⊥ i krótki baseline czasowy dają wysoką modelowaną koherencję, a jednocześnie B⊥ jest wystarczająco duży, by faza była czuła na topografię.

## 2. Interferogram – faza `Phase_ifg_…` (1 pkt)
`[UZUPEŁNIJ: zrzut fazy]`
- Faza interferometryczna to różnica faz master·conj(slave), zwinięta do przedziału (−π, π].
- Po usunięciu fazy płaskiej ziemi (flat-earth) pozostała faza jest głównie topograficzna: widać **prążki (fringes)** układające się jak poziomice wokół masywu Tatr; każdy pełny cykl kolorów ≈ h_a ≈ 180 m różnicy wysokości. Najgęstsze prążki – strome stoki, najrzadsze – płaskie Podhale/Kotlina Popradzka.
- Obszary „szumu” (losowa faza) to miejsca niskiej koherencji: lasy, zbiorniki wodne, strome stoki odwrócone od radaru (cień) lub zwrócone ku niemu (layover).
- Domieszka fazy atmosferycznej (para wodna – sierpień!) i ewentualnej deformacji jest na tym etapie nieodróżnialna od topografii.

## 3. Koherencja `coh_…` – histogram
`[UZUPEŁNIJ: zrzut histogramu + średnia/mediana koherencji]`
- Koherencja γ ∈ [0, 1] – moduł znormalizowanej korelacji zespolonej w oknie (domyślnie 10×3 px rg×az). γ ≈ 1 – piksele stabilne (skały, zabudowa), γ ≈ 0 – faza losowa.
- Spodziewany obraz: wysokie wartości na odsłoniętych skałach powyżej granicy lasu (sierpień – brak śniegu) i w zabudowie; niskie w lasach (pasmo C, λ≈5.5 cm, rozprasza się w koronach, które poruszają się z wiatrem), na wodzie i w obszarach layover/cienia; pola uprawne zmienne (żniwa w sierpniu – zmiana pokrycia w ciągu 12 dni).
- Ocena: `[UZUPEŁNIJ: np. „rozkład przesunięty ku wartościom średnim/wysokim, mediana 0.xx – dane nadają się do dalszego przetwarzania”]`.

## 4. S1-TOPS Deburst (1 pkt)
`[UZUPEŁNIJ: zrzut przed/po]`
W trybie TOPS (IW) każdy subswath rejestrowany jest jako seria burstów zachodzących na siebie w azymucie, rozdzielonych liniami bez danych (czarne pasy). Deburst łączy bursty w ciągły obraz i usuwa nieważne linie/próbki z brzegów burstów – nawet przy jednym burście obcina pasy bez danych, które psułyby filtrację (FFT w Goldsteinie) i rozwijanie fazy (nieciągłość = sztuczne skoki fazy).

## 5. Filtr Goldsteina (FFT 256, okno 7) i inne parametry
`[UZUPEŁNIJ: zrzuty dla kilku ustawień]`
Filtr adaptacyjny w dziedzinie częstotliwości: widmo fazy w każdym oknie FFT jest mnożone przez swój wygładzony moduł podniesiony do potęgi α (α=1). Wzmacnia dominującą częstotliwość prążków, tłumi szum – prążki stają się ostrzejsze, a obszary o niskiej koherencji gładsze.
- Większe FFT (256) – silniejsze uśrednianie, lepiej dla rzadkich prążków; ryzyko rozmycia gęstych prążków na stromych stokach.
- Mniejsze FFT (32/64) – lepiej zachowuje gęste prążki, słabsze odszumienie.
- Okno wygładzania widma 3 → 7 – coraz silniejsze wygładzanie.
- `[UZUPEŁNIJ: wnioski z porównania]`

## 6. Multilooking (9 looków w range) (1 pkt)
`[UZUPEŁNIJ: zrzut, rozmiar piksela wynikowego z metadanych]`
Uśrednianie zespolonego interferogramu w oknie 9 (range) × n (azymut; przy „GR square pixel” SNAP dobiera n tak, by piksel w terenie był ~kwadratowy – dla IW ok. 2). Piksel SLC IW to ok. 2.3 m (slant range) × 14 m (azymut), czyli ok. 4 m × 14 m w terenie → po multilookingu ok. 37 m × 28–42 m. Efekt: redukcja szumu fazy i speckle, mniejszy plik (szybszy snaphu) kosztem rozdzielczości przestrzennej.

## 7. Rozwijanie fazy – SNAPHU (1 pkt)
`[UZUPEŁNIJ: zrzut Phase_ vs Unw_Phase_, czas obliczeń]`
Snaphu Export: tryb kosztów TOPO, 5×5 kafli, zakładka 20 px. SNAPHU (statistical-cost network-flow) szuka takiej liczby całkowitej cykli 2π w każdym pikselu, by gradienty fazy były najbardziej prawdopodobne przy zadanym modelu kosztów (TOPO – model dla topografii, uwzględnia layover i koherencję). Wynik `Unw_Phase_` jest ciągły i rośnie z wysokością terenu, zamiast „zawijać się” co 2π. Błędy rozwijania (skoki o wielokrotność 2π ≈ h_a) koncentrują się w obszarach niskiej koherencji i na granicach kafli.
Na Linuksie snaphu skompilowano z `snaphu-v1.4.2.tar.gz` (`make`) zamiast używać `snaphu.exe` + Cygwin.

## 8. Phase to Elevation, Terrain Correction, porównanie z demTatry.tif (1 pkt)
`[UZUPEŁNIJ: mapy.png, wykresy.png, statystyki.txt ze skryptu skrypty/09_analiza_dem.py]`

| Statystyka różnicy InSAR − SRTM | Wartość |
|---|---|
| średnia / mediana | `[…]` |
| odch. std / NMAD | `[…]` |
| RMSE (po odjęciu offsetu) | `[…]` |

Gdzie największe różnice i dlaczego:
1. **Stałe przesunięcie** – różne odniesienia wysokości: SRTM (demTatry.tif) podaje wysokości względem geoidy EGM96, a wynik SNAP może być względem elipsoidy WGS84; w Polsce/Słowacji undulacja geoidy ≈ 40 m. Dodatkowo faza rozwinięta jest znana z dokładnością do stałej.
2. **Strome stoki** – geometria radaru (descending, patrzy na zachód): stoki wschodnie zwrócone ku radarowi → foreshortening/layover, stoki zachodnie odwrócone → cień radarowy. Tam brak użytecznej fazy, a interpolacja daje duże błędy. `[UZUPEŁNIJ: wartości z „klasy nachylenia/geometria radaru” w statystyki.txt]`
3. **Niska koherencja** – lasy reglowe, woda, zmiany pokrycia (żniwa) → szum fazy, błędy rozwijania (skoki ±h_a ≈ 180 m).
4. **Atmosfera** – opóźnienie troposferyczne zależne od wysokości (stratyfikacja) i turbulentne; w górach latem może dawać błędy rzędu kilku–kilkudziesięciu metrów wysokości przy h_a ≈ 180 m (1 rad fazy ≈ 29 m).
5. **Niejednorodność danych referencyjnych** – SRTM z 2000 r. (pasmo C, też widzi korony drzew), ok. 30 m, w Tatrach luki SRTM uzupełnione interpolacją; różnice w resamplingu.
6. **Mały B⊥** – im mniejszy baseline, tym większy h_a i tym większy błąd wysokości z tego samego szumu fazy (σ_h = h_a·σ_φ / 2π).
