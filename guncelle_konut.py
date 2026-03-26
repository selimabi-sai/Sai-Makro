# -*- coding: utf-8 -*-
"""
Konut Güncelleme — EVDS'den çek, makro_data/konut.csv'ye kaydet.
Kullanım: python guncelle_konut.py
"""

import time
import logging
import sys
from datetime import datetime

import pandas as pd

from config import (
    DATA_DIR, KONUT_BASLANGIC,
    KONUT_FE_SERILER, KONUT_DUZEY_SERILER,
    KONUT_KREDI_SERILER, KONUT_RUHSAT_SERILER,
    evds_cek,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("konut")

CSV_DOSYA = DATA_DIR / "konut.csv"


def _rename(df, seri_dict, suffix="", formulas_ek=""):
    """EVDS kolon adlarını okunabilir isimlere çevir."""
    rm = {"Tarih": "Tarih"}
    for kod, isim in seri_dict.items():
        evds_kol = kod.replace(".", "_") + formulas_ek
        rm[evds_kol] = f"{isim}{suffix}"
    return df.rename(columns=rm)


def main():
    bitis = datetime.now().strftime("%d-%m-%Y")

    log.info("=" * 60)
    log.info("KONUT GÜNCELLEMESİ")
    log.info("=" * 60)

    parcalar = []

    # ── 1) Fiyat endeksleri — düzey + aylık % + yıllık % ──
    fe_kodlar = list(KONUT_FE_SERILER.keys())
    log.info(f"\n1/5  Fiyat Endeksleri (düzey) — {len(fe_kodlar)} seri...")
    df_fe_d = evds_cek(fe_kodlar, KONUT_BASLANGIC, bitis)
    df_fe_d = _rename(df_fe_d, KONUT_FE_SERILER, "_duzey")
    log.info(f"     ✓ {len(df_fe_d)} satır")
    time.sleep(1)

    log.info("2/5  Fiyat Endeksleri (aylık %)...")
    df_fe_a = evds_cek(fe_kodlar, KONUT_BASLANGIC, bitis, formulas=1)
    df_fe_a = _rename(df_fe_a, KONUT_FE_SERILER, "_aylik", "-1")
    log.info(f"     ✓ {len(df_fe_a)} satır")
    time.sleep(1)

    log.info("3/5  Fiyat Endeksleri (yıllık %)...")
    df_fe_y = evds_cek(fe_kodlar, KONUT_BASLANGIC, bitis, formulas=3)
    df_fe_y = _rename(df_fe_y, KONUT_FE_SERILER, "_yillik", "-3")
    log.info(f"     ✓ {len(df_fe_y)} satır")
    time.sleep(1)

    # Birleştir
    df_fe = df_fe_d.merge(df_fe_a, on="Tarih", how="outer").merge(df_fe_y, on="Tarih", how="outer")
    parcalar.append(df_fe)

    # ── 2) Düzey veriler (satış, birim fiyat/kira) ────────
    duzey_kodlar = list(KONUT_DUZEY_SERILER.keys())
    log.info(f"\n4/5  Satış & Birim veriler — {len(duzey_kodlar)} seri...")
    df_duzey = evds_cek(duzey_kodlar, KONUT_BASLANGIC, bitis, frequency=5)
    df_duzey = _rename(df_duzey, KONUT_DUZEY_SERILER)
    log.info(f"     ✓ {len(df_duzey)} satır")
    parcalar.append(df_duzey)
    time.sleep(1)

    # ── 3) Konut kredisi faizi (haftalık) ─────────────────
    kredi_kodlar = list(KONUT_KREDI_SERILER.keys())
    log.info(f"     Konut Kredisi Faizi — {len(kredi_kodlar)} seri...")
    df_kredi = evds_cek(kredi_kodlar, KONUT_BASLANGIC, bitis)
    df_kredi = _rename(df_kredi, KONUT_KREDI_SERILER)
    log.info(f"     ✓ {len(df_kredi)} satır")
    parcalar.append(df_kredi)
    time.sleep(1)

    # ── 4) Yapı ruhsatları ────────────────────────────────
    ruhsat_kodlar = list(KONUT_RUHSAT_SERILER.keys())
    log.info(f"\n5/5  Yapı Ruhsatları — {len(ruhsat_kodlar)} seri...")
    df_ruhsat = evds_cek(ruhsat_kodlar, KONUT_BASLANGIC, bitis)
    df_ruhsat = _rename(df_ruhsat, KONUT_RUHSAT_SERILER)
    log.info(f"     ✓ {len(df_ruhsat)} satır")
    parcalar.append(df_ruhsat)

    # ── Hepsini birleştir ─────────────────────────────────
    log.info("\nBirleştiriliyor...")
    df = parcalar[0]
    for p in parcalar[1:]:
        df = df.merge(p, on="Tarih", how="outer")

    df = df.sort_values("Tarih").reset_index(drop=True)

    # Numerik dönüşüm
    for c in df.columns:
        if c != "Tarih":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # ── Türev hesaplamalar ────────────────────────────────
    # Yapı ruhsatları: Apt + Ev = Toplam Konut
    if "Ruhsat_Apt_Yapi" in df.columns and "Ruhsat_Ev_Yapi" in df.columns:
        df["Ruhsat_Konut_Yapi"] = df["Ruhsat_Apt_Yapi"].fillna(0) + df["Ruhsat_Ev_Yapi"].fillna(0)
    if "Ruhsat_Apt_Yuzolcum" in df.columns and "Ruhsat_Ev_Yuzolcum" in df.columns:
        df["Ruhsat_Konut_Yuzolcum"] = df["Ruhsat_Apt_Yuzolcum"].fillna(0) + df["Ruhsat_Ev_Yuzolcum"].fillna(0)
    if "Ruhsat_Apt_Daire" in df.columns and "Ruhsat_Ev_Daire" in df.columns:
        df["Ruhsat_Konut_Daire"] = df["Ruhsat_Apt_Daire"].fillna(0) + df["Ruhsat_Ev_Daire"].fillna(0)

    # İpotekli satış oranı (%)
    if "Satis_Toplam" in df.columns and "Satis_Ipotekli" in df.columns:
        df["Ipotekli_Oran"] = (df["Satis_Ipotekli"] / df["Satis_Toplam"] * 100).round(1)

    # Birinci el satış oranı (%)
    if "Satis_Toplam" in df.columns and "Satis_IlkEl" in df.columns:
        df["IlkEl_Oran"] = (df["Satis_IlkEl"] / df["Satis_Toplam"] * 100).round(1)

    # Amortisman (ay) = birim fiyat / birim kira
    if "Birim_Fiyat_TLm2" in df.columns and "Birim_Kira_TLm2" in df.columns:
        df["Amortisman_Ay"] = (df["Birim_Fiyat_TLm2"] / df["Birim_Kira_TLm2"]).round(0)

    # ── Kaydet ────────────────────────────────────────────
    df.to_csv(CSV_DOSYA, index=False)
    log.info(f"\n💾 {CSV_DOSYA}")
    log.info(f"   {len(df)} satır, {len(df.columns)} kolon")
    log.info(f"   Tarih: {df['Tarih'].min()} — {df['Tarih'].max()}")
    log.info(f"\n   Kolonlar:")
    for c in df.columns:
        log.info(f"     {c}")
    log.info("\n✅ Konut güncelleme tamamlandı.")


if __name__ == "__main__":
    main()
