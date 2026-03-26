# -*- coding: utf-8 -*-
"""
Yabancı Sermaye Akımı Güncelleme — EVDS'den çek, makro_data/ysa.csv'ye kaydet.
Kullanım: python guncelle_ysa.py
"""

import logging
import sys
from datetime import datetime

import pandas as pd

from config import (
    DATA_DIR, YSA_SERILER, YSA_BASLANGIC, evds_cek
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("ysa")

CSV_DOSYA = DATA_DIR / "ysa.csv"


def main():
    kodlar = list(YSA_SERILER.keys())
    bitis = datetime.now().strftime("%d-%m-%Y")

    log.info("=" * 60)
    log.info(f"YABANCI SERMAYE AKIMI GÜNCELLEMESİ — {len(kodlar)} seri")
    log.info("=" * 60)

    # Düzey çek (mn $ haftalık, formulas yok)
    log.info("Veriler çekiliyor...")
    df = evds_cek(kodlar, YSA_BASLANGIC, bitis)

    # Kolon isimleri düzenle
    rename_map = {"Tarih": "Tarih"}
    for kod, isim in YSA_SERILER.items():
        evds_kol = kod.replace(".", "_")
        rename_map[evds_kol] = isim
    df = df.rename(columns=rename_map)

    bilinen = ["Tarih"] + list(YSA_SERILER.values())
    mevcut = [c for c in bilinen if c in df.columns]
    df = df[mevcut].copy()

    for c in df.columns:
        if c != "Tarih":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.ffill().fillna(0)

    log.info(f"  ✓ {len(df)} satır çekildi")

    # Türev kolonlar
    df["Toplam"] = df[["Hisse", "DIBS", "Ozel_Sektor", "Eurobond"]].sum(axis=1)
    df["Kumulatif"] = df["Toplam"].cumsum()
    df["Hisse_8H"] = df["Hisse"].rolling(8).mean()
    df["DIBS_8H"] = df["DIBS"].rolling(8).mean()
    df["Ozel_Sektor_8H"] = df["Ozel_Sektor"].rolling(8).mean()
    df["Eurobond_8H"] = df["Eurobond"].rolling(8).mean()
    df["Toplam_8H"] = df["Toplam"].rolling(8).mean()
    df["Ceyrek"] = df["Tarih"].dt.to_period("Q").astype(str)

    # Kaydet
    df.to_csv(CSV_DOSYA, index=False)
    log.info(f"\n💾 {CSV_DOSYA}")
    log.info(f"   {len(df)} satır, {len(df.columns)} kolon")
    log.info(f"   Tarih aralığı: {df['Tarih'].min()} — {df['Tarih'].max()}")
    log.info("\n✅ YSA güncelleme tamamlandı.")


if __name__ == "__main__":
    main()
