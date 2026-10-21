#!/usr/bin/env python3
"""Sprawdza, ktory subswath/burst (numeracja jak w SNAP TOPSAR-Split, od 1)
zawiera Tatry - czyta adnotacje bezposrednio z .zip, bez rozpakowywania.

Uzycie:  python3 01_sprawdz_burst.py ../dane/*.zip
"""
import sys
import zipfile
import xml.etree.ElementTree as ET

SZCZYTY = {
    "Giewont": (19.934, 49.251),
    "Kasprowy Wierch": (19.982, 49.232),
    "Krywan": (20.000, 49.163),
    "Rysy": (20.088, 49.179),
    "Gerlach": (20.134, 49.164),
    "Lomnica": (20.213, 49.195),
    "Hawran (T. Bielskie)": (20.240, 49.240),
}


def w_wielokacie(pkt, poly):
    x, y = pkt
    wynik = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            wynik = not wynik
    return wynik


def rzad_siatki(punkty, linia):
    """lon/lat wzdluz linii `linia` - interpolacja liniowa miedzy wierszami siatki."""
    linie = sorted({p[0] for p in punkty})
    linia = min(max(linia, linie[0]), linie[-1])
    for a, b in zip(linie, linie[1:]):
        if a <= linia <= b:
            break
    t = (linia - a) / (b - a) if b != a else 0.0
    ra = sorted((p for p in punkty if p[0] == a), key=lambda p: p[1])
    rb = sorted((p for p in punkty if p[0] == b), key=lambda p: p[1])
    return [(pa[3] + t * (pb[3] - pa[3]), pa[2] + t * (pb[2] - pa[2])) for pa, pb in zip(ra, rb)]


def bursty(xml_bytes):
    root = ET.fromstring(xml_bytes)
    lpb = int(root.findtext("swathTiming/linesPerBurst"))
    n = len(root.findall("swathTiming/burstList/burst"))
    punkty = [
        (int(g.findtext("line")), int(g.findtext("pixel")),
         float(g.findtext("latitude")), float(g.findtext("longitude")))
        for g in root.iter("geolocationGridPoint")
    ]
    for k in range(n):
        gora = rzad_siatki(punkty, k * lpb)
        dol = rzad_siatki(punkty, (k + 1) * lpb - 1)
        yield k + 1, gora + dol[::-1]


def main(zipy):
    for sciezka in zipy:
        print(f"\n=== {sciezka.split('/')[-1]}")
        with zipfile.ZipFile(sciezka) as z:
            adnotacje = sorted(
                n for n in z.namelist()
                if "/annotation/s1" in n and "-vv-" in n and n.endswith(".xml")
                and "/calibration/" not in n
            )
            for nazwa in adnotacje:
                swath = nazwa.split("/")[-1].split("-")[1].upper()
                for nr, poly in bursty(z.read(nazwa)):
                    trafione = [s for s, p in SZCZYTY.items() if w_wielokacie(p, poly)]
                    if trafione:
                        print(f"  {swath} burst {nr}: {', '.join(trafione)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
