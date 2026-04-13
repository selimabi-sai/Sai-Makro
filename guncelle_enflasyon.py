# -*- coding: utf-8 -*-
"""
Enflasyon Güncelleme — EVDS'den çek, makro_data/enflasyon.csv'ye kaydet.
Kullanim: python guncelle_enflasyon.py
"""

import logging
import sys
from datetime import datetime

import pandas as pd
from evds import evdsAPI

from config import DATA_DIR, EVDS_API_KEY
from veri_kaynak_onceligi import csv_gecmisi_koru


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("enflasyon")


CSV_DOSYA = DATA_DIR / "enflasyon.csv"
ENFLASYON_BASLANGIC = "01-01-2012"

ENFLASYON_SERILER = {
    "TP.FE25.OKTG01": "TUFE_Genel",
    "TP.FE25.OKTG04": "Cekirdek_C",
    "TP.FE25.OKTG23": "Hizmet",
    "TP.FE25.OKTG08": "Mallar",
    "TP.FE25.OKTG09": "Enerji",
    "TP.FE25.OKTG24": "Kira",
    "TP.ENFBEK.PKA12ENF": "Beklenti_Piyasa",
    "TP.ENFBEK.IYA12ENF": "Beklenti_ReelSektor",
    "TP.ENFBEK.HBA12ENF": "Beklenti_Hanehalki",
}


def main():
    bitis = datetime.now().strftime("%d-%m-%Y")
    evds = evdsAPI(EVDS_API_KEY)

    log.info("=" * 60)
    log.info("ENFLASYON GUNCELLEMESI")
    log.info("=" * 60)
    log.info("Veriler cekiliyor...")

    df = evds.get_data(
        list(ENFLASYON_SERILER.keys()),
        startdate=ENFLASYON_BASLANGIC,
        enddate=bitis,
    )

    if "Tarih" in df.columns:
        df["Tarih"] = pd.to_datetime(df["Tarih"], format="mixed", dayfirst=True, errors="coerce")
        df = df.sort_values("Tarih").reset_index(drop=True)
    if "UNIXTIME" in df.columns:
        df = df.drop(columns=["UNIXTIME"])

    rename_map = {"Tarih": "Tarih"}
    for kod, yeni_ad in ENFLASYON_SERILER.items():
        kolon = kod.replace(".", "_")
        rename_map[kolon] = yeni_ad
    df = df.rename(columns=rename_map)

    bilinen = ["Tarih"] + list(ENFLASYON_SERILER.values())
    mevcut = [c for c in bilinen if c in df.columns]
    df = df[mevcut].copy()
    df = csv_gecmisi_koru(CSV_DOSYA, df)

    for kolon in bilinen:
        if kolon in df.columns and kolon != "Tarih":
            df[kolon] = pd.to_numeric(df[kolon], errors="coerce")

    if "TUFE_Genel" in df.columns:
        df["TUFE_Aylik_Pct"] = df["TUFE_Genel"].pct_change() * 100
        df["TUFE_Yillik_Pct"] = df["TUFE_Genel"].pct_change(12) * 100
    if "Cekirdek_C" in df.columns:
        df["Cekirdek_Yillik_Pct"] = df["Cekirdek_C"].pct_change(12) * 100
    if "Hizmet" in df.columns:
        df["Hizmet_Yillik_Pct"] = df["Hizmet"].pct_change(12) * 100

    df.to_csv(CSV_DOSYA, index=False)

    log.info("")
    log.info(f"Kaydedildi: {CSV_DOSYA}")
    log.info(f"Satir: {len(df)} | Kolon: {len(df.columns)}")
    log.info(f"Tarih araligi: {df['Tarih'].min()} - {df['Tarih'].max()}")
    log.info("Enflasyon guncelleme tamamlandi.")


if __name__ == "__main__":
    main()
