#!/usr/bin/env python3
"""Ostatni punkt labu: porownanie DEM z InSAR z demTatry.tif (odpowiednik
Raster Calculator w QGIS) + statystyki i wykresy do sprawozdania.

Uzycie:
  python3 09_analiza_dem.py --insar ../wyniki/08_dem_insar_TC.tif \
      [--koherencja ../wyniki/08_koherencja_TC.tif] [--ref ../demTatry.tif] \
      [--out ../wyniki/analiza]

Wyniki: roznica_dem.tif (InSAR - ref), statystyki.txt, wykresy *.png.
"""
import argparse
import os

import numpy as np
from osgeo import gdal
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

gdal.UseExceptions()

# Geometria Sentinel-1, tor 51 descending, IW1 (sprawdz w metadanych SNAP:
# Abstracted_Metadata -> centre_heading, incidence_near/far)
HEADING = 193.0          # kierunek lotu satelity [deg od N]
KAT_PADANIA = 34.0       # srodek IW1 (~30.5-36.5 deg)


def wczytaj_na_siatke(sciezka, wzor):
    """Przepróbkowuje raster `sciezka` na siatke rastra `wzor` (bilinear)."""
    gt = wzor.GetGeoTransform()
    ds = gdal.Warp(
        "", sciezka, format="MEM",
        outputBounds=(gt[0], gt[3] + gt[5] * wzor.RasterYSize,
                      gt[0] + gt[1] * wzor.RasterXSize, gt[3]),
        width=wzor.RasterXSize, height=wzor.RasterYSize,
        dstSRS=wzor.GetProjection(), resampleAlg="bilinear", dstNodata=np.nan,
        outputType=gdal.GDT_Float32,
    )
    return ds.ReadAsArray().astype(np.float64)


def pasmo(ds):
    b = ds.GetRasterBand(1)
    a = b.ReadAsArray().astype(np.float64)
    nd = b.GetNoDataValue()
    if nd is not None:
        a[a == nd] = np.nan
    a[a == 0] = np.nan  # SNAP wpisuje 0 poza obszarem danych
    return a


def geometria(dem, gt):
    """Nachylenie, ekspozycja i lokalny kat padania dla siatki w stopniach geogr."""
    lat0 = gt[3] + gt[5] * dem.shape[0] / 2
    dx = abs(gt[1]) * 111320 * np.cos(np.radians(lat0))
    dy = abs(gt[5]) * 110540
    dz_dy, dz_dx = np.gradient(dem, dy, dx)
    dz_dy = -dz_dy  # wiersze rosna na poludnie
    nachylenie = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
    ekspozycja = (np.degrees(np.arctan2(-dz_dx, -dz_dy)) + 360) % 360  # kierunek spadku
    # wektor od terenu do satelity (patrzy w prawo => satelita po lewej stronie toru)
    az_do_sat = np.radians((HEADING - 90) % 360)
    th = np.radians(KAT_PADANIA)
    v = np.array([np.sin(th) * np.sin(az_do_sat), np.sin(th) * np.cos(az_do_sat), np.cos(th)])
    s, a = np.radians(nachylenie), np.radians(ekspozycja)
    n = np.stack([np.sin(s) * np.sin(a), np.sin(s) * np.cos(a), np.cos(s)])
    cos_lok = np.tensordot(v, n, axes=1)
    kat_lok = np.degrees(np.arccos(np.clip(cos_lok, -1, 1)))
    return nachylenie, ekspozycja, kat_lok


def statystyki(x):
    x = x[np.isfinite(x)]
    p = np.percentile(x, [2, 5, 25, 50, 75, 95, 98])
    return {
        "liczba pikseli": x.size,
        "srednia [m]": x.mean(),
        "mediana [m]": p[3],
        "odch. std [m]": x.std(),
        "RMSE [m]": np.sqrt(np.mean(x ** 2)),
        "NMAD [m]": 1.4826 * np.median(np.abs(x - p[3])),
        "min / max [m]": (x.min(), x.max()),
        "p2 / p98 [m]": (p[0], p[6]),
        "p25 / p75 [m]": (p[2], p[4]),
    }


def main():
    ap = argparse.ArgumentParser()
    tu = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--insar", required=True)
    ap.add_argument("--ref", default=os.path.join(tu, "..", "demTatry.tif"))
    ap.add_argument("--koherencja")
    ap.add_argument("--out", default=os.path.join(tu, "..", "wyniki", "analiza"))
    arg = ap.parse_args()
    os.makedirs(arg.out, exist_ok=True)

    ds = gdal.Open(arg.insar)
    gt = ds.GetGeoTransform()
    insar = pasmo(ds)
    ref = wczytaj_na_siatke(arg.ref, ds)
    roznica = insar - ref
    nach, eksp, kat_lok = geometria(ref, gt)
    koh = wczytaj_na_siatke(arg.koherencja, ds) if arg.koherencja else None

    drv = gdal.GetDriverByName("GTiff")
    out = drv.Create(os.path.join(arg.out, "roznica_dem.tif"), ds.RasterXSize, ds.RasterYSize, 1,
                     gdal.GDT_Float32, options=["COMPRESS=DEFLATE"])
    out.SetGeoTransform(gt)
    out.SetProjection(ds.GetProjection())
    out.GetRasterBand(1).WriteArray(np.where(np.isfinite(roznica), roznica, -9999).astype(np.float32))
    out.GetRasterBand(1).SetNoDataValue(-9999)
    out = None

    st = statystyki(roznica)
    offset = st["mediana [m]"]
    linie = ["Roznica DEM InSAR - demTatry.tif", "=" * 40]
    def fmt(v):
        if isinstance(v, tuple):
            return " / ".join(f"{x:.1f}" for x in v)
        return f"{v:.2f}" if isinstance(v, float) else str(v)
    linie += [f"{k:16s}: {fmt(v)}" for k, v in st.items()]
    linie += ["", f"Po odjeciu stalego przesuniecia (mediana {offset:.1f} m):"]
    st2 = statystyki(roznica - offset)
    linie += [f"  {k:14s}: {v:.2f}" for k, v in st2.items() if isinstance(v, float)]

    ok = np.isfinite(roznica)
    bez = np.abs(roznica - offset)
    linie += ["", "Sredni |blad| (po odjeciu offsetu) w klasach nachylenia:"]
    for lo, hi in [(0, 10), (10, 20), (20, 30), (30, 40), (40, 90)]:
        m = ok & (nach >= lo) & (nach < hi)
        if m.any():
            linie.append(f"  {lo:2d}-{hi:2d} deg: {bez[m].mean():7.1f} m  ({m.sum()} px)")
    layover = ok & (kat_lok < 10)      # stoki zwrocone do radaru, bliskie layover
    cien = ok & (kat_lok > 80)         # stoki odwrocone, bliskie cienia radarowego
    reszta = ok & ~layover & ~cien
    linie += ["", "Geometria radaru (lokalny kat padania):",
              f"  ~layover/foreshortening (<10 deg): {bez[layover].mean() if layover.any() else float('nan'):7.1f} m  ({layover.sum()} px)",
              f"  ~cien radarowy (>80 deg)         : {bez[cien].mean() if cien.any() else float('nan'):7.1f} m  ({cien.sum()} px)",
              f"  pozostale                        : {bez[reszta].mean():7.1f} m  ({reszta.sum()} px)"]
    if koh is not None:
        linie += ["", "Sredni |blad| w klasach koherencji:"]
        for lo, hi in [(0, .2), (.2, .4), (.4, .6), (.6, .8), (.8, 1.01)]:
            m = ok & (koh >= lo) & (koh < hi)
            if m.any():
                linie.append(f"  {lo:.1f}-{min(hi, 1):.1f}: {bez[m].mean():7.1f} m  ({m.sum()} px)")
    tekst = "\n".join(linie)
    open(os.path.join(arg.out, "statystyki.txt"), "w").write(tekst + "\n")
    print(tekst)

    ext = (gt[0], gt[0] + gt[1] * ds.RasterXSize, gt[3] + gt[5] * ds.RasterYSize, gt[3])
    lim = np.nanpercentile(np.abs(roznica - offset), 98)

    fig, ax = plt.subplots(1, 3, figsize=(18, 5.5), constrained_layout=True)
    for a, dane, tyt, cmap, vr in [
        (ax[0], ref, "demTatry.tif (SRTM) [m]", "terrain", (np.nanmin(ref), np.nanmax(ref))),
        (ax[1], insar, "DEM z InSAR [m]", "terrain", (np.nanmin(ref), np.nanmax(ref))),
        (ax[2], roznica - offset, f"InSAR - SRTM - {offset:.0f} m [m]", "RdBu_r", (-lim, lim)),
    ]:
        im = a.imshow(dane, extent=ext, cmap=cmap, vmin=vr[0], vmax=vr[1], interpolation="nearest")
        a.set_title(tyt)
        a.set_aspect(1 / np.cos(np.radians((ext[2] + ext[3]) / 2)))
        a.set_xlabel("dlugosc geogr. [deg]")
        fig.colorbar(im, ax=a, shrink=0.8)
    ax[0].set_ylabel("szerokosc geogr. [deg]")
    fig.savefig(os.path.join(arg.out, "mapy.png"), dpi=150)

    fig, ax = plt.subplots(1, 3 if koh is not None else 2, figsize=(16, 4.5), constrained_layout=True)
    r = (roznica - offset)[ok]
    ax[0].hist(r, bins=200, range=(-lim, lim), color="#3b6ea5")
    ax[0].set_title("Histogram roznicy (po odjeciu offsetu)")
    ax[0].set_xlabel("[m]")
    klasy = np.arange(0, 60, 5)
    sr = [bez[ok & (nach >= k) & (nach < k + 5)].mean() if (ok & (nach >= k) & (nach < k + 5)).any() else np.nan for k in klasy]
    ax[1].plot(klasy + 2.5, sr, "o-")
    ax[1].set_title("Sredni |blad| a nachylenie stoku")
    ax[1].set_xlabel("nachylenie [deg]")
    ax[1].set_ylabel("|blad| [m]")
    if koh is not None:
        kk = np.arange(0, 1, 0.05)
        sr = [bez[ok & (koh >= k) & (koh < k + .05)].mean() if (ok & (koh >= k) & (koh < k + .05)).any() else np.nan for k in kk]
        ax[2].plot(kk + .025, sr, "o-")
        ax[2].set_title("Sredni |blad| a koherencja")
        ax[2].set_xlabel("koherencja")
    fig.savefig(os.path.join(arg.out, "wykresy.png"), dpi=150)
    print("\nZapisano w", os.path.abspath(arg.out))


if __name__ == "__main__":
    main()
