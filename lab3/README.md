# Lab 3 – InSAR: NMT Tatr z pary Sentinel-1 (SNAP + SNAPHU)

Instrukcje: [lab3-2026.pdf](lab3-2026.pdf) (aktualna, na zajęciach) i [lab3zdalne.pdf](lab3zdalne.pdf) (wersja zdalna).
Różnice: wersja 2026 używa DEM **Copernicus 30m (Auto Download)** i snaphu **5×5 kafli, overlap 20**;
wersja zdalna – External DEM `demTatry.tif` i 10×10 kafli. Domyślnie wszystko poniżej = wersja 2026.

## Co jest gotowe

- [x] `snaphu` skompilowane natywnie pod Linuksa (`./snaphu`, źródła w `snaphu_build/`) – `snaphu.exe`/Cygwin niepotrzebne. Przetestowane na syntetycznej fazie.
- [x] ESA SNAP 14 zainstalowany w `~/esa-snap` (GUI: `~/esa-snap/bin/snap`, linia poleceń: `~/esa-snap/bin/gpt`).
- [x] Ustalony subswath/burst z Tatrami i master/slave (tabela niżej).
- [x] Skrypty: pobieranie z weryfikacją MD5, sprawdzenie burstu, cały łańcuch w `gpt`, uruchamianie snaphu, analiza różnicy DEM.
- [x] [sprawozdanie_szkic.md](sprawozdanie_szkic.md) – odpowiedzi teoretyczne do każdego punktu, miejsca na zrzuty i liczby.
- [ ] Pobranie zobrazowań (~9.7 GB, wymaga konta NASA Earthdata).

## Parametry – ściąga

| | Master | Slave |
|---|---|---|
| Plik | `S1A_IW_SLC__1SDV_20160811T045259_…_24E3.zip` | `S1A_IW_SLC__1SDV_20160823T045313_…_AB6B.zip` |
| Data | 11.08.2016 | 23.08.2016 |
| **TOPSAR-Split** | **IW1, burst 6**, VV | **IW1, burst 1**, VV |

- Oba bursty to ten sam fragment terenu (`051_108178_IW1`): Rysy, Gerlach, Łomnica, Tatry Bielskie.
  IW2 (burst 6 / burst 1) obejmuje zachodnią część (Kasprowy, Krywań) – gdyby prowadzący chciał Tatry Zachodnie.
  Numery burstów są ustalone z metadanych ASF – po pobraniu potwierdź: `python3 skrypty/01_sprawdz_burst.py dane/*.zip`.
- Tor 51, descending, B⊥ ≈ 72 m (szac.), B_temp = 12 dni → h_a ≈ 180 m/prążek.
- Na mapie w TOPSAR-Split: biały prostokąt nad Tatrami (ok. 49.2°N, 20.1°E). Orbita descending, więc burst 1 jest najbardziej na północ:
  w scenie z 11.08 to 6. prostokąt licząc od północy, w scenie z 23.08 – pierwszy (najbardziej północny).

| Krok (menu SNAP) | Ustawienia |
|---|---|
| Radar › Interferometric › InSAR Stack Overview | dodaj oba .zip → Overview → master = 11.08 (sprawdź) |
| Radar › Coregistration › S1 TOPS Coregistration › S1 TOPS Coregistration | Read = master, Read(2) = slave; Split: IW1, VV, burst 6 / 1; Orbit: Sentinel Precise; Back-Geocoding: DEM Copernicus 30m (Auto Download), DEM resampling **BICUBIC**, resampling **BISINC_5_POINT** |
| Radar › Interferometric › Products › Interferogram Formation | Subtract flat-earth ✔ (reszta domyślnie) → oglądasz `Phase_ifg…`, histogram `coh_…` |
| Radar › Sentinel-1 TOPS › S-1 TOPS Deburst | VV |
| Radar › Interferometric › Filtering › Goldstein Phase Filtering | FFT **256**, window **7** (przetestuj np. 64/3, 128/5) |
| Radar › SAR Utilities › Multilooking | range looks **9**, GR square pixel (azymut liczy sam) |
| Radar › Interferometric › Unwrapping › Snaphu Export | folder wpisz ręcznie (np. `…/lab3/wyniki/snaphu`), **TOPO**, kafle **5×5**, overlap **20/20** |
| *terminal* | `skrypty/06_uruchom_snaphu.sh <folder z snaphu.conf>` |
| Radar › Interferometric › Unwrapping › Snaphu Import | Read-Phase = produkt po multilookingu, Read-Unwrapped-Phase = `UnwPhase_*.hdr` (nie .img!), w Write dopisz „2” do nazwy |
| Radar › Interferometric › Products › Phase to Elevation | DEM Copernicus 30m |
| Radar › Geometric › Terrain Correction › Range Doppler Terrain Correction | DEM Copernicus 30m; I/O: format **GeoTIFF**, zapis w `wyniki/` |
| QGIS › Raster Calculator | `"dem_insar@1" - "demTatry@1"` – albo `skrypty/09_analiza_dem.py` (to samo + statystyki i wykresy) |

## Kolejność pracy po pobraniu danych

```bash
cd lab3

# 1. pobranie (raz: konto Earthdata w ~/.netrc – patrz nagłówek skryptu)
skrypty/00_pobierz_dane.sh
python3 skrypty/01_sprawdz_burst.py dane/*.zip      # potwierdza IW1 burst 6 / burst 1

# 2a. GUI – zgodnie z tabelą wyżej (zrzuty do sprawozdania)
~/esa-snap/bin/snap &

# 2b. albo wszystko automatycznie (zapas / weryfikacja; ~kilkanaście–kilkadziesiąt min)
skrypty/02_przetwarzanie_gpt.sh                     # kroki 1–9, wyniki w wyniki/
FFT=64 OKNO=3 SUFIKS=_fft64 skrypty/02_przetwarzanie_gpt.sh 4 5   # inne parametry Goldsteina
DEM=external skrypty/02_przetwarzanie_gpt.sh        # wariant z demTatry.tif (wersja zdalna)
```

Wyniki `wyniki/*.dim` otwierasz w SNAP GUI (File › Open Product) – histogram koherencji, zrzuty faz itd.
Wynik analizy: `wyniki/analiza/{statystyki.txt, mapy.png, wykresy.png, roznica_dem.tif}`.

## Pułapki

- **SNAP 14 vs instrukcja** (pisana pod starszy SNAP): nazwy menu się zgadzają, ale
  - *Goldstein Phase Filtering* ma nową opcję **Use adaptive alpha** (domyślnie włączona) – odznacz, żeby był klasyczny filtr z α = 1 jak w instrukcji (skrypt gpt robi to domyślnie; `ADAPT_ALPHA=true` włącza);
  - *Phase to Elevation* ma wybór metody – zostaw domyślne **DEM Seed**;
  - *Interferogram Formation* – okno koherencji domyślnie 10×10.
- **Nie rozpakowuj .zip** – SNAP czyta je bezpośrednio.
- Pierwsze uruchomienie pobiera orbity precyzyjne i kafle Copernicus DEM – potrzebny internet.
- Snaphu Export: ścieżkę folderu **wpisz ręcznie**, a snaphu uruchamiaj w podfolderze nazwanym jak produkt.
- Snaphu Import: wskazujesz **.hdr**, nie .img.
- Różnica InSAR − SRTM ma stały offset (~40 m?) – SRTM jest względem geoidy EGM96; skrypt analizy podaje statystyki też po odjęciu mediany.
- `srtm_41_02/` jest niekompletny (brak .tif) i obejmuje 50–55°N – nie dotyczy Tatr, nieużywany.
- `dane/` i `wyniki/` są w `.gitignore` (gigabajty).
