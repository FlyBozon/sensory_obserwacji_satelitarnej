Przygotowałam wszystko, co dało się zrobić bez zobrazowań. Po ich pobraniu zostaje uruchomienie trzech poleceń i zrzuty ekranu. Folder labu jest teraz w `.../sensory_obserwacji_satelitarnej/sensory_obserwacji_satelitarnej/lab3`. Pusty katalog, który przez chwilę odtworzyłem pod starą ścieżką, już usunąłem.

Skrypty sprawdziłem na sztucznych danych, a grafy SNAP tylko w teście bez danych wejściowych. Pełnego przebiegu przetwarzania nie dało się uruchomić bez zobrazowań.

## Co jest zrobione

- **ESA SNAP 14 jest zainstalowany** w `~/esa-snap`, ze skrótem w menu. Sprawdziłem, że nazwy pozycji menu zgadzają się z instrukcją.
- **Ustalone parametry bez pobierania scen**, z publicznych metadanych ASF:
  - master: 11.08.2016, IW1, burst 6;
  - slave: 23.08.2016, IW1, burst 1;
  - to ten sam fragment terenu nad Rysami, Gerlachem i Łomnicą, a zarazem jedyny burst nad Tatrami, który występuje w obu scenach;
  - baseline prostopadły ok. 72 m, czyli ok. 180 m wysokości na jeden prążek; to oszacowanie ASF, dokładną wartość pokaże Stack Overview.
- **[README.md](lab3/README.md) to ściąga.** Zawiera tabelę z każdym krokiem w menu SNAP i jego parametrami według aktualnej instrukcji (`lab3-2026.pdf`), kolejność pracy i pułapki.
- **[sprawozdanie_szkic.md](lab3/sprawozdanie_szkic.md)** ma gotowe odpowiedzi teoretyczne do każdego punktowanego zadania. Liczby i zrzuty wpisujesz w miejsca `[UZUPEŁNIJ]`.
- **Skrypty w [skrypty/](lab3/skrypty/):**

| Skrypt | Co robi | Test |
|---|---|---|
| `00_pobierz_dane.sh` | pobiera obie sceny (z możliwością wznowienia) i sprawdza sumy MD5 | – |
| `01_sprawdz_burst.py` | potwierdza numery burstów z plików .zip | sztuczna adnotacja ✔ |
| `02_przetwarzanie_gpt.sh` | cały łańcuch w linii poleceń, kroki 1–9 | grafy przechodzą walidację, pełny przebieg czeka na dane |
| `06_uruchom_snaphu.sh` | czyta polecenie z `snaphu.conf` i uruchamia skompilowane snaphu | sztuczna faza rozwinięta z błędem 0,0001 rad ✔ |
| `09_analiza_dem.py` | różnica InSAR − `demTatry.tif` (zamiast QGIS) ze statystykami, mapami i zależnością błędu od nachylenia, koherencji i geometrii radaru (layover, cień) | sztuczny DEM ✔ |

Skrypt `02_przetwarzanie_gpt.sh` to zapas. Możesz przeklikać lab w GUI według tabeli, a skryptem tylko sprawdzić wyniki albo zrobić testy filtracji, np. `FFT=64 OKNO=3 SUFIKS=_fft64 skrypty/02_przetwarzanie_gpt.sh 4 5`.

## Na co uważać w SNAP 14
Instrukcja była pisana pod starszą wersję SNAP. W filtrze Goldsteina pojawiła się nowa opcja **Use adaptive alpha**, domyślnie włączona. Odznacz ją, żeby filtr działał jak w instrukcji. Skrypt robi to sam.

## Po pobraniu danych
```bash
cd lab3
skrypty/00_pobierz_dane.sh                     # wymaga wpisu Earthdata w ~/.netrc, opis w skrypcie
python3 skrypty/01_sprawdz_burst.py dane/*.zip
~/esa-snap/bin/snap &                          # albo: skrypty/02_przetwarzanie_gpt.sh
```

Pierwsze przetwarzanie potrzebuje internetu, bo SNAP sam pobiera orbity i DEM Copernicus. Foldery `dane/` i `wyniki/` dodałem do `.gitignore`, żeby gigabajty danych nie trafiły do repo.