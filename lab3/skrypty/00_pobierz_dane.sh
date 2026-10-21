#!/usr/bin/env bash
# Pobiera obie sceny Sentinel-1 SLC z ASF do lab3/dane/ i sprawdza sumy MD5.
#
# Wymaga konta NASA Earthdata (https://urs.earthdata.nasa.gov) wpisanego do ~/.netrc:
#   echo "machine urs.earthdata.nasa.gov login LOGIN password HASLO" >> ~/.netrc
#   chmod 600 ~/.netrc
#
# Mozna przerwac (Ctrl+C) i uruchomic ponownie - wget -c wznowi pobieranie.
set -euo pipefail

LAB="$(cd "$(dirname "$0")/.." && pwd)"
DANE="$LAB/dane"
mkdir -p "$DANE"

# nazwa sceny -> md5 (z API ASF)
declare -A MD5=(
  [S1A_IW_SLC__1SDV_20160811T045259_20160811T045326_012548_013A69_24E3]=4fbb5872ca0cd6eb2ddb76347edfc20a
  [S1A_IW_SLC__1SDV_20160823T045313_20160823T045340_012723_014032_AB6B]=adda7a84bbd16d5ddf4b7340849d803a
)

if ! grep -q "urs.earthdata.nasa.gov" ~/.netrc 2>/dev/null; then
  echo "Brak wpisu urs.earthdata.nasa.gov w ~/.netrc - patrz komentarz na gorze skryptu." >&2
  exit 1
fi

for SCENA in "${!MD5[@]}"; do
  PLIK="$DANE/$SCENA.zip"
  echo "=== $SCENA"
  wget -c --netrc --auth-no-challenge --keep-session-cookies \
       --load-cookies /tmp/asf_cookies.txt --save-cookies /tmp/asf_cookies.txt \
       -O "$PLIK" "https://datapool.asf.alaska.edu/SLC/SA/$SCENA.zip"
  echo -n "md5: "
  if echo "${MD5[$SCENA]}  $PLIK" | md5sum -c --quiet -; then
    echo "OK"
  else
    echo "NIEZGODNE - usun plik i pobierz ponownie" >&2
  fi
done
