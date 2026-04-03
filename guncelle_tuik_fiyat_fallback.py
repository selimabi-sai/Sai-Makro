# -*- coding: utf-8 -*-
"""
TUİK bültenlerinden TÜFE ve Yİ-ÜFE fallback güncellemesi.

Amaç:
- EVDS geç güncellendiğinde TÜİK'in 10:00 bültenlerinden son ayı almak
- makro_data/tufe.csv ve makro_data/ufe.csv dosyalarına geçici ara güncelleme yazmak

Kullanım:
    python guncelle_tuik_fiyat_fallback.py
    python guncelle_tuik_fiyat_fallback.py --only tufe
    python guncelle_tuik_fiyat_fallback.py --data-dir /tmp/makro_deploy/makro_data --dry-run
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import re
import sys
import urllib.request
from pathlib import Path

import pandas as pd

from config import DATA_DIR, TUFE_SERILER, UFE_SERILER


BASE_URL = "https://veriportali.tuik.gov.tr"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/tr/press-releases",
    "X-Requested-With": "XMLHttpRequest",
}
TUFE_BULTEN_ADI = "Tüketici Fiyat Endeksi"
UFE_BULTEN_ADI = "Yurt İçi Üretici Fiyat Endeksi"
TR_AYLAR = {
    "ocak": 1,
    "subat": 2,
    "şubat": 2,
    "mart": 3,
    "nisan": 4,
    "mayis": 5,
    "mayıs": 5,
    "haziran": 6,
    "temmuz": 7,
    "agustos": 8,
    "ağustos": 8,
    "eylul": 9,
    "eylül": 9,
    "ekim": 10,
    "kasim": 11,
    "kasım": 11,
    "aralik": 12,
    "aralık": 12,
}
TUFE_ANA_SIRASI = list(TUFE_SERILER.values())[:14]
TUFE_CEKIRDEK_MAP = {
    "B": "Çekirdek B",
    "C": "Çekirdek C",
    "D": "Çekirdek D",
}
UFE_KOD_MAP = {
    "genel": "ÜFE Genel",
    "b": "Madencilik ve Taşocakçılığı",
    "c": "İmalat",
    "d": "Elektrik, Gaz, Buhar",
    "e": "Su Temini, Atık Yönetimi",
    "10": "Gıda Ürünleri",
    "11": "İçecekler",
    "13": "Tekstil",
    "14": "Giyim Eşyası",
    "15": "Deri",
    "17": "Kağıt",
    "20": "Kimyasallar",
    "24": "Ana Metaller",
    "28": "Makine ve Ekipmanlar",
    "31": "Mobilya",
}


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("tuik_fiyat_fallback")


def request_url(url: str):
    return urllib.request.Request(url, headers=HEADERS)


def api_get_json(path: str) -> dict:
    with urllib.request.urlopen(request_url(f"{BASE_URL}{path}"), timeout=60) as response:
        return json.load(response)


def download_bytes(url: str) -> bytes:
    full_url = url if url.startswith("http") else f"{BASE_URL}{url}"
    with urllib.request.urlopen(request_url(full_url), timeout=60) as response:
        return response.read()


def normalize_text(text: object) -> str:
    value = "" if text is None else str(text)
    value = value.replace("\n", " ").replace("\r", " ")
    return re.sub(r"\s+", " ", value).strip().lower()


def parse_press_id(press_url: str) -> int:
    match = re.search(r"/press/(\d+)", press_url or "")
    if not match:
        raise ValueError(f"Bulten id cozumlenemedi: {press_url}")
    return int(match.group(1))


def parse_period_start(period_text: str) -> pd.Timestamp:
    parts = str(period_text).strip().split()
    if len(parts) != 2:
        raise ValueError(f"Donem cozumlenemedi: {period_text}")
    ay = TR_AYLAR.get(normalize_text(parts[0]))
    yil = int(parts[1])
    if ay is None:
        raise ValueError(f"Ay cozumlenemedi: {period_text}")
    return pd.Timestamp(year=yil, month=ay, day=1)


def latest_press_detail(press_name: str) -> dict:
    payload = api_get_json("/api/tr/press/latest")
    items = payload.get("data") or []
    candidates = [
        item for item in items
        if item.get("name") == press_name and item.get("typeId") == 1 and item.get("url")
    ]
    if not candidates:
        raise ValueError(f"Latest API icinde bulten bulunamadi: {press_name}")
    candidates.sort(key=lambda item: item.get("date", ""), reverse=True)
    press_id = parse_press_id(candidates[0]["url"])
    detail_payload = api_get_json(f"/api/tr/press/{press_id}")
    return detail_payload["data"]


def find_excel_url(detail: dict, title_contains: str) -> str:
    needle = normalize_text(title_contains)
    for group_name in ("tables", "statisticalTables"):
        for item in detail.get(group_name) or []:
            if (item.get("type") or "").lower() not in {"xls", "xlsx"}:
                continue
            if needle in normalize_text(item.get("title")):
                return item["url"]
    raise ValueError(f"Excel eki bulunamadi: {title_contains}")


def last_numeric_value(row: pd.Series, start_col: int = 3) -> float:
    series = pd.to_numeric(row.iloc[start_col:], errors="coerce").dropna()
    if series.empty:
        raise ValueError("Satirda sayisal deger bulunamadi")
    return float(series.iloc[-1])


def parse_tufe_levels(detail: dict) -> tuple[pd.Timestamp, dict[str, float]]:
    period_start = parse_period_start(detail["period"])

    summary_url = find_excel_url(detail, "Ana harcama gruplarına göre ağırlıklar")
    core_url = find_excel_url(detail, "Özel Kapsamlı TÜFE Göstergeleri")

    summary_df = pd.read_excel(io.BytesIO(download_bytes(summary_url)), sheet_name=0, header=None)
    levels: dict[str, float] = {}
    for row_idx, series_name in zip(range(4, 18), TUFE_ANA_SIRASI):
        levels[series_name] = float(pd.to_numeric(summary_df.iloc[row_idx, 6], errors="coerce"))

    core_df = pd.read_excel(io.BytesIO(download_bytes(core_url)), sheet_name=0, header=None)
    for code, series_name in TUFE_CEKIRDEK_MAP.items():
        match = core_df[core_df[0].astype(str).str.strip().eq(code)]
        if match.empty:
            raise ValueError(f"Cekirdek TUFE satiri bulunamadi: {code}")
        levels[series_name] = last_numeric_value(match.iloc[0], start_col=3)

    return period_start, levels


def parse_ufe_levels(detail: dict) -> tuple[pd.Timestamp, dict[str, float]]:
    period_start = parse_period_start(detail["period"])
    sector_url = find_excel_url(detail, "Sektörlere göre yurt içi üretici fiyat endeksi")
    sector_df = pd.read_excel(io.BytesIO(download_bytes(sector_url)), sheet_name=0, header=None)

    levels: dict[str, float] = {}
    for idx in range(4, len(sector_df)):
        first_col = normalize_text(sector_df.iloc[idx, 0])
        code = normalize_text(sector_df.iloc[idx, 1])
        if (
            "ÜFE Genel" not in levels
            and ("yurt içi üretici fiyat endeksi" in first_col or "domestic producer price index" in first_col)
            and "general" in code
        ):
            levels["ÜFE Genel"] = float(pd.to_numeric(sector_df.iloc[idx, 3], errors="coerce"))
            continue
        if code not in UFE_KOD_MAP:
            continue
        levels[UFE_KOD_MAP[code]] = float(pd.to_numeric(sector_df.iloc[idx, 3], errors="coerce"))

    eksik = [name for name in UFE_SERILER.values() if name not in levels]
    if eksik:
        raise ValueError(f"UFE satirlari eksik: {', '.join(eksik)}")

    return period_start, levels


def upsert_latest_row(csv_path: Path, period_start: pd.Timestamp, levels: dict[str, float], series_names: list[str]) -> tuple[pd.DataFrame, bool]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV bulunamadi: {csv_path}")

    before = pd.read_csv(csv_path)
    after = before.copy()
    after["Tarih"] = pd.to_datetime(after["Tarih"], errors="coerce")

    row_mask = after["Tarih"].eq(period_start)
    row_data: dict[str, object] = {"Tarih": period_start}
    for series_name in series_names:
        row_data[f"{series_name}_duzey"] = levels[series_name]

    if row_mask.any():
        row_idx = after.index[row_mask][0]
        for key, value in row_data.items():
            after.at[row_idx, key] = value
    else:
        new_index = len(after)
        after.at[new_index, "Tarih"] = period_start
        for key, value in row_data.items():
            if key == "Tarih":
                continue
            after.at[new_index, key] = value

    after = after.sort_values("Tarih").reset_index(drop=True)

    for series_name in series_names:
        level_col = f"{series_name}_duzey"
        monthly_col = f"{series_name}_aylik"
        annual_col = f"{series_name}_yillik"
        after[level_col] = pd.to_numeric(after[level_col], errors="coerce")
        after[monthly_col] = after[level_col].pct_change(fill_method=None) * 100
        after[annual_col] = after[level_col].pct_change(12, fill_method=None) * 100

    changed = before.to_csv(index=False) != after.assign(
        Tarih=after["Tarih"].dt.strftime("%Y-%m-%d")
    ).to_csv(index=False)
    return after, changed


def save_dataframe(df: pd.DataFrame, csv_path: Path) -> None:
    output = df.copy()
    output["Tarih"] = output["Tarih"].dt.strftime("%Y-%m-%d")
    output.to_csv(csv_path, index=False)


def process_tufe(data_dir: Path, dry_run: bool) -> bool:
    csv_path = data_dir / "tufe.csv"
    detail = latest_press_detail(TUFE_BULTEN_ADI)
    period_start, levels = parse_tufe_levels(detail)
    updated_df, changed = upsert_latest_row(csv_path, period_start, levels, list(TUFE_SERILER.values()))
    latest_row = updated_df.loc[updated_df["Tarih"].eq(period_start)].iloc[0]
    log.info("TUFE TUİK fallback donemi: %s", period_start.strftime("%Y-%m-%d"))
    log.info("TUFE Genel duzey: %.2f", latest_row["TÜFE Genel_duzey"])
    log.info("Cekirdek C duzey: %.2f", latest_row["Çekirdek C_duzey"])
    if changed and not dry_run:
        save_dataframe(updated_df, csv_path)
        log.info("Yazildi: %s", csv_path)
    elif changed:
        log.info("Dry-run: tufe.csv degisecek")
    else:
        log.info("Degisiklik yok: tufe.csv")
    return changed


def process_ufe(data_dir: Path, dry_run: bool) -> bool:
    csv_path = data_dir / "ufe.csv"
    detail = latest_press_detail(UFE_BULTEN_ADI)
    period_start, levels = parse_ufe_levels(detail)
    updated_df, changed = upsert_latest_row(csv_path, period_start, levels, list(UFE_SERILER.values()))
    latest_row = updated_df.loc[updated_df["Tarih"].eq(period_start)].iloc[0]
    log.info("UFE TUİK fallback donemi: %s", period_start.strftime("%Y-%m-%d"))
    log.info("UFE Genel duzey: %.2f", latest_row["ÜFE Genel_duzey"])
    log.info("Imalat duzey: %.2f", latest_row["İmalat_duzey"])
    if changed and not dry_run:
        save_dataframe(updated_df, csv_path)
        log.info("Yazildi: %s", csv_path)
    elif changed:
        log.info("Dry-run: ufe.csv degisecek")
    else:
        log.info("Degisiklik yok: ufe.csv")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=("tufe", "ufe", "both"), default="both")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--data-dir", default=str(DATA_DIR))
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    changed_any = False

    log.info("=" * 60)
    log.info("TUIK FIYAT FALLBACK GUNCELLEMESI")
    log.info("Veri klasoru: %s", data_dir)
    log.info("Mod: %s", "dry-run" if args.dry_run else "write")
    log.info("=" * 60)

    if args.only in ("tufe", "both"):
        changed_any = process_tufe(data_dir, args.dry_run) or changed_any

    if args.only in ("ufe", "both"):
        changed_any = process_ufe(data_dir, args.dry_run) or changed_any

    log.info("-" * 60)
    if changed_any:
        log.info("Fallback veri hazir.")
    else:
        log.info("Yeni fallback degisikligi bulunmadi.")


if __name__ == "__main__":
    main()
