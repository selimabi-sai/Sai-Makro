# -*- coding: utf-8 -*-
"""
Veri kaynak önceliği yardımcıları.

Öncelik sırası:
1. Taze çekilen veri
2. Resmi fallback / önceki katmanlardan eklenen veri
3. Mevcut CSV geçmişi
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def csv_gecmisi_koru(
    csv_path: Path,
    fresh_df: pd.DataFrame,
    tarih_kol: str = "Tarih",
) -> pd.DataFrame:
    """
    Taze dataframe'i mevcut CSV ile birleştirir.

    Aynı tarih/kolon için taze veri önceliklidir; taze veri NaN ise mevcut CSV değeri korunur.
    CSV'de olup bu tur gelmeyen kolonlar/satırlar da saklanır.
    """
    fresh = fresh_df.copy()
    if tarih_kol not in fresh.columns:
        return fresh

    fresh[tarih_kol] = pd.to_datetime(fresh[tarih_kol], errors="coerce")
    fresh = (
        fresh.dropna(subset=[tarih_kol])
        .sort_values(tarih_kol)
        .drop_duplicates(subset=[tarih_kol], keep="last")
        .reset_index(drop=True)
    )

    if not csv_path.exists():
        return fresh

    try:
        mevcut = pd.read_csv(csv_path)
    except Exception:
        return fresh

    if tarih_kol not in mevcut.columns:
        return fresh

    mevcut[tarih_kol] = pd.to_datetime(mevcut[tarih_kol], errors="coerce")
    mevcut = (
        mevcut.dropna(subset=[tarih_kol])
        .sort_values(tarih_kol)
        .drop_duplicates(subset=[tarih_kol], keep="last")
        .reset_index(drop=True)
    )

    taze_indexli = fresh.set_index(tarih_kol)
    mevcut_indexli = mevcut.set_index(tarih_kol)
    birlesik = taze_indexli.combine_first(mevcut_indexli)
    birlesik.index.name = tarih_kol
    birlesik = birlesik.reset_index().sort_values(tarih_kol).reset_index(drop=True)

    kolon_sirasi = [tarih_kol]
    kolon_sirasi.extend([c for c in fresh.columns if c != tarih_kol])
    kolon_sirasi.extend([c for c in mevcut.columns if c != tarih_kol and c not in kolon_sirasi])
    return birlesik.reindex(columns=kolon_sirasi)
