# -*- coding: utf-8 -*-
"""
Konut Güncelleme — EVDS + TÜİK press API, makro_data/konut.csv'ye kaydet.
Kullanım: python guncelle_konut.py
"""

import ast
import html
import json
import logging
import re
import sys
import time
import unicodedata
import urllib.request
from datetime import datetime

import pandas as pd

from config import (
    DATA_DIR, KONUT_BASLANGIC,
    KONUT_FE_SERILER, KONUT_DUZEY_SERILER,
    KONUT_KREDI_SERILER, KONUT_RUHSAT_SERILER,
    evds_cek,
)
from veri_kaynak_onceligi import csv_gecmisi_koru

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("konut")

CSV_DOSYA = DATA_DIR / "konut.csv"
KONUT_PRESS_BASE_URL = "https://veriportali.tuik.gov.tr"
KONUT_PRESS_TITLE = "Konut ve İş Yeri Satış İstatistikleri"
INSAAT_MALIYET_PRESS_TITLE = "İnşaat Maliyet Endeksi"
INSAAT_URETIM_PRESS_TITLE = "İnşaat Üretim Endeksi"
INSAAT_GUVEN_PRESS_TITLE = "Hizmet, Perakende Ticaret ve İnşaat Güven Endeksleri"
KONUT_PRESS_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/135.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Origin": KONUT_PRESS_BASE_URL,
    "Referer": f"{KONUT_PRESS_BASE_URL}/tr/press-releases",
    "X-Requested-With": "XMLHttpRequest",
}
KONUT_SATIS_KOLONLARI = [
    "Satis_Toplam",
    "Satis_Ipotekli",
    "Satis_IlkEl",
    "Satis_IkinciEl",
]
INSAAT_KOLONLARI = [
    "Insaat_Maliyet_Aylik_Degisim",
    "Insaat_Maliyet_Yillik_Degisim",
    "Insaat_Uretim_Aylik_Degisim",
    "Insaat_Uretim_Yillik_Degisim",
    "Insaat_Guven_Endeks",
]
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
TR_CHAR_MAP = str.maketrans({
    "ı": "i",
    "İ": "I",
    "ş": "s",
    "Ş": "S",
    "ğ": "g",
    "Ğ": "G",
    "ü": "u",
    "Ü": "U",
    "ö": "o",
    "Ö": "O",
    "ç": "c",
    "Ç": "C",
})


def _rename(df, seri_dict, suffix="", formulas_ek=""):
    """EVDS kolon adlarını okunabilir isimlere çevir."""
    rm = {"Tarih": "Tarih"}
    for kod, isim in seri_dict.items():
        evds_kol = kod.replace(".", "_") + formulas_ek
        rm[evds_kol] = f"{isim}{suffix}"
    return df.rename(columns=rm)


def _request_url(url):
    return urllib.request.Request(url, headers=KONUT_PRESS_HEADERS)


def _api_get_json(path, timeout=60):
    full_url = path if path.startswith("http") else f"{KONUT_PRESS_BASE_URL}{path}"
    son_hata = None
    for deneme in range(3):
        try:
            with urllib.request.urlopen(_request_url(full_url), timeout=timeout) as response:
                return json.load(response)
        except Exception as exc:
            son_hata = exc
            if deneme < 2:
                time.sleep(1.5 * (deneme + 1))
    raise son_hata


def _normalize_text(text):
    value = "" if text is None else str(text)
    value = value.translate(TR_CHAR_MAP)
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", value).strip().lower()


def _parse_period_start(period_text):
    parts = str(period_text).strip().split()
    if len(parts) != 2:
        raise ValueError(f"Donem cozumlenemedi: {period_text}")
    ay = TR_AYLAR.get(_normalize_text(parts[0]))
    yil = int(parts[1])
    if ay is None:
        raise ValueError(f"Ay cozumlenemedi: {period_text}")
    return pd.Timestamp(year=yil, month=ay, day=1)


def _load_existing_sales():
    if not CSV_DOSYA.exists():
        return pd.DataFrame(columns=["Tarih"] + KONUT_SATIS_KOLONLARI)
    try:
        mevcut = pd.read_csv(CSV_DOSYA)
    except Exception:
        return pd.DataFrame(columns=["Tarih"] + KONUT_SATIS_KOLONLARI)

    mevcut_kolonlar = [c for c in ["Tarih"] + KONUT_SATIS_KOLONLARI if c in mevcut.columns]
    if "Tarih" not in mevcut_kolonlar or len(mevcut_kolonlar) == 1:
        return pd.DataFrame(columns=["Tarih"] + KONUT_SATIS_KOLONLARI)

    mevcut = mevcut[mevcut_kolonlar].copy()
    mevcut["Tarih"] = pd.to_datetime(mevcut["Tarih"], errors="coerce")
    mevcut = mevcut.dropna(subset=["Tarih"]).sort_values("Tarih")
    for kol in KONUT_SATIS_KOLONLARI:
        if kol in mevcut.columns:
            mevcut[kol] = pd.to_numeric(mevcut[kol], errors="coerce")
    return mevcut


def _latest_press_detail(press_title, max_pages=6):
    candidates = []
    for page in range(1, max_pages + 1):
        payload = _api_get_json(f"/api/tr/press?page={page}")
        items = payload.get("data") or []
        candidates.extend(
            item for item in items
            if item.get("title") == press_title and item.get("id")
        )
        if candidates:
            break
    if not candidates:
        raise ValueError(f"Press bulteni bulunamadi: {press_title}")
    candidates.sort(key=lambda item: int(item["id"]), reverse=True)
    detail_payload = _api_get_json(f"/api/tr/press/{candidates[0]['id']}")
    return detail_payload["data"]


def _parse_js_like_options(option_text):
    raw = html.unescape(option_text)
    raw = re.sub(r"\bnull\b", "None", raw)
    raw = re.sub(r"\btrue\b", "True", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\bfalse\b", "False", raw, flags=re.IGNORECASE)
    return ast.literal_eval(raw)


def _extract_chart_options(content):
    matches = re.finditer(
        r'data-name="(?P<name>[^"]+)".*?data-options="(?P<options>\{.*?\})">\s*Yükleniyor',
        content,
        flags=re.S,
    )
    charts = {}
    for match in matches:
        charts[match.group("name")] = _parse_js_like_options(match.group("options"))
    if not charts:
        raise ValueError("Press iceriginde grafik verisi bulunamadi")
    return charts


def _chart_by_name(charts, include_tokens, exclude_tokens=None):
    exclude_tokens = exclude_tokens or []
    for chart in charts.values():
        name = _normalize_text(chart.get("name"))
        if all(token in name for token in include_tokens) and not any(token in name for token in exclude_tokens):
            return chart
    raise ValueError(f"Grafik bulunamadi: include={include_tokens}, exclude={exclude_tokens}")


def _frame_from_single_series_chart(chart, column_name):
    labels = chart.get("labels") or []
    if not labels:
        return pd.DataFrame(columns=["Tarih", column_name])

    frame = pd.DataFrame({
        "Tarih": pd.to_datetime(labels, format="%Y-%m", errors="coerce")
    })
    if frame["Tarih"].isna().all():
        return pd.DataFrame(columns=["Tarih", column_name])

    series_list = chart.get("data") or []
    if not series_list:
        raise ValueError(f"Grafikte seri bulunamadi: {chart.get('name')}")

    values = pd.to_numeric(pd.Series(series_list[0].get("data") or []), errors="coerce")
    frame[column_name] = values.reindex(range(len(frame))).values
    return frame.dropna(subset=["Tarih"])


def _frame_from_named_series(chart, column_name, label_tokens):
    labels = chart.get("labels") or []
    if not labels:
        return pd.DataFrame(columns=["Tarih", column_name])

    frame = pd.DataFrame({
        "Tarih": pd.to_datetime(labels, format="%Y-%m", errors="coerce")
    })
    if frame["Tarih"].isna().all():
        return pd.DataFrame(columns=["Tarih", column_name])

    for seri in chart.get("data") or []:
        label = _normalize_text(seri.get("label"))
        if all(token in label for token in label_tokens):
            values = pd.to_numeric(pd.Series(seri.get("data") or []), errors="coerce")
            frame[column_name] = values.reindex(range(len(frame))).values
            return frame.dropna(subset=["Tarih"])

    raise ValueError(f"Istenen seri bulunamadi: {label_tokens}")


def _merge_monthly_frames(*frames):
    clean_frames = [frame for frame in frames if frame is not None and not frame.empty]
    if not clean_frames:
        return pd.DataFrame(columns=["Tarih"])

    merged = clean_frames[0].copy()
    for frame in clean_frames[1:]:
        merged = merged.merge(frame, on="Tarih", how="outer")

    merged["Tarih"] = pd.to_datetime(merged["Tarih"], errors="coerce")
    return (
        merged.dropna(subset=["Tarih"])
        .sort_values("Tarih")
        .drop_duplicates(subset=["Tarih"], keep="last")
        .reset_index(drop=True)
    )


def _validate_latest_period(frame, period_text):
    if frame.empty:
        raise ValueError("Bos veri seti dondu")
    period_start = _parse_period_start(period_text)
    son_donem = frame["Tarih"].dropna().max()
    if son_donem is None or son_donem.to_period("M") != period_start.to_period("M"):
        raise ValueError(f"Press donemi uyusmuyor: period={period_text} veri={son_donem}")


def _sales_frame_from_chart(chart):
    labels = chart.get("labels") or []
    if not labels:
        return pd.DataFrame()

    frame = pd.DataFrame({
        "Tarih": pd.to_datetime(labels, format="%Y-%m", errors="coerce")
    })
    if frame["Tarih"].isna().all():
        return pd.DataFrame()

    for seri in chart.get("data") or []:
        label = _normalize_text(seri.get("label"))
        values = pd.to_numeric(pd.Series(seri.get("data") or []), errors="coerce")
        values = values.reindex(range(len(frame)))

        if "ilk el" in label:
            frame["Satis_IlkEl"] = values.values
        elif "ikinci el" in label:
            frame["Satis_IkinciEl"] = values.values
        elif "ipotekli" in label:
            frame["Satis_Ipotekli"] = values.values

    return frame.dropna(subset=["Tarih"])


def _load_tuik_sales_series():
    detail = _latest_press_detail(KONUT_PRESS_TITLE)
    charts = _extract_chart_options(detail.get("content") or "")

    pieces = []
    for chart in charts.values():
        frame = _sales_frame_from_chart(chart)
        if not frame.empty:
            pieces.append(frame)

    if not pieces:
        raise ValueError("TUİK press grafikleri icinden satis serisi ayiklanamadi")

    satis = pieces[0]
    for piece in pieces[1:]:
        ek_kolonlar = [c for c in piece.columns if c != "Tarih" and c not in satis.columns]
        if ek_kolonlar:
            satis = satis.merge(piece[["Tarih"] + ek_kolonlar], on="Tarih", how="outer")

    for kol in ["Satis_IlkEl", "Satis_IkinciEl", "Satis_Ipotekli"]:
        if kol not in satis.columns:
            raise ValueError(f"TUİK press serisinde kolon eksik: {kol}")

    satis["Satis_Toplam"] = satis["Satis_IlkEl"].fillna(0) + satis["Satis_IkinciEl"].fillna(0)
    satis = satis[["Tarih"] + KONUT_SATIS_KOLONLARI].sort_values("Tarih").drop_duplicates("Tarih", keep="last")

    _validate_latest_period(satis, detail["period"])
    return satis


def _load_insaat_maliyet_series():
    detail = _latest_press_detail(INSAAT_MALIYET_PRESS_TITLE)
    charts = _extract_chart_options(detail.get("content") or "")
    yillik = _frame_from_single_series_chart(
        _chart_by_name(
            charts,
            include_tokens=["insaat maliyet endeksi", "yillik degisim orani"],
            exclude_tokens=["bina insaati", "bina disi"],
        ),
        "Insaat_Maliyet_Yillik_Degisim",
    )
    aylik = _frame_from_single_series_chart(
        _chart_by_name(
            charts,
            include_tokens=["insaat maliyet endeksi", "aylik degisim oranlari"],
        ),
        "Insaat_Maliyet_Aylik_Degisim",
    )
    maliyet = _merge_monthly_frames(yillik, aylik)
    _validate_latest_period(maliyet, detail["period"])
    return maliyet


def _load_insaat_uretim_series():
    detail = _latest_press_detail(INSAAT_URETIM_PRESS_TITLE)
    charts = _extract_chart_options(detail.get("content") or "")
    yillik = _frame_from_single_series_chart(
        _chart_by_name(
            charts,
            include_tokens=["insaat uretim endeksi", "yillik degisim"],
        ),
        "Insaat_Uretim_Yillik_Degisim",
    )
    aylik = _frame_from_single_series_chart(
        _chart_by_name(
            charts,
            include_tokens=["insaat uretim endeksi", "aylik degisim"],
        ),
        "Insaat_Uretim_Aylik_Degisim",
    )
    uretim = _merge_monthly_frames(yillik, aylik)
    _validate_latest_period(uretim, detail["period"])
    return uretim


def _load_insaat_guven_series():
    detail = _latest_press_detail(INSAAT_GUVEN_PRESS_TITLE)
    charts = _extract_chart_options(detail.get("content") or "")
    guven = _frame_from_named_series(
        _chart_by_name(
            charts,
            include_tokens=["guven endeksleri"],
        ),
        "Insaat_Guven_Endeks",
        label_tokens=["insaat sektoru"],
    )
    _validate_latest_period(guven, detail["period"])
    return guven


def _load_resmi_insaat_series():
    return _merge_monthly_frames(
        _load_insaat_maliyet_series(),
        _load_insaat_uretim_series(),
        _load_insaat_guven_series(),
    )


def main():
    bitis = datetime.now().strftime("%d-%m-%Y")

    log.info("=" * 60)
    log.info("KONUT GÜNCELLEMESİ")
    log.info("=" * 60)

    parcalar = []

    # ── 1) Fiyat endeksleri — düzey + aylık % + yıllık % ──
    fe_kodlar = list(KONUT_FE_SERILER.keys())
    log.info(f"\n1/6  Fiyat Endeksleri (düzey) — {len(fe_kodlar)} seri...")
    df_fe_d = evds_cek(fe_kodlar, KONUT_BASLANGIC, bitis)
    df_fe_d = _rename(df_fe_d, KONUT_FE_SERILER, "_duzey")
    log.info(f"     ✓ {len(df_fe_d)} satır")
    time.sleep(1)

    log.info("2/6  Fiyat Endeksleri (aylık %)...")
    df_fe_a = evds_cek(fe_kodlar, KONUT_BASLANGIC, bitis, formulas=1)
    df_fe_a = _rename(df_fe_a, KONUT_FE_SERILER, "_aylik", "-1")
    log.info(f"     ✓ {len(df_fe_a)} satır")
    time.sleep(1)

    log.info("3/6  Fiyat Endeksleri (yıllık %)...")
    df_fe_y = evds_cek(fe_kodlar, KONUT_BASLANGIC, bitis, formulas=3)
    df_fe_y = _rename(df_fe_y, KONUT_FE_SERILER, "_yillik", "-3")
    log.info(f"     ✓ {len(df_fe_y)} satır")
    time.sleep(1)

    # Birleştir
    df_fe = df_fe_d.merge(df_fe_a, on="Tarih", how="outer").merge(df_fe_y, on="Tarih", how="outer")
    parcalar.append(df_fe)

    # ── 2) Düzey veriler (satış, birim fiyat/kira) ────────
    duzey_kodlar = list(KONUT_DUZEY_SERILER.keys())
    log.info(f"\n4/6  Satış & Birim veriler — {len(duzey_kodlar)} seri...")
    df_duzey = evds_cek(duzey_kodlar, KONUT_BASLANGIC, bitis, frequency=5)
    df_duzey = _rename(df_duzey, KONUT_DUZEY_SERILER)

    mevcut_satis = _load_existing_sales()
    if not mevcut_satis.empty:
        log.info(f"     Mevcut satış geçmişi korundu — {len(mevcut_satis)} satır")

    try:
        tuik_satis = _load_tuik_sales_series()
        log.info(
            "     TÜİK press satış serisi eklendi — "
            f"{len(tuik_satis)} satır ({tuik_satis['Tarih'].max().strftime('%Y-%m')})"
        )
    except Exception as exc:
        log.warning(f"     ! TÜİK press satış serisi alınamadı: {exc}")
        tuik_satis = pd.DataFrame(columns=["Tarih"] + KONUT_SATIS_KOLONLARI)

    if not mevcut_satis.empty or not tuik_satis.empty:
        satis_gecmisi = pd.concat([mevcut_satis, tuik_satis], ignore_index=True)
        satis_gecmisi["Tarih"] = pd.to_datetime(satis_gecmisi["Tarih"], errors="coerce")
        satis_gecmisi = (
            satis_gecmisi.sort_values("Tarih")
            .dropna(subset=["Tarih"])
            .drop_duplicates(subset=["Tarih"], keep="last")
            .reset_index(drop=True)
        )
        df_duzey["Tarih"] = pd.to_datetime(df_duzey["Tarih"], errors="coerce")
        df_duzey = df_duzey.drop(columns=KONUT_SATIS_KOLONLARI, errors="ignore")
        df_duzey = df_duzey.merge(satis_gecmisi, on="Tarih", how="outer")

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
    log.info(f"\n5/6  Yapı Ruhsatları — {len(ruhsat_kodlar)} seri...")
    df_ruhsat = evds_cek(ruhsat_kodlar, KONUT_BASLANGIC, bitis)
    df_ruhsat = _rename(df_ruhsat, KONUT_RUHSAT_SERILER)
    log.info(f"     ✓ {len(df_ruhsat)} satır")
    parcalar.append(df_ruhsat)

    # ── 5) Resmi TÜİK inşaat serileri ────────────────────
    log.info("\n6/6  Resmi TÜİK İnşaat Serileri...")
    try:
        df_insaat = _load_resmi_insaat_series()
        log.info(
            "     ✓ %s satır, son dönem %s",
            len(df_insaat),
            df_insaat["Tarih"].max().strftime("%Y-%m"),
        )
    except Exception as exc:
        log.warning(f"     ! Resmi TÜİK inşaat serileri alınamadı: {exc}")
        df_insaat = pd.DataFrame(columns=["Tarih"] + INSAAT_KOLONLARI)
    parcalar.append(df_insaat)

    # ── Hepsini birleştir ─────────────────────────────────
    log.info("\nBirleştiriliyor...")
    df = parcalar[0]
    for p in parcalar[1:]:
        df = df.merge(p, on="Tarih", how="outer")

    df = df.sort_values("Tarih").reset_index(drop=True)
    df = csv_gecmisi_koru(CSV_DOSYA, df)

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
