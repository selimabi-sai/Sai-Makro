# -*- coding: utf-8 -*-
"""
Kredi Kartı Güncelleme — EVDS'den çek, makro_data/kredi_karti.csv'ye kaydet.
Kullanım: python guncelle_kredi_karti.py

Çıktı CSV yapısı (ham veri):
  Tarih, KT1..KT26, KT49..KT52  (harcama, Bin TL)
         KA1..KA26, KA49..KA52  (işlem adedi)

Türev hesaplamaları (MA, YoY, Sepet) dashboard tarafında yapılır.
"""

import time
import logging
import sys
from datetime import datetime

import pandas as pd

from config import (
    DATA_DIR, EVDS_API_KEY,
    KK_BASLANGIC, KK_KT_SUFFIXES, KK_KA_SUFFIXES,
)
from evds import evdsAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("kredi_karti")

CSV_DOSYA = DATA_DIR / "kredi_karti.csv"
BATCH_SIZE = 15


def evds_batch_pull(evds, prefix, suffixes, start, end):
    """EVDS'den 15'li batch'ler halinde veri çek ve birleştir."""
    all_dfs = []
    for i in range(0, len(suffixes), BATCH_SIZE):
        batch = suffixes[i:i + BATCH_SIZE]
        codes = [f"{prefix}.{s}" for s in batch]
        log.info(f"     {codes[0]} ... {codes[-1]} ({len(codes)} seri)")
        try:
            df = evds.get_data(codes, startdate=start, enddate=end)
            all_dfs.append(df)
        except Exception as e:
            log.error(f"     HATA: {e}")
        time.sleep(1)

    if not all_dfs:
        return pd.DataFrame()

    merged = all_dfs[0]
    for d in all_dfs[1:]:
        merged = merged.merge(d, on="Tarih", how="outer")
    return merged


def main():
    bitis = datetime.now().strftime("%d-%m-%Y")

    log.info("=" * 60)
    log.info("KREDİ KARTI GÜNCELLEMESİ")
    log.info("=" * 60)

    evds = evdsAPI(EVDS_API_KEY)

    # ── 1) Harcama tutarları (Bin TL) ─────────────────────
    log.info(f"\n1/2  Harcama tutarları — {len(KK_KT_SUFFIXES)} seri...")
    df_kt = evds_batch_pull(evds, "TP.KKHARTUT", KK_KT_SUFFIXES, KK_BASLANGIC, bitis)
    log.info(f"     ✓ {len(df_kt)} satır")

    # ── 2) İşlem adetleri ────────────────────────────────
    log.info(f"\n2/2  İşlem adetleri — {len(KK_KA_SUFFIXES)} seri...")
    df_ka = evds_batch_pull(evds, "TP.KKISLADE", KK_KA_SUFFIXES, KK_BASLANGIC, bitis)
    log.info(f"     ✓ {len(df_ka)} satır")

    # ── Tarih düzenle ─────────────────────────────────────
    for df in [df_kt, df_ka]:
        if "Tarih" in df.columns:
            df["Tarih"] = pd.to_datetime(df["Tarih"], format="mixed", dayfirst=True, errors="coerce")
        if "UNIXTIME" in df.columns:
            df.drop(columns=["UNIXTIME"], inplace=True)

    df_kt = df_kt.sort_values("Tarih").reset_index(drop=True)
    df_ka = df_ka.sort_values("Tarih").reset_index(drop=True)

    # ── Kolon isimlerini normalize et ─────────────────────
    # TP_KKHARTUT_KT1 → KT1,  TP_KKISLADE_KA1 → KA1
    def norm_col(c):
        return c.replace("TP_KKHARTUT_", "").replace("TP_KKISLADE_", "")

    df_kt.columns = [norm_col(c) if c != "Tarih" else c for c in df_kt.columns]
    df_ka.columns = [norm_col(c) if c != "Tarih" else c for c in df_ka.columns]

    # ── Numerik dönüşüm + boş doldur ─────────────────────
    for c in df_kt.columns:
        if c != "Tarih":
            df_kt[c] = pd.to_numeric(df_kt[c], errors="coerce")
    for c in df_ka.columns:
        if c != "Tarih":
            df_ka[c] = pd.to_numeric(df_ka[c], errors="coerce")

    df_kt = df_kt.ffill().fillna(0)
    df_ka = df_ka.ffill().fillna(0)

    # ── Birleştir ─────────────────────────────────────────
    log.info("\nBirleştiriliyor...")
    df = df_kt.merge(df_ka, on="Tarih", how="outer")
    df = df.sort_values("Tarih").reset_index(drop=True)

    # ── Kaydet ────────────────────────────────────────────
    df.to_csv(CSV_DOSYA, index=False)

    kt_cols = [c for c in df.columns if c.startswith("KT")]
    ka_cols = [c for c in df.columns if c.startswith("KA")]

    log.info(f"\n💾 {CSV_DOSYA}")
    log.info(f"   {len(df)} satır, {len(df.columns)} kolon")
    log.info(f"   KT kolonları: {len(kt_cols)}, KA kolonları: {len(ka_cols)}")
    log.info(f"   Tarih: {df['Tarih'].min()} — {df['Tarih'].max()}")

    if "KT1" in df.columns:
        son = df.iloc[-1]
        log.info(f"   Son hafta toplam harcama: {float(son['KT1'])/1e6:,.1f} mr ₺")

    log.info("\n✅ Kredi kartı güncelleme tamamlandı.")


if __name__ == "__main__":
    main()
