#!/usr/bin/env bash
# Caly lancuch z instrukcji (lab3-2026.pdf) wykonany z linii polecen przez SNAP gpt.
# To alternatywa / zapas dla klikania w GUI - wyniki (BEAM-DIMAP) otwierasz potem
# w SNAP, zeby zrobic zrzuty, histogram koherencji itd.
#
# Uzycie:
#   ./02_przetwarzanie_gpt.sh            # wszystkie kroki (pomija te, ktore juz maja wynik)
#   ./02_przetwarzanie_gpt.sh 4 5        # tylko wybrane kroki
#   FFT=64 OKNO=3 SUFIKS=_fft64 ./02_przetwarzanie_gpt.sh 4   # test innych parametrow Goldsteina
#   DEM=external ./02_przetwarzanie_gpt.sh   # demTatry.tif zamiast Copernicus 30m (wersja zdalna)
#
# Kroki: 1 koregistracja, 2 interferogram, 3 deburst, 4 Goldstein, 5 multilook,
#        6 snaphu export + snaphu, 7 snaphu import, 8 wysokosc + terrain correction (GeoTIFF),
#        9 analiza roznicy z demTatry.tif
set -euo pipefail

LAB="$(cd "$(dirname "$0")/.." && pwd)"
G="$LAB/skrypty/grafy"
W="$LAB/wyniki"
GPT="${GPT:-$(command -v gpt || echo "$HOME/esa-snap/bin/gpt")}"
mkdir -p "$W"

MASTER="$LAB/dane/S1A_IW_SLC__1SDV_20160811T045259_20160811T045326_012548_013A69_24E3.zip"
SLAVE="$LAB/dane/S1A_IW_SLC__1SDV_20160823T045313_20160823T045340_012723_014032_AB6B.zip"
# Ustalone z metadanych burstow ASF - potwierdz: python3 01_sprawdz_burst.py ../dane/*.zip
SUBSWATH="${SUBSWATH:-IW1}"
BURST_M="${BURST_M:-6}"
BURST_S="${BURST_S:-1}"

if [[ "${DEM:-copernicus}" == external ]]; then
  DEMARGS=(-PdemName="External DEM" -PexternalDEM="$LAB/demTatry.tif")
else
  DEMARGS=(-PdemName="Copernicus 30m Global DEM" -PexternalDEM="")
fi
FFT="${FFT:-256}"; OKNO="${OKNO:-7}"; SUFIKS="${SUFIKS:-}"

P1="$W/01_coreg.dim"
P2="$W/02_coreg_ifg.dim"
P3="$W/03_coreg_ifg_deb.dim"
P4="$W/04_coreg_ifg_deb_flt${SUFIKS}.dim"
P5="$W/05_coreg_ifg_deb_flt_ML${SUFIKS}.dim"
P7="$W/07_unw${SUFIKS}.dim"
P8="$W/08_dem_insar_TC${SUFIKS}.tif"
P8b="$W/08_koherencja_TC.tif"

snaphu_dir() { echo "$W/snaphu/$(basename "$P5" .dim)"; }

gpt_run() {  # gpt_run <graf> <wynik> [parametry...]
  local graf="$1" wynik="$2"; shift 2
  if [[ -e "$wynik" && -z "${FORCE:-}" ]]; then
    echo ">> pomijam $(basename "$wynik") (istnieje; FORCE=1 aby nadpisac)"; return
  fi
  echo ">> $(basename "$graf") -> $(basename "$wynik")   [$(date +%T)]"
  time "$GPT" "$G/$graf" -c 4G -q "$(nproc)" -Poutput="$wynik" "$@"
}

krok() {
  case "$1" in
    1) [[ -f "$MASTER" && -f "$SLAVE" ]] || { echo "Brak plikow .zip w $LAB/dane (00_pobierz_dane.sh)" >&2; exit 1; }
       gpt_run 01_koregistracja.xml "$P1" -Pmaster="$MASTER" -Pslave="$SLAVE" \
         -Psubswath="$SUBSWATH" -PburstMaster="$BURST_M" -PburstSlave="$BURST_S" "${DEMARGS[@]}" ;;
    2) gpt_run 02_interferogram.xml "$P2" -Pinput="$P1" ;;
    3) gpt_run 03_deburst.xml "$P3" -Pinput="$P2" ;;
    4) gpt_run 04_goldstein.xml "$P4" -Pinput="$P3" -Pfft="$FFT" -Pokno="$OKNO" ;;
    5) gpt_run 05_multilook.xml "$P5" -Pinput="$P4" -PrgLooks="${RG_LOOKS:-9}" ;;
    6) # SNAP tworzy w EXP podfolder nazwany jak produkt wejsciowy
       local exp; exp="$(snaphu_dir)"
       if ! find "$exp" -name snaphu.conf 2>/dev/null | grep -q . || [[ -n "${FORCE:-}" ]]; then
         mkdir -p "$exp"
         echo ">> 05b_snaphu_export.xml -> $exp"
         "$GPT" "$G/05b_snaphu_export.xml" -c 4G -Pinput="$P5" -Pfolder="$exp" \
           -Pkafle="${KAFLE:-5}" -Poverlap="${OVERLAP:-20}"
       fi
       local conf; conf="$(find "$exp" -name snaphu.conf | head -1)"
       ls "$(dirname "$conf")"/UnwPhase_*.img >/dev/null 2>&1 && [[ -z "${FORCE:-}" ]] \
         && echo ">> pomijam snaphu (UnwPhase_*.img istnieje)" \
         || "$LAB/skrypty/06_uruchom_snaphu.sh" "$(dirname "$conf")" ;;
    7) local hdr; hdr="$(find "$(snaphu_dir)" -name 'UnwPhase_*.hdr' | head -1)"
       gpt_run 07_snaphu_import.xml "$P7" -Pinput="$P5" -PunwHdr="$hdr" ;;
    8) gpt_run 08_wysokosc_TC.xml "$P8" -Pinput="$P7" "${DEMARGS[@]}"
       gpt_run 08b_koherencja_TC.xml "$P8b" -Pinput="$P5" "${DEMARGS[@]}" ;;
    9) python3 "$LAB/skrypty/09_analiza_dem.py" --insar "$P8" --koherencja "$P8b" \
         --out "$W/analiza${SUFIKS}" ;;
    *) echo "Nieznany krok $1" >&2; exit 1 ;;
  esac
}

KROKI=("$@"); [[ ${#KROKI[@]} -gt 0 ]] || KROKI=(1 2 3 4 5 6 7 8 9)
for k in "${KROKI[@]}"; do krok "$k"; done
echo "Gotowe: ${KROKI[*]}"
