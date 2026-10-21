#!/usr/bin/env bash
# Uruchamia snaphu (skompilowane w lab3/snaphu) z poleceniem zapisanym w
# naglowku snaphu.conf przez SNAP (Snaphu Export).
#
# Uzycie:  ./06_uruchom_snaphu.sh <folder_z_snaphu.conf>
#   np.    ./06_uruchom_snaphu.sh ../wyniki/snaphu/05_ifg_deb_flt_ML
# Bez argumentu szuka snaphu.conf w lab3/wyniki/snaphu/*/
set -euo pipefail

LAB="$(cd "$(dirname "$0")/.." && pwd)"
SNAPHU="$LAB/snaphu"

if [[ $# -ge 1 ]]; then
  DIR="$1"
else
  DIR="$(dirname "$(ls -t "$LAB"/wyniki/snaphu/*/snaphu.conf | head -1)")"
fi
cd "$DIR"
[[ -f snaphu.conf ]] || { echo "Brak snaphu.conf w $DIR" >&2; exit 1; }

# Naglowek wyglada tak:
#   # Command to call snaphu:
#   #
#   #       snaphu -f snaphu.conf Phase_ifg_IW1_VV_11Aug2016_23Aug2016.snaphu.img 2569
CMD="$(grep -m1 -E '^#\s+snaphu\s+-f' snaphu.conf | sed -E 's/^#\s+snaphu\s+//')"
[[ -n "$CMD" ]] || { echo "Nie znaleziono polecenia w snaphu.conf" >&2; exit 1; }

echo "Folder : $DIR"
echo "Polecenie: $SNAPHU $CMD"
echo "Start  : $(date)"
# shellcheck disable=SC2086
time "$SNAPHU" $CMD 2>&1 | tee snaphu.log
echo "Koniec : $(date)"
# .hdr tworzy juz SNAP przy eksporcie - snaphu dopisuje tylko .img
ls -la UnwPhase_*.img 2>/dev/null || echo "UWAGA: brak pliku UnwPhase_*.img - sprawdz snaphu.log"
