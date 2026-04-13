# -*- coding: utf-8 -*-
"""
ÜFE Güncelleme — EVDS'den çek, makro_data/ufe.csv'ye kaydet.
Kullanım: python guncelle_ufe.py
"""

import time
import logging
import sys
from datetime import datetime

import pandas as pd

from config import (
    DATA_DIR, UFE_SERILER, UFE_BASLANGIC, evds_cek
)
from veri_kaynak_onceligi import csv_gecmisi_koru

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("ufe")

CSV_DOSYA = DATA_DIR / "ufe.csv"


def main():
    kodlar = list(UFE_SERILER.keys())
    bitis = datetime.now().strftime("%d-%m-%Y")

    log.info("=" * 60)
    log.info(f"ÜFE GÜNCELLEMESİ — {len(kodlar)} seri × 3 hesaplama")
    log.info("=" * 60)

    # 1) Düzey
    log.info("\n1/3  Düzey endeks çekiliyor...")
    df_duzey = evds_cek(kodlar, UFE_BASLANGIC, bitis)
    log.info(f"     ✓ {len(df_duzey)} satır")
    time.sleep(1)

    # 2) Aylık %
    log.info("2/3  Aylık % değişim çekiliyor...")
    df_aylik = evds_cek(kodlar, UFE_BASLANGIC, bitis, formulas=1)
    log.info(f"     ✓ {len(df_aylik)} satır")
    time.sleep(1)

    # 3) Yıllık %
    log.info("3/3  Yıllık % değişim çekiliyor...")
    df_yillik = evds_cek(kodlar, UFE_BASLANGIC, bitis, formulas=3)
    log.info(f"     ✓ {len(df_yillik)} satır")

    # Kolon isimleri
    def rename_map(suffix, formulas_ek=""):
        rm = {"Tarih": "Tarih"}
        for kod, isim in UFE_SERILER.items():
            evds_kol = kod.replace(".", "_") + formulas_ek
            rm[evds_kol] = f"{isim}{suffix}"
        return rm

    df_duzey = df_duzey.rename(columns=rename_map("_duzey", ""))
    df_aylik = df_aylik.rename(columns=rename_map("_aylik", "-1"))
    df_yillik = df_yillik.rename(columns=rename_map("_yillik", "-3"))

    # Birleştir
    df = df_duzey.merge(df_aylik, on="Tarih", how="outer")
    df = df.merge(df_yillik, on="Tarih", how="outer")
    df = df.sort_values("Tarih").reset_index(drop=True)
    df = csv_gecmisi_koru(CSV_DOSYA, df)

    for c in df.columns:
        if c != "Tarih":
            df[c] = pd.to_numeric(df[c], errors="coerce")

    # Kaydet
    df.to_csv(CSV_DOSYA, index=False)
    log.info(f"\n💾 {CSV_DOSYA}")
    log.info(f"   {len(df)} satır, {len(df.columns)} kolon")
    log.info(f"   Tarih aralığı: {df['Tarih'].min()} — {df['Tarih'].max()}")
    log.info("\n✅ ÜFE güncelleme tamamlandı.")


if __name__ == "__main__":
    main()
