# -*- coding: utf-8 -*-
"""
SAI MANAGER DASHBOARD
====================
streamlit run sai_makro_dashboard.py --server.port 8503
"""

import base64
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Sai Manager",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── RENK ──────────────────────────────────────────────────
NAVY_900 = "#0B1F3B"
NAVY_800 = "#0F2B4C"
NAVY_700 = "#1E3A8A"
BLUE_600 = "#2563EB"
BLUE_500 = "#3B82F6"
BLUE_400 = "#60A5FA"
BLUE_300 = "#93C5FD"
SLATE_500 = "#64748B"
RED_500 = "#EF4444"
BG = "#F8FAFC"
GRID = "#E2E8F0"
BLACK = "#000000"
MIN_GOSTERIM_YIL = 2022
SON_GOSTERIM_HAFTA = 20
AY_TICK_FONT = 10
CEYREKSEL_BASLANGIC = pd.Timestamp("2020-01-01")
TR_AY_KISA = {
    1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz",
    7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"
}

# ── CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; }

    section[data-testid="stSidebar"] {
        background-color: #0B1F3B;
        min-width: 280px;
        max-width: 320px;
    }
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown li,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stCheckbox label span,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        color: #E2E8F0 !important;
    }

    section[data-testid="stSidebar"] .stCheckbox label p {
        color: #CBD5E1 !important;
        font-size: 13px !important;
    }

    .modul-baslik {
        font-size: 11px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }

    .stTabs [data-baseweb="tab"] {
        opacity: 1 !important;
    }

    .stTabs [data-baseweb="tab"] p {
        color: #0B1F3B !important;
        font-weight: 700 !important;
    }

    .stTabs [aria-selected="true"] p {
        color: #1E3A8A !important;
    }
</style>
""", unsafe_allow_html=True)

# ── VERİ YÜKLEME ─────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd()
DATA_DIR = SCRIPT_DIR / "makro_data"
HAVA_TRAFIK_DIR = SCRIPT_DIR / "hava trafik"
JET_YAKITI_DIR = SCRIPT_DIR / "jet yakıtı"
LOGO_PATH = SCRIPT_DIR / "assets" / "sai_manager_19_nis.png"


def csv_cache_key(filename):
    csv = DATA_DIR / filename
    return csv.stat().st_mtime_ns if csv.exists() else 0


def excel_cache_key(filename):
    excel = HAVA_TRAFIK_DIR / filename
    return excel.stat().st_mtime_ns if excel.exists() else 0


def jet_cache_key(filename):
    csv = JET_YAKITI_DIR / filename
    return csv.stat().st_mtime_ns if csv.exists() else 0

try:
    from config import (
        TUFE_SERILER, UFE_SERILER, YSA_MENU, KONUT_MENU,
        KK_MENU, KK_SEKTOR_MAP, KK_GERCEK, KK_MA, KK_YOY, KK_ANA_SEKTORLER,
    )
except ImportError:
    TUFE_SERILER = {}
    UFE_SERILER = {}
    YSA_MENU = []
    KONUT_MENU = []
    KK_MENU = []
    KK_SEKTOR_MAP = {}
    KK_GERCEK = []
    KK_MA = 13
    KK_YOY = 52
    KK_ANA_SEKTORLER = []

TUFE_KALEMLER = list(TUFE_SERILER.values()) if TUFE_SERILER else []
UFE_KALEMLER = list(UFE_SERILER.values()) if UFE_SERILER else []

@st.cache_data(ttl=3600)
def tufe_yukle(_cache_key):
    csv = DATA_DIR / "tufe.csv"
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    if "Tarih" in df.columns:
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
    return df

@st.cache_data(ttl=3600)
def ufe_yukle(_cache_key):
    csv = DATA_DIR / "ufe.csv"
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    if "Tarih" in df.columns:
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
    return df

@st.cache_data(ttl=3600)
def ysa_yukle(_cache_key):
    csv = DATA_DIR / "ysa.csv"
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    if "Tarih" in df.columns:
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
    return df

@st.cache_data(ttl=3600)
def konut_yukle(_cache_key):
    csv = DATA_DIR / "konut.csv"
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    if "Tarih" in df.columns:
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
    return df

@st.cache_data(ttl=3600)
def kredi_karti_yukle(_cache_key):
    """Ham CSV oku, türev kolonları hesapla."""
    csv = DATA_DIR / "kredi_karti.csv"
    if not csv.exists():
        return None
    df = pd.read_csv(csv)
    if "Tarih" in df.columns:
        df["Tarih"] = pd.to_datetime(df["Tarih"], errors="coerce")
    df = df.sort_values("Tarih").reset_index(drop=True)

    kt_cols = [c for c in df.columns if c.startswith("KT")]
    ka_cols = [c for c in df.columns if c.startswith("KA")]

    # Numerik dönüşüm
    for c in kt_cols + ka_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.ffill().fillna(0)

    # MA (13H)
    for c in kt_cols:
        df[f"{c}_MA"] = df[c].rolling(KK_MA).mean()
    for c in ka_cols:
        df[f"{c}_MA"] = df[c].rolling(KK_MA).mean()

    # YoY (52H)
    for c in kt_cols:
        df[f"{c}_yoy"] = df[c].pct_change(KK_YOY) * 100

    # Sepet (TL) = (Bin TL * 1000) / adet
    for kt in kt_cols:
        ka = kt.replace("KT", "KA")
        if ka in df.columns:
            df[f"Sepet_{kt}"] = (df[kt] * 1000) / df[ka].replace(0, np.nan)
            df[f"Sepet_{kt}_MA"] = df[f"Sepet_{kt}"].rolling(KK_MA).mean()

    # Çeyrek
    df["Ceyrek"] = df["Tarih"].dt.to_period("Q").astype(str)

    return df


@st.cache_data(ttl=3600)
def thyao_trafik_yukle(_cache_key):
    excel = HAVA_TRAFIK_DIR / "thyao_trafik_verileri.xlsx"
    if not excel.exists():
        return None

    raw = pd.read_excel(excel, sheet_name="toplu")
    if raw.empty or raw.shape[0] < 12:
        return None

    tarih_hucreleri = raw.iloc[1, 1:]
    tarihler = pd.to_datetime(tarih_hucreleri.astype(str), format="%Y/%m", errors="coerce")
    gecerli_mask = ~tarihler.isna()
    if not gecerli_mask.any():
        return None

    veri = pd.DataFrame({"Tarih": pd.to_datetime(tarihler[gecerli_mask]).to_list()})
    secili_kolonlar = [raw.columns[i + 1] for i, ok in enumerate(gecerli_mask) if ok]
    metric_rows = {
        "ASK_000": 3,
        "Ucretli_Yolcu_Km_000": 4,
        "Doluluk_Orani": 5,
        "Yolcu_Sayisi": 6,
        "Kargo_Posta_Ton": 8,
        "Ucak_Sayisi": 9,
        "Koltuk_Kapasitesi": 10,
    }

    for yeni_ad, row_idx in metric_rows.items():
        seri = pd.to_numeric(raw.loc[row_idx, secili_kolonlar], errors="coerce")
        veri[yeni_ad] = seri.to_numpy()

    veri = veri.dropna(subset=["Tarih"]).sort_values("Tarih").reset_index(drop=True)
    return veri


def _temiz_havacilik_metin(value):
    text = str(value or "").strip()
    text = text.encode("ascii", "ignore").decode()
    text = " ".join(text.split())
    return text


def _ay_metnini_tarihe_cevir(value):
    text = _temiz_havacilik_metin(value).lower()
    parcalar = text.split()
    if len(parcalar) < 2:
        return pd.NaT

    ay_map = {
        "oca": 1, "sub": 2, "mar": 3, "nis": 4, "may": 5, "haz": 6,
        "tem": 7, "agu": 8, "eyl": 9, "eki": 10, "kas": 11, "ara": 12,
    }
    ay = ay_map.get(parcalar[0][:3])
    yil = pd.to_numeric(parcalar[1], errors="coerce")
    if ay is None or pd.isna(yil):
        return pd.NaT
    return pd.Timestamp(year=int(yil), month=int(ay), day=1)


def _genel_bakis_tablosu_yukle(excel_adi):
    excel = HAVA_TRAFIK_DIR / excel_adi
    if not excel.exists():
        return None

    raw = pd.read_excel(excel, sheet_name="genel_bakis", header=None)
    if raw.empty:
        return None

    baslangic = None
    for idx, value in enumerate(raw.iloc[1].tolist()):
        if _temiz_havacilik_metin(value).lower() == "donem":
            baslangic = idx
            break
    if baslangic is None:
        return None

    blok = raw.iloc[2:, baslangic:].copy().reset_index(drop=True)
    blok = blok.dropna(axis=1, how="all")
    kolonlar = [_temiz_havacilik_metin(c) for c in raw.iloc[1, baslangic:baslangic + blok.shape[1]].tolist()]
    blok.columns = kolonlar
    blok = blok.rename(columns={blok.columns[0]: "Donem"})
    blok["Tarih"] = blok["Donem"].apply(_ay_metnini_tarihe_cevir)
    blok = blok.dropna(subset=["Tarih"]).copy()

    for col in blok.columns:
        if col not in {"Donem", "Tarih"}:
            blok[col] = pd.to_numeric(blok[col], errors="coerce")

    return blok.sort_values("Tarih").reset_index(drop=True)


@st.cache_data(ttl=3600)
def pgsus_trafik_yukle(_cache_key):
    return _genel_bakis_tablosu_yukle("pgsus_trafik_verileri.xlsx")


def _tavhl_yurtdisi_aylik_yukle():
    excel = HAVA_TRAFIK_DIR / "tavhl_trafik_verileri.xlsx"
    if not excel.exists():
        return pd.DataFrame()

    xl = pd.ExcelFile(excel)
    detail_targets = {
        "milas - bodrum": "Milas Bodrum Yolcu",
        "gazipasa alanya": "Gazipasa Alanya Yolcu",
        "almaty": "Almaty Yolcu",
        "georgia / grcistan": "Gurcistan Yolcu",
        "madinah / medine": "Medine Yolcu",
        "tunisia / tunus": "Tunus Yolcu",
        "north macedonia / kuzey makedonya": "Kuzey Makedonya Yolcu",
        "zagreb": "Zagreb Yolcu",
    }
    rows = []
    for sh in xl.sheet_names:
        sh_text = str(sh)
        if len(sh_text) != 4 or not sh_text.isdigit():
            continue

        month = int(sh_text[:2])
        year = 2000 + int(sh_text[2:])
        if month < 1 or month > 12:
            continue

        raw = pd.read_excel(excel, sheet_name=sh, header=None)
        if raw.empty:
            continue

        first_col = raw.iloc[:, 0].fillna("").astype(str).map(_temiz_havacilik_metin).str.lower()
        yolcu_start_candidates = first_col[first_col.str.contains("passengers / yolcu", na=False)].index.tolist()
        ucus_start_candidates = first_col[first_col.str.contains("air traffic movements / ucus sayisi", na=False)].index.tolist()
        yolcu_start = (yolcu_start_candidates[0] + 1) if yolcu_start_candidates else 0
        yolcu_end = ucus_start_candidates[0] if ucus_start_candidates else len(raw)
        yolcu_labels = first_col.iloc[yolcu_start:yolcu_end]

        record = {"Tarih": pd.Timestamp(year=year, month=month, day=1), "TAV Yurtdisi Yolcu": np.nan, "TAV Yurtici Yolcu": np.nan}
        for col_name in detail_targets.values():
            record[col_name] = np.nan

        idxs = yolcu_labels[yolcu_labels.str.contains("tav total", na=False)].index.tolist()
        if idxs:
            idx = idxs[0]
            record["TAV Yurtdisi Yolcu"] = pd.to_numeric(raw.iloc[idx + 1, 2], errors="coerce") if idx + 1 < len(raw) else np.nan
            record["TAV Yurtici Yolcu"] = pd.to_numeric(raw.iloc[idx + 2, 2], errors="coerce") if idx + 2 < len(raw) else np.nan

        for row_idx, label in yolcu_labels.items():
            if label in detail_targets:
                record[detail_targets[label]] = pd.to_numeric(raw.iloc[row_idx, 2], errors="coerce")

        rows.append(record)

    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values("Tarih").drop_duplicates(subset=["Tarih"], keep="last")


@st.cache_data(ttl=3600)
def tavhl_trafik_yukle(_cache_key):
    df = _genel_bakis_tablosu_yukle("tavhl_trafik_verileri.xlsx")
    detay = _tavhl_yurtdisi_aylik_yukle()
    if df is None or df.empty:
        return detay if not detay.empty else None
    if detay.empty:
        return df
    return df.merge(detay, on="Tarih", how="left")


@st.cache_data(ttl=3600)
def jet_yakiti_yukle(_cache_key):
    csv = JET_YAKITI_DIR / "jet_yakiti_model_haftalik_fred.csv"
    if not csv.exists():
        return None

    df = pd.read_csv(csv)
    if "observation_date" not in df.columns:
        return None

    df["Tarih"] = pd.to_datetime(df["observation_date"], errors="coerce")
    veri_kollari = [
        "jet_fuel_usd_per_gallon",
        "brent_usd_per_barrel",
        "jet_crack_usd_per_barrel",
        "jet_minus_ulsd_usd_per_gallon",
    ]
    for col in veri_kollari:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["Tarih"]).sort_values("Tarih").reset_index(drop=True)


def _ay_etiket(tarihler):
    return [f"{TR_AY_KISA[pd.Timestamp(t).month]} {str(pd.Timestamp(t).year)[2:]}" for t in tarihler]


def _son_ay_baslangici(tarihler, min_yil=MIN_GOSTERIM_YIL):
    seri = pd.to_datetime(pd.Series(tarihler), errors="coerce").dropna()
    if seri.empty:
        return None
    ilk_yil = int(seri.min().year)
    baslangic_yil = max(ilk_yil, min_yil)
    return pd.Timestamp(baslangic_yil, 1, 1)


def _son_25_ay(df, subset=None, tarih_kol="Tarih"):
    if df is None or df.empty or tarih_kol not in df.columns:
        return pd.DataFrame()
    tail = df.copy()
    if subset:
        tail = tail.dropna(subset=subset)
    if tail.empty:
        return tail
    ilk_tarih = _son_ay_baslangici(tail[tarih_kol])
    if ilk_tarih is None:
        return tail.iloc[0:0]
    tarihler = pd.to_datetime(tail[tarih_kol], errors="coerce")
    return tail.loc[tarihler >= ilk_tarih].copy()


def _2020den_bugune(df, subset=None, tarih_kol="Tarih"):
    if df is None or df.empty or tarih_kol not in df.columns:
        return pd.DataFrame()
    tail = df.copy()
    if subset:
        tail = tail.dropna(subset=subset)
    if tail.empty:
        return tail
    tarihler = pd.to_datetime(tail[tarih_kol], errors="coerce")
    return tail.loc[tarihler >= CEYREKSEL_BASLANGIC].copy()


def _uygula_kategorik_ay_xaxis(fig, labels, font_color=BLACK, size=AY_TICK_FONT):
    label_list = list(labels)
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=label_list,
        tickmode="array",
        tickvals=label_list,
        ticktext=label_list,
        tickangle=-45,
        tickfont=dict(size=size, color=font_color),
        showgrid=False,
        automargin=True,
    )


def _uygula_tarih_ay_xaxis(fig, tarihler, font_color=BLACK, size=AY_TICK_FONT):
    seri = pd.to_datetime(pd.Series(tarihler), errors="coerce").dropna()
    if seri.empty:
        return
    ilk = seri.min().to_period("M").to_timestamp()
    son = seri.max().to_period("M").to_timestamp()
    tickler = pd.date_range(ilk, son, freq="MS")
    fig.update_xaxes(
        tickmode="array",
        tickvals=list(tickler),
        ticktext=_ay_etiket(tickler),
        tickangle=-45,
        tickfont=dict(size=size, color=font_color),
        showgrid=False,
        automargin=True,
    )


def _hafta_etiket(tarihler):
    return [pd.Timestamp(t).strftime("%d.%m.%y") for t in tarihler]


def _son_n_hafta(df, subset=None, tarih_kol="Tarih", hafta_sayisi=SON_GOSTERIM_HAFTA):
    if df is None or df.empty or tarih_kol not in df.columns:
        return pd.DataFrame()
    tail = df.copy()
    if subset:
        tail = tail.dropna(subset=subset)
    if tail.empty:
        return tail
    tail[tarih_kol] = pd.to_datetime(tail[tarih_kol], errors="coerce")
    tail = tail.dropna(subset=[tarih_kol]).sort_values(tarih_kol)
    return tail.tail(hafta_sayisi).copy()


def _uygula_tarih_hafta_xaxis(fig, tarihler, font_color=BLACK, size=AY_TICK_FONT):
    seri = pd.to_datetime(pd.Series(tarihler), errors="coerce").dropna().sort_values()
# -- HAVACILIK GRAFIKLER --
HAVACILIK_THYAO_GRAFIKLER = [
    {"title": "THYAO - Arz Edilen Koltuk Km (000)", "col": "ASK_000", "quarterly": "sum", "format": "integer"},
    {"title": "THYAO - Ucretli Yolcu Km (000)", "col": "Ucretli_Yolcu_Km_000", "quarterly": "sum", "format": "integer"},
    {"title": "THYAO - Yolcu Doluluk Orani", "col": "Doluluk_Orani", "quarterly": "ratio_of_sums", "numer_col": "Ucretli_Yolcu_Km_000", "denom_col": "ASK_000", "format": "percent"},
    {"title": "THYAO - Yolcu Sayisi", "col": "Yolcu_Sayisi", "quarterly": "sum", "format": "integer"},
    {"title": "THYAO - Kargo + Posta (Ton)", "col": "Kargo_Posta_Ton", "quarterly": "sum", "format": "integer"},
    {"title": "THYAO - Koltuk Kapasitesi", "col": "Koltuk_Kapasitesi", "quarterly": "mean", "format": "integer"},
]

HAVACILIK_PGSUS_GRAFIKLER = [
    {"title": "PGSUS - Misafir Sayisi (mn)", "col": "Misafir Sayisi (mn)", "quarterly": "sum", "format": "decimal1"},
    {"title": "PGSUS - Konma", "col": "Konma", "quarterly": "sum", "format": "integer"},
    {"title": "PGSUS - Koltuk Sayisi (mn)", "col": "Koltuk Sayisi (mn)", "quarterly": "sum", "format": "decimal1"},
    {"title": "PGSUS - Doluluk Orani", "col": "Doluluk Orani", "quarterly": "mean", "format": "percent"},
    {"title": "PGSUS - ASK (mln km)", "col": "ASK (mln km)", "quarterly": "sum", "format": "decimal1"},
]

HAVACILIK_TAVHL_GRAFIKLER = [
    {"title": "TAVHL - TAV Toplam Yolcu", "col": "TAV Toplam Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - TAV Yurtdisi Yolcu", "col": "TAV Yurtdisi Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - TAV Yurtici Yolcu", "col": "TAV Yurtici Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Antalya Yolcu", "col": "Antalya Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Izmir Yolcu", "col": "Izmir Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Ankara Yolcu", "col": "Ankara Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Milas Bodrum Yolcu", "col": "Milas Bodrum Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Gazipasa Alanya Yolcu", "col": "Gazipasa Alanya Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Almaty Yolcu", "col": "Almaty Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Gurcistan Yolcu", "col": "Gurcistan Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Medine Yolcu", "col": "Medine Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Tunus Yolcu", "col": "Tunus Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Kuzey Makedonya Yolcu", "col": "Kuzey Makedonya Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - Zagreb Yolcu", "col": "Zagreb Yolcu", "quarterly": "sum", "format": "integer"},
    {"title": "TAVHL - TAV Toplam Ucus", "col": "TAV Toplam Ucus", "quarterly": "sum", "format": "integer"},
]

HAVACILIK_JET_GRAFIKLER = [
    {"title": "Jet Yakiti - Fiyat (USD/galon)", "col": "jet_fuel_usd_per_gallon", "quarterly": "mean", "monthly": "mean", "source_freq": "weekly", "format": "decimal2"},
    {"title": "Jet Yakiti - Brent (USD/varil)", "col": "brent_usd_per_barrel", "quarterly": "mean", "monthly": "mean", "source_freq": "weekly", "format": "decimal1"},
    {"title": "Jet Yakiti - Jet Crack (USD/varil)", "col": "jet_crack_usd_per_barrel", "quarterly": "mean", "monthly": "mean", "source_freq": "weekly", "format": "decimal1"},
    {"title": "Jet Yakiti - Jet minus ULSD (USD/galon)", "col": "jet_minus_ulsd_usd_per_gallon", "quarterly": "mean", "monthly": "mean", "source_freq": "weekly", "format": "decimal2"},
]



def _havacilik_aylik_ozet(df, spec):
    temp = df.copy()
    temp["Tarih"] = pd.to_datetime(temp["Tarih"], errors="coerce")
    temp = temp.dropna(subset=["Tarih", spec["col"]]).sort_values("Tarih")
    if temp.empty:
        return pd.DataFrame(columns=["Tarih", spec["col"]])

    if spec.get("source_freq") == "weekly":
        temp["Ay"] = temp["Tarih"].dt.to_period("M")
        method = spec.get("monthly", "mean")
        if method == "sum":
            grouped = temp.groupby("Ay")[spec["col"]].sum(min_count=1)
        else:
            grouped = temp.groupby("Ay")[spec["col"]].mean()
        grouped = grouped.dropna().tail(25)
        return pd.DataFrame({"Tarih": [p.to_timestamp() for p in grouped.index], spec["col"]: grouped.to_numpy()})

    return _son_25_ay(temp, subset=[spec['col']])


def _havacilik_sezonsal_aylik_ozet(df, spec):
    aylik = _havacilik_aylik_ozet(df, spec)
    if aylik.empty:
        return pd.DataFrame(columns=['Tarih', 'Yil', 'AyNo', 'AyIsim', spec['col']])

    aylik = aylik.copy()
    aylik['Tarih'] = pd.to_datetime(aylik['Tarih'], errors='coerce')
    aylik = aylik.dropna(subset=['Tarih', spec['col']]).sort_values('Tarih')
    if aylik.empty:
        return pd.DataFrame(columns=['Tarih', 'Yil', 'AyNo', 'AyIsim', spec['col']])

    aylik['Yil'] = aylik['Tarih'].dt.year
    aylik['AyNo'] = aylik['Tarih'].dt.month
    aylik['AyIsim'] = aylik['AyNo'].map(TR_AY_KISA)
    return aylik[['Tarih', 'Yil', 'AyNo', 'AyIsim', spec['col']]]


def _ceyrek_etiket(periodler):
    return [f"{p.year}Q{p.quarter}" for p in periodler]


def _havacilik_ceyreklik_ozet(df, spec):
    temp = df.copy()
    temp["Tarih"] = pd.to_datetime(temp["Tarih"], errors="coerce")
    temp = temp.dropna(subset=["Tarih"]).sort_values("Tarih")
    temp["Ceyrek"] = temp["Tarih"].dt.to_period("Q")

    method = spec.get("quarterly", "sum")
    if method == "sum":
        grouped = temp.groupby("Ceyrek")[spec["col"]].sum(min_count=1)
    elif method == "mean":
        grouped = temp.groupby("Ceyrek")[spec["col"]].mean()
    elif method == "ratio_of_sums":
        numer_col = spec["numer_col"]
        denom_col = spec["denom_col"]

        def _ratio(group):
            pay = group[numer_col].sum(min_count=1)
            payda = group[denom_col].sum(min_count=1)
            if pd.isna(pay) or pd.isna(payda) or payda == 0:
                return np.nan
            return pay / payda

        grouped = temp.groupby("Ceyrek").apply(_ratio)
    else:
        raise ValueError(f"Unknown quarterly method: {method}")

    grouped = grouped.dropna().tail(9)
    if grouped.empty:
        return pd.DataFrame(columns=["Ceyrek", "Deger"])
    return pd.DataFrame({"Ceyrek": grouped.index.tolist(), "Deger": grouped.to_numpy()})


def havacilik_karsilastirma_grafik(df, spec):
    aylik = _havacilik_sezonsal_aylik_ozet(df, spec)
    ceyreklik = _havacilik_ceyreklik_ozet(df, spec)
    if aylik.empty or ceyreklik.empty:
        return None

    ceyrek_labels = _ceyrek_etiket(ceyreklik['Ceyrek'])
    aylik_renkler = ['#2563EB', '#F97316', '#64748B', '#EAB308', '#14B8A6']
    yillar = sorted(aylik['Yil'].unique(), reverse=True)

    fig = make_subplots(rows=1, cols=2, subplot_titles=('Aylik Dagilim', 'Ceyreklik - Son 9 Ceyrek'), horizontal_spacing=0.10)
    for idx, yil in enumerate(yillar):
        parca = aylik.loc[aylik['Yil'] == yil].sort_values('AyNo')
        renk = aylik_renkler[idx % len(aylik_renkler)]
        fig.add_trace(go.Scatter(x=parca['AyNo'], y=parca[spec['col']], mode='lines+markers', name=str(yil), line=dict(color=renk, width=2.8), marker=dict(size=7, color=renk), customdata=parca['AyIsim'], hovertemplate=f'{yil} / ' + '%{customdata}<br>%{y}<extra></extra>'), row=1, col=1)
    fig.add_trace(go.Scatter(x=ceyrek_labels, y=ceyreklik['Deger'], mode='lines+markers', line=dict(color=NAVY_700, width=2.8), marker=dict(size=6, color=NAVY_700), showlegend=False), row=1, col=2)
    fig.update_layout(title=dict(text=spec['title'], font=dict(size=17, color=NAVY_900), x=0.5, xanchor='center'), paper_bgcolor='#EEF4FB', plot_bgcolor='#F7FAFE', font=dict(family='Arial', color=NAVY_900, size=13), margin=dict(t=96, b=50, l=44, r=44), height=430, legend=dict(orientation='h', yanchor='bottom', y=1.03, xanchor='left', x=0.02, bgcolor='rgba(255,255,255,0.85)', bordercolor='#D6E0EF', borderwidth=1, font=dict(size=11, color=NAVY_900)))
    fig.update_annotations(font=dict(size=13, color=NAVY_900))
    fig.update_xaxes(tickmode='array', tickvals=list(range(1, 13)), ticktext=[str(i) for i in range(1, 13)], range=[0.7, 12.3], tickangle=0, tickfont=dict(size=11, color=NAVY_900), showgrid=False, automargin=True, row=1, col=1)
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=11, color=NAVY_900), showgrid=False, automargin=True, row=1, col=2)
    fig.update_yaxes(gridcolor=GRID, zeroline=True, zerolinecolor=SLATE_500, zerolinewidth=0.8, tickfont=dict(size=11, color=NAVY_900))
    return fig


def havacilik_grafik_grid(grafik_listesi):
    grafik_listesi = [g for g in grafik_listesi if g is not None]
    if not grafik_listesi:
        st.info("Grafik uretilemedi.")
        return
    if len(grafik_listesi) == 1:
        grafik_listesi[0].update_layout(height=500)
        st.plotly_chart(grafik_listesi[0], use_container_width=True)
        return
    for i in range(0, len(grafik_listesi), 2):
        cols = st.columns(2)
        for j in range(2):
            idx = i + j
            if idx < len(grafik_listesi):
                with cols[j]:
                    st.plotly_chart(grafik_listesi[idx], use_container_width=True)


def render_thyao_tab():
    df = thyao_trafik_yukle(excel_cache_key("thyao_trafik_verileri.xlsx"))
    if df is None or df.empty:
        st.warning("THYAO trafik verisi bulunamadi.")
        return

    st.caption("Kaynak: hava trafik/thyao_trafik_verileri.xlsx")
    havacilik_grafik_grid([havacilik_karsilastirma_grafik(df, spec) for spec in HAVACILIK_THYAO_GRAFIKLER])
    st.caption("Ceyreklik gorunum mevcut ceyrek dahil son 9 ceyregi gosterir. Akim metriklerinde 3 aylik toplam, doluluk oraninda ucretli yolcu km / arz edilen koltuk km, koltuk kapasitesinde uc aylik ortalama kullanilir.")


def render_pgsus_tab():
    df = pgsus_trafik_yukle(excel_cache_key("pgsus_trafik_verileri.xlsx"))
    if df is None or df.empty:
        st.warning("PGSUS trafik verisi bulunamadi.")
        return

    st.caption("Kaynak: hava trafik/pgsus_trafik_verileri.xlsx")
    havacilik_grafik_grid([havacilik_karsilastirma_grafik(df, spec) for spec in HAVACILIK_PGSUS_GRAFIKLER])


def render_tavhl_tab():
    df = tavhl_trafik_yukle(excel_cache_key("tavhl_trafik_verileri.xlsx"))
    if df is None or df.empty:
        st.warning("TAVHL trafik verisi bulunamadi.")
        return

    st.caption("Kaynak: hava trafik/tavhl_trafik_verileri.xlsx")
    havacilik_grafik_grid([havacilik_karsilastirma_grafik(df, spec) for spec in HAVACILIK_TAVHL_GRAFIKLER])


def render_jet_yakiti_tab():
    df = jet_yakiti_yukle(jet_cache_key("jet_yakiti_model_haftalik_fred.csv"))
    if df is None or df.empty:
        st.warning("Jet Yakiti verisi bulunamadi.")
        return

    st.caption("Kaynak: jet yakıtı/jet_yakiti_model_haftalik_fred.csv")
    havacilik_grafik_grid([havacilik_karsilastirma_grafik(df, spec) for spec in HAVACILIK_JET_GRAFIKLER])
    st.caption("Jet yakiti serileri haftalik kaynaktan gelir; aylik ve ceyreklik gorunumlerde ortalama fiyat kullanilir.")
    st.markdown(
        """* Brent, ham petrol referansidir; ULSD, dusuk kukurtlu dizel proxy serisidir.
* Jet Crack, jet yakitinin Brent ham petrole gore farkini gosterir. Yukari gitmesi, jet yakitinin ham petrole gore daha guclu fiyatlandigini anlatir.
* Jet minus ULSD, jet yakitinin ULSD tarafina gore farkini gosterir. Asagi gitmesi, jet fiyati artsa bile ULSD tarafinin daha hizli arttigini ve jet yakitinin dizel tarafina gore geride kaldigini anlatir."""
    )


def tufe_grafik(df, kalem_adi):
    aylik_kol = f"{kalem_adi}_aylik"
    yillik_kol = f"{kalem_adi}_yillik"

    if aylik_kol not in df.columns:
        return None

    tail = _son_25_ay(df, subset=[aylik_kol])
    if tail.empty:
        return None

    x_labels = _ay_etiket(tail["Tarih"])

    aylik = tail[aylik_kol].values
    yillik = tail[yillik_kol].values if yillik_kol in tail.columns else None

    bar_colors = [BLUE_500 if v >= 0 else RED_500 for v in aylik]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=x_labels, y=aylik,
            marker=dict(color=bar_colors, line=dict(color="white", width=0.4)),
            text=[f"{v:.2f}" for v in aylik],
            textposition="outside",
            textfont=dict(size=14, color=NAVY_900),
            name="Aylık %",
            hovertemplate="%{x}<br>Aylık: %{y:.2f}%<extra></extra>",
        ),
        secondary_y=False,
    )

    if yillik is not None:
        fig.add_trace(
            go.Scatter(
                x=x_labels, y=yillik,
                mode="lines+markers",
                line=dict(color=RED_500, width=2.5),
                marker=dict(size=4, color=RED_500),
                name="Yıllık %",
                hovertemplate="%{x}<br>Yıllık: %{y:.2f}%<extra></extra>",
            ),
            secondary_y=True,
        )

    fig.update_layout(
        title=dict(text=kalem_adi, font=dict(size=17, color=NAVY_900), x=0.5),
        paper_bgcolor="white", plot_bgcolor=BG,
        font=dict(family="Arial", color=NAVY_900, size=13),
        margin=dict(t=60, b=50, l=55, r=55),
        height=520,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=12, color="#000000"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1),
        bargap=0.25,
    )

    fig.update_yaxes(
        title_text="Aylık %", secondary_y=False,
        gridcolor=GRID, zeroline=True, zerolinecolor=SLATE_500, zerolinewidth=0.8,
        tickfont=dict(color=BLUE_500, size=12), title_font=dict(color=BLUE_500, size=13),
    )
    fig.update_yaxes(
        title_text="Yıllık %", secondary_y=True,
        showgrid=False, zeroline=False,
        tickfont=dict(color=RED_500, size=12), title_font=dict(color=RED_500, size=13),
    )
    _uygula_kategorik_ay_xaxis(fig, x_labels, font_color=NAVY_900)

    return fig


# ── YSA GRAFİKLER ─────────────────────────────────────────
YSA_RENK = {"Hisse": NAVY_900, "DIBS": NAVY_700, "Ozel_Sektor": BLUE_600, "Eurobond": BLUE_400}
YSA_ISIM = {"Hisse": "Hisse Senedi", "DIBS": "DİBS", "Ozel_Sektor": "Özel Sektör", "Eurobond": "Eurobond"}

def _ysa_ortak_layout():
    return dict(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial", color=BLACK, size=14),
        margin=dict(t=65, b=55, l=65, r=65),
        height=520,
    )

def ysa_bilesen_grafik(df, bilesen_kol, baslik):
    tail = _son_n_hafta(df, subset=[bilesen_kol])
    if tail.empty:
        return None
    x_labels = _hafta_etiket(tail["Tarih"])
    vals = tail[bilesen_kol].values
    bar_colors = [BLUE_500 if v >= 0 else RED_500 for v in vals]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_labels, y=vals,
        marker=dict(color=bar_colors, line=dict(color="white", width=0.5)),
        text=[f"{v:+,.0f}" for v in vals],
        textposition="outside",
        textfont=dict(size=14, color=BLACK),
        hovertemplate="%{x} %{y:+,.0f} mn USD",
    ))
    fig.update_layout(
        **_ysa_ortak_layout(),
        title=dict(text=f"{baslik} (Son {SON_GOSTERIM_HAFTA} Hafta)", font=dict(size=17, color=BLACK), x=0.5),
        showlegend=False, bargap=0.3,
        yaxis=dict(gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK, zerolinewidth=0.8,
                   title_text="mn USD", tickfont=dict(size=14, color=BLACK),
                   title_font=dict(size=14, color=BLACK)),
    )
    _uygula_kategorik_ay_xaxis(fig, x_labels)
    return fig


def ysa_toplam_aylik_grafik(df):
    if "Toplam" not in df.columns:
        return None
    tail = _son_n_hafta(df, subset=["Toplam"])
    if tail.empty:
        return None
    x_labels = _hafta_etiket(tail["Tarih"])
    vals = tail["Toplam"].values
    bar_colors = [BLUE_500 if v >= 0 else RED_500 for v in vals]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x_labels, y=vals, marker=dict(color=bar_colors, line=dict(color="white", width=0.4)),
        text=[f"{v:+,.0f}" for v in vals], textposition="outside", textfont=dict(size=13, color=BLACK),
        name="Haftalik Toplam (mn USD)", hovertemplate="%{x} %{y:+,.0f} mn USD"), secondary_y=False)
    if "Toplam_8H" in tail.columns and tail["Toplam_8H"].notna().any():
        fig.add_trace(go.Scatter(x=x_labels, y=tail["Toplam_8H"].values, mode="lines",
            line=dict(color=BLACK, width=2.5), name="8 Hafta Ort.",
            hovertemplate="%{x} %{y:,.0f} mn USD"), secondary_y=False)
    fig.update_layout(**_ysa_ortak_layout(),
        title=dict(text=f"Toplam Net Akim (Son {SON_GOSTERIM_HAFTA} Hafta, mn USD)", font=dict(size=17, color=BLACK), x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1), bargap=0.3)
    fig.update_yaxes(title_text="mn USD", secondary_y=False, gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK, zerolinewidth=0.8,
                     tickfont=dict(color=BLACK, size=13), title_font=dict(color=BLACK, size=14))
    _uygula_kategorik_ay_xaxis(fig, x_labels)
    return fig


def ysa_kumulatif_grafik(df):
    if "Kumulatif" not in df.columns:
        return None
    tail = _son_n_hafta(df, subset=["Kumulatif"])
    if tail.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tail["Tarih"], y=tail["Kumulatif"], mode="lines+markers",
        line=dict(color=BLUE_600, width=3.5), fill="tozeroy", fillcolor="rgba(37,99,235,0.25)",
        hovertemplate="Kumulatif %{y:+,.0f} mn USD"))
    fig.update_layout(**_ysa_ortak_layout(),
        title=dict(text=f"Kumulatif Net Akim (Son {SON_GOSTERIM_HAFTA} Hafta, mn USD)", font=dict(size=17, color=BLACK), x=0.5),
        showlegend=False, yaxis=dict(gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK, zerolinewidth=0.8,
            title_text="mn USD", tickfont=dict(size=14, color=BLACK), title_font=dict(size=14, color=BLACK)),
        xaxis=dict(showgrid=False, tickfont=dict(size=13, color=BLACK)))
    _uygula_tarih_hafta_xaxis(fig, tail["Tarih"])
    return fig


def ysa_ceyreklik_grafik(df):
    if "Ceyrek" not in df.columns:
        return None
    tail = _2020den_bugune(df, subset=["Hisse", "DIBS", "Ozel_Sektor", "Eurobond"])
    if tail.empty:
        return None
    qg = tail.groupby("Ceyrek")[["Hisse","DIBS","Ozel_Sektor","Eurobond"]].sum().reset_index()
    qg["Toplam"] = qg[["Hisse","DIBS","Ozel_Sektor","Eurobond"]].sum(axis=1)
    fig = go.Figure()
    for kol, renk in YSA_RENK.items():
        isim = YSA_ISIM[kol]
        fig.add_trace(go.Bar(x=qg["Ceyrek"], y=qg[kol], name=isim,
            marker=dict(color=renk, line=dict(color="white", width=0.8)),
            text=[f"{v:+,.0f}" for v in qg[kol]], textposition="inside", textfont=dict(size=12, color="white"),
            hovertemplate="%{x}<br>" + isim + ": %{y:+,.0f} mn $<extra></extra>"))
    fig.update_layout(**_ysa_ortak_layout(), barmode="relative",
        title=dict(text="Çeyreklik Dağılım (2020'den Bugüne, mn $)", font=dict(size=17, color=BLACK), x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1),
        yaxis=dict(gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK, zerolinewidth=0.8,
                   title_text="mn $", tickfont=dict(size=14, color=BLACK), title_font=dict(size=14, color=BLACK)),
        xaxis=dict(showgrid=False, tickfont=dict(size=14, color=BLACK)), bargap=0.25)
    return fig

# ── KONUT GRAFİKLER ───────────────────────────────────────
def _konut_ortak():
    return dict(
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial", color=BLACK, size=14),
        margin=dict(t=80, b=55, l=65, r=65), height=520,
    )

def konut_kfe_grafik(df):
    a_kol, y_kol = "KFE_Turkiye_aylik", "KFE_Turkiye_yillik"
    if a_kol not in df.columns: return None
    tail = _son_25_ay(df, subset=[a_kol])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    aylik = tail[a_kol].values
    yillik = tail[y_kol].values if y_kol in tail.columns else None
    bar_c = [BLUE_500 if v >= 0 else RED_500 for v in aylik]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=aylik, marker=dict(color=bar_c), text=[f"{v:.2f}" for v in aylik],
                         textposition="outside", textfont=dict(size=14, color=BLACK), name="Aylık %",
                         hovertemplate="%{x}<br>Aylık: %{y:.2f}%<extra></extra>"), secondary_y=False)
    if yillik is not None:
        fig.add_trace(go.Scatter(x=x, y=yillik, mode="lines+markers", line=dict(color=RED_500, width=2.5),
                                  marker=dict(size=4), name="Yıllık %",
                                  hovertemplate="%{x}<br>Yıllık: %{y:.2f}%<extra></extra>"), secondary_y=True)
    fig.update_layout(**_konut_ortak(), title=dict(text="Konut Fiyat Endeksi — Türkiye", font=dict(size=17, color=BLACK), x=0.5),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1), bargap=0.25)
    fig.update_yaxes(title_text="Aylık %", secondary_y=False, gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK,
                     tickfont=dict(color=BLUE_600, size=13), title_font=dict(color=BLUE_600, size=14))
    fig.update_yaxes(title_text="Yıllık %", secondary_y=True, showgrid=False,
                     tickfont=dict(color=RED_500, size=13), title_font=dict(color=RED_500, size=14))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig

def konut_satis_grafik(df):
    if "Satis_Toplam" not in df.columns: return None
    tail = _son_25_ay(df, subset=["Satis_Toplam"])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    satis = tail["Satis_Toplam"].values
    ipotekli = tail["Ipotekli_Oran"].values if "Ipotekli_Oran" in tail.columns else None
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=satis/1000, marker_color=BLUE_500, text=[f"{v/1000:.0f}" for v in satis],
                         textposition="outside", textfont=dict(size=13, color=BLACK), name="Toplam (bin)",
                         hovertemplate="%{x}<br>Satış: %{y:,.0f} bin<extra></extra>"), secondary_y=False)
    if ipotekli is not None:
        fig.add_trace(go.Scatter(x=x, y=ipotekli, mode="lines+markers", line=dict(color=RED_500, width=2.5),
                                  marker=dict(size=4), name="İpotekli Oran (%)",
                                  hovertemplate="%{x}<br>İpotekli: %{y:.1f}%<extra></extra>"), secondary_y=True)
    fig.update_layout(**_konut_ortak(), title=dict(text="Konut Satış Adetleri", font=dict(size=17, color=BLACK), x=0.5),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1), bargap=0.25)
    fig.update_yaxes(title_text="Bin Adet", secondary_y=False, gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK,
                     tickfont=dict(size=13, color=BLACK), title_font=dict(size=14, color=BLACK))
    fig.update_yaxes(title_text="İpotekli Oran (%)", secondary_y=True, showgrid=False,
                     tickfont=dict(color=RED_500, size=13), title_font=dict(color=RED_500, size=14))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig

def konut_ilk_ikinci_el_grafik(df):
    if "Satis_IlkEl" not in df.columns or "Satis_IkinciEl" not in df.columns: return None
    tail = _son_25_ay(df, subset=["Satis_IlkEl"])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    ilk = tail["Satis_IlkEl"].values
    ikinci = tail["Satis_IkinciEl"].values
    oran = tail["IlkEl_Oran"].values if "IlkEl_Oran" in tail.columns else None
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x, y=ilk/1000, name="Birinci El (bin)",
                         marker=dict(color=BLUE_500, line=dict(color="white", width=0.5)),
                         hovertemplate="%{x}<br>Birinci El: %{y:,.0f} bin<extra></extra>"), secondary_y=False)
    fig.add_trace(go.Bar(x=x, y=ikinci/1000, name="İkinci El (bin)",
                         marker=dict(color=BLUE_300, line=dict(color="white", width=0.5)),
                         hovertemplate="%{x}<br>İkinci El: %{y:,.0f} bin<extra></extra>"), secondary_y=False)
    if oran is not None:
        fig.add_trace(go.Scatter(x=x, y=oran, mode="lines+markers+text",
                                  line=dict(color=BLACK, width=2.5), marker=dict(size=4, color=BLACK),
                                  text=[f"{v:.0f}%" for v in oran], textposition="top center",
                                  textfont=dict(size=11, color=BLACK), name="Birinci El Oran (%)",
                                  hovertemplate="%{x}<br>Birinci El: %{y:.1f}%<extra></extra>"), secondary_y=True)
    fig.update_layout(**_konut_ortak(), barmode="stack",
                      title=dict(text="Birinci El / İkinci El Satışlar", font=dict(size=17, color=BLACK), x=0.5),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1), bargap=0.25)
    fig.update_yaxes(title_text="Bin Adet", secondary_y=False, gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK,
                     tickfont=dict(size=13, color=BLACK), title_font=dict(size=14, color=BLACK))
    fig.update_yaxes(title_text="Birinci El Oran (%)", secondary_y=True, showgrid=False,
                     tickfont=dict(color=BLACK, size=13), title_font=dict(color=BLACK, size=14))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig

def konut_yeni_eski_grafik(df):
    kols = {"Yeni_Konut_FE_duzey": "Yeni Konut", "Eski_Konut_FE_duzey": "Eski Konut"}
    mevcut = {k: v for k, v in kols.items() if k in df.columns}
    if not mevcut: return None
    ilk_kol = list(mevcut.keys())[0]
    tail = _son_25_ay(df, subset=[ilk_kol])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    renkler = [BLUE_600, RED_500]
    fig = go.Figure()
    for i, (kol, isim) in enumerate(mevcut.items()):
        vals = tail[kol].values
        fig.add_trace(go.Scatter(x=x, y=vals, name=isim, mode="lines+markers+text",
                                  line=dict(color=renkler[i], width=2.5), marker=dict(size=4),
                                  text=[f"{v:,.0f}" for v in vals], textposition="top center",
                                  textfont=dict(size=11, color=renkler[i]),
                                  hovertemplate="%{x}<br>" + isim + ": %{y:,.1f}<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text="Yeni vs Eski Konut Fiyat Endeksi", font=dict(size=17, color=BLACK), x=0.5),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1),
                      yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=13, color=BLACK), title_text="Endeks"))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig

def konut_kira_grafik(df):
    kol = "Kira_Endeksi_duzey"
    if kol not in df.columns: return None
    tail = _son_25_ay(df, subset=[kol])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    vals = tail[kol].values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=vals, mode="lines+markers+text",
                              line=dict(color=BLUE_600, width=3), marker=dict(size=4),
                              text=[f"{v:,.0f}" for v in vals], textposition="top center",
                              textfont=dict(size=11, color=BLUE_600),
                              hovertemplate="%{x}<br>Kira Endeksi: %{y:,.1f}<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text="Yeni Kiracı Kira Endeksi", font=dict(size=17, color=BLACK), x=0.5),
                      showlegend=False, yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK), title_text="Endeks"))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig

def konut_birim_fiyat_grafik(df):
    kol = "Birim_Fiyat_TLm2"
    if kol not in df.columns: return None
    tail = _son_25_ay(df, subset=[kol])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    vals = tail[kol].values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=vals, mode="lines+markers+text",
                              line=dict(color=BLUE_600, width=3), marker=dict(size=4),
                              text=[f"₺{v:,.0f}" for v in vals], textposition="top center",
                              textfont=dict(size=11, color=BLUE_600),
                              hovertemplate="%{x}<br>₺%{y:,.0f}/m²<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text="Konut Birim Fiyat (TL/m²)", font=dict(size=17, color=BLACK), x=0.5),
                      showlegend=False, yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK), title_text="TL/m²"))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig

def konut_birim_kira_grafik(df):
    kol = "Birim_Kira_TLm2"
    if kol not in df.columns: return None
    tail = _son_25_ay(df, subset=[kol])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    vals = tail[kol].values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=vals, mode="lines+markers+text",
                              line=dict(color="#8B5CF6", width=3), marker=dict(size=4),
                              text=[f"₺{v:,.0f}" for v in vals], textposition="top center",
                              textfont=dict(size=11, color="#8B5CF6"),
                              hovertemplate="%{x}<br>₺%{y:,.0f}/m²<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text="Konut Birim Kira (TL/m²)", font=dict(size=17, color=BLACK), x=0.5),
                      showlegend=False, yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK), title_text="TL/m²"))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig

def konut_amortisman_grafik(df):
    kol = "Amortisman_Ay"
    if kol not in df.columns: return None
    tail = _son_25_ay(df, subset=[kol])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    vals = tail[kol].values
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=vals, mode="lines+markers+text",
                              line=dict(color=BLACK, width=2.5), marker=dict(size=4),
                              text=[f"{v:.0f}" for v in vals], textposition="top center",
                              textfont=dict(size=11, color=BLACK),
                              hovertemplate="%{x}<br>%{y:.0f} ay<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text="Konut Amortisman Süresi (Ay)", font=dict(size=17, color=BLACK), x=0.5),
                      showlegend=False, yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK), title_text="Ay"))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig

def konut_kredi_faiz_grafik(df):
    kol = "Konut_Kredi_Faiz"
    if kol not in df.columns: return None
    tail = df.dropna(subset=[kol]).copy()
    tail["Ay"] = tail["Tarih"].dt.to_period("M")
    tail = tail.groupby("Ay", as_index=False)[kol].mean()
    tail["Tarih"] = tail["Ay"].dt.to_timestamp()
    ilk_tarih = _son_ay_baslangici(tail["Tarih"])
    if ilk_tarih is None: return None
    tail = tail.loc[pd.to_datetime(tail["Tarih"], errors="coerce") >= ilk_tarih].copy()
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=tail[kol], mode="lines+markers", line=dict(color=RED_500, width=2.5),
                              hovertemplate="%{x}<br>%{y:.2f}%<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text="Konut Kredisi Faizi (%)", font=dict(size=17, color=BLACK), x=0.5),
                      showlegend=False, yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK), title_text="%"),
                      xaxis=dict(showgrid=False, tickfont=dict(size=13, color=BLACK)))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig


def konut_insaat_maliyet_grafik(df):
    a_kol = "Insaat_Maliyet_Aylik_Degisim"
    y_kol = "Insaat_Maliyet_Yillik_Degisim"
    filtre_kol = next((kol for kol in [a_kol, y_kol] if kol in df.columns and df[kol].notna().any()), None)
    if filtre_kol is None:
        return None
    tail = _son_25_ay(df, subset=[filtre_kol])
    if tail.empty:
        return None
    x = _ay_etiket(tail["Tarih"])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    has_aylik = a_kol in tail.columns and tail[a_kol].notna().any()
    has_yillik = y_kol in tail.columns and tail[y_kol].notna().any()
    if has_aylik:
        aylik = tail[a_kol].values
        renkler = [BLUE_500 if v >= 0 else RED_500 for v in aylik]
        fig.add_trace(go.Bar(
            x=x, y=aylik, marker=dict(color=renkler),
            text=[f"{v:.2f}" for v in aylik], textposition="outside",
            textfont=dict(size=13, color=BLACK), name="Aylık %",
            hovertemplate="%{x}<br>Aylık: %{y:.2f}%<extra></extra>"
        ), secondary_y=False)
    if has_yillik:
        fig.add_trace(go.Scatter(
            x=x, y=tail[y_kol], mode="lines+markers", line=dict(color=RED_500, width=2.5),
            marker=dict(size=4), name="Yıllık %",
            hovertemplate="%{x}<br>Yıllık: %{y:.2f}%<extra></extra>"
        ), secondary_y=has_aylik)
    fig.update_layout(**_konut_ortak(),
        title=dict(
            text="İnşaat Maliyet Endeksi Değişim Oranları" if has_aylik else "İnşaat Maliyet Endeksi (Yıllık Değişim %)",
            font=dict(size=17, color=BLACK),
            x=0.5,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="#D1D5DB", borderwidth=1), bargap=0.25)
    fig.update_yaxes(
        title_text="Aylık %" if has_aylik else "Yıllık %",
        secondary_y=False,
        gridcolor="#D1D5DB",
        zeroline=True,
        zerolinecolor=BLACK,
        tickfont=dict(color=BLUE_600 if has_aylik else RED_500, size=13),
        title_font=dict(color=BLUE_600 if has_aylik else RED_500, size=14),
    )
    if has_aylik and has_yillik:
        fig.update_yaxes(title_text="Yıllık %", secondary_y=True, showgrid=False,
                         tickfont=dict(color=RED_500, size=13), title_font=dict(color=RED_500, size=14))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig


def konut_insaat_uretim_grafik(df):
    a_kol = "Insaat_Uretim_Aylik_Degisim"
    y_kol = "Insaat_Uretim_Yillik_Degisim"
    filtre_kol = next((kol for kol in [a_kol, y_kol] if kol in df.columns and df[kol].notna().any()), None)
    if filtre_kol is None:
        return None
    tail = _son_25_ay(df, subset=[filtre_kol])
    if tail.empty:
        return None
    x = _ay_etiket(tail["Tarih"])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    has_aylik = a_kol in tail.columns and tail[a_kol].notna().any()
    has_yillik = y_kol in tail.columns and tail[y_kol].notna().any()
    if has_aylik:
        aylik = tail[a_kol].values
        renkler = [BLUE_500 if v >= 0 else RED_500 for v in aylik]
        fig.add_trace(go.Bar(
            x=x, y=aylik, marker=dict(color=renkler),
            text=[f"{v:.2f}" for v in aylik], textposition="outside",
            textfont=dict(size=13, color=BLACK), name="Aylık %",
            hovertemplate="%{x}<br>Aylık: %{y:.2f}%<extra></extra>"
        ), secondary_y=False)
    if has_yillik:
        fig.add_trace(go.Scatter(
            x=x, y=tail[y_kol], mode="lines+markers", line=dict(color=RED_500, width=2.5),
            marker=dict(size=4), name="Yıllık %",
            hovertemplate="%{x}<br>Yıllık: %{y:.2f}%<extra></extra>"
        ), secondary_y=has_aylik)
    fig.update_layout(**_konut_ortak(),
        title=dict(
            text="İnşaat Üretim Endeksi Değişim Oranları" if has_aylik else "İnşaat Üretim Endeksi (Yıllık Değişim %)",
            font=dict(size=17, color=BLACK),
            x=0.5,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="#D1D5DB", borderwidth=1), bargap=0.25)
    fig.update_yaxes(
        title_text="Aylık %" if has_aylik else "Yıllık %",
        secondary_y=False,
        gridcolor="#D1D5DB",
        zeroline=True,
        zerolinecolor=BLACK,
        tickfont=dict(color=BLUE_600 if has_aylik else RED_500, size=13),
        title_font=dict(color=BLUE_600 if has_aylik else RED_500, size=14),
    )
    if has_aylik and has_yillik:
        fig.update_yaxes(title_text="Yıllık %", secondary_y=True, showgrid=False,
                         tickfont=dict(color=RED_500, size=13), title_font=dict(color=RED_500, size=14))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig


def konut_insaat_guven_grafik(df):
    kol = "Insaat_Guven_Endeks"
    if kol not in df.columns:
        return None
    tail = _son_25_ay(df, subset=[kol])
    if tail.empty:
        return None
    x = _ay_etiket(tail["Tarih"])
    vals = tail[kol].values
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=vals, mode="lines+markers+text", line=dict(color=NAVY_800, width=2.8),
        marker=dict(size=4, color=NAVY_800), text=[f"{v:.1f}" for v in vals], textposition="top center",
        textfont=dict(size=11, color=NAVY_800),
        hovertemplate="%{x}<br>Endeks: %{y:.1f}<extra></extra>"
    ))
    fig.update_layout(**_konut_ortak(),
        title=dict(text="İnşaat Güven Endeksi", font=dict(size=17, color=BLACK), x=0.5),
        showlegend=False,
        yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK), title_text="Endeks"))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig


def konut_ruhsat_grafik(df, kol, baslik):
    if kol not in df.columns: return None
    tail = df.dropna(subset=[kol]).copy()
    tail = tail[tail[kol] > 0]
    tail = _2020den_bugune(tail, subset=[kol])
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    vals = tail[kol].values
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=vals, marker_color=BLUE_500, text=[f"{v:,.0f}" for v in vals],
                         textposition="outside", textfont=dict(size=13, color=BLACK),
                         hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text=f"{baslik} (2020'den Bugüne)", font=dict(size=17, color=BLACK), x=0.5),
                      showlegend=False, bargap=0.3,
                      yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK)),
                      xaxis=dict(showgrid=False, tickfont=dict(size=12, color=BLACK)))
    _uygula_kategorik_ay_xaxis(fig, x)
    return fig


# ── KREDİ KARTI FORMAT YARDIMCILARI ─────────────────────
def _kk_fmt_tl(val):
    if pd.isna(val) or val == 0: return "-"
    return f"{val/1_000_000:,.1f} mr ₺"

def _kk_fmt_pct(val):
    if pd.isna(val): return "-"
    return f"%{val:+.1f}"

def _kk_fmt_adet(val):
    if pd.isna(val) or val == 0: return "-"
    if abs(val) >= 1e9: return f"{val/1e9:,.2f} mr"
    if abs(val) >= 1e6: return f"{val/1e6:,.1f} mn"
    return f"{val:,.0f}"

def _kk_fmt_sepet(val):
    if pd.isna(val) or val == 0: return "-"
    return f"{val:,.0f} ₺"


# ── KREDİ KARTI GRAFİKLER ────────────────────────────────
def _kk_ortak():
    return dict(
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Arial", color=BLACK, size=14),
        margin=dict(t=65, b=55, l=65, r=65), height=520,
    )

def kk_haftalik_trend(df):
    """01 — Haftalık toplam harcama bar + 13H ort çizgi."""
    if "KT1" not in df.columns: return None
    tail = _son_25_ay(df, subset=["KT1"])
    if tail.empty:
        return None
    last_n = len(tail)
    baslangic_yili = pd.to_datetime(tail['Tarih']).min().year
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tail["Tarih"], y=tail["KT1"]/1e6, marker=dict(color=BLUE_500), name="Haftalık"))
    if "KT1_MA" in tail.columns:
        fig.add_trace(go.Scatter(x=tail["Tarih"], y=tail["KT1_MA"]/1e6, mode="lines",
                                  line=dict(color=NAVY_800, width=2.5), name=f"{KK_MA}H Ort."))
    fig.update_layout(**_kk_ortak(),
        title=dict(text=f"Toplam Kartlı Harcama (Başlangıç: {baslangic_yili}, {last_n} Haftalık Gözlem) — mr ₺", font=dict(size=17, color=BLACK), x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    font=dict(size=13, color=BLACK), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1),
        yaxis=dict(gridcolor=GRID, zeroline=False, title_text="mr ₺",
                   tickfont=dict(size=13, color=BLACK), title_font=dict(size=14, color=BLACK)),
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color=BLACK)))
    _uygula_tarih_ay_xaxis(fig, tail["Tarih"])
    return fig

def kk_yoy_bar(df):
    """01 — Sektörel YoY değişim yatay bar."""
    son = df.iloc[-1]
    veri_tarihi = son["Tarih"]
    yoy_data = []
    for kt in KK_GERCEK:
        yoy_col = f"{kt}_yoy"
        if yoy_col in df.columns and not np.isnan(son.get(yoy_col, np.nan)):
            yoy_data.append((KK_SEKTOR_MAP.get(kt, kt), float(son[yoy_col])))
    if not yoy_data: return None
    yoy_data.sort(key=lambda x: x[1], reverse=True)
    names = [d[0] for d in yoy_data]
    vals = [d[1] for d in yoy_data]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=vals, y=names, orientation="h",
        marker=dict(color=[BLUE_500 if v >= 0 else RED_500 for v in vals]),
        text=[f"%{v:+.0f}" for v in vals], textposition="outside", cliponaxis=False))
    max_yoy = max(abs(v) for v in vals) if vals else 100
    layout = _kk_ortak()
    layout.update(height=600, margin=dict(t=65, b=30, l=160, r=50))
    fig.update_layout(**layout,
        title=dict(text=f"Sektörel YoY Değişim ({veri_tarihi.strftime('%d.%m.%Y')}) — %", font=dict(size=17, color=BLACK), x=0.5),
        showlegend=False,
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=True, zerolinecolor=BLACK,
                   tickfont=dict(size=13, color=BLACK),
                   range=[min(vals) * 1.15, max_yoy * 1.35]))
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=12, color=BLACK))
    return fig

def kk_sektorel_tablo_html(df):
    """02 — Sektörel dağılım HTML tablosu (rapordaki 8 kolon)."""
    son = df.iloc[-1]
    toplam = float(son.get("KT1", 0))
    rows = []
    for kt in KK_GERCEK:
        if kt not in df.columns: continue
        tutar = float(son.get(kt, 0))
        yoy_col = f"{kt}_yoy"
        ma_col = f"{kt}_MA"
        ka = kt.replace("KT", "KA")
        sepet_col = f"Sepet_{kt}"
        sepet_ma_col = f"Sepet_{kt}_MA"

        yoy = float(son.get(yoy_col, np.nan)) if yoy_col in df.columns else np.nan
        ma_val = float(son.get(ma_col, 0)) if ma_col in df.columns else 0
        vs_ma = ((tutar / ma_val) - 1) * 100 if ma_val > 0 else np.nan
        pay = tutar / toplam * 100 if toplam > 0 else 0
        adet = float(son.get(ka, 0)) if ka in df.columns else 0
        sepet = float(son.get(sepet_col, 0)) if sepet_col in df.columns else 0
        sepet_ma = float(son.get(sepet_ma_col, 0)) if sepet_ma_col in df.columns else 0

        rows.append({
            "sektor": KK_SEKTOR_MAP.get(kt, kt),
            "tutar": tutar, "pay": pay, "yoy": yoy, "vs_ma": vs_ma,
            "adet": adet, "sepet": sepet, "sepet_ma": sepet_ma,
        })
    rows.sort(key=lambda r: r["tutar"], reverse=True)

    # HTML oluştur
    html = f"""<table style="width:100%; border-collapse:collapse; font-family:Arial; font-size:14px; margin-top:8px; border:1px solid #CBD5E1;">
<thead><tr style="background:{NAVY_800}; color:white; font-weight:bold; font-size:14px;">
<th style="padding:10px 8px; text-align:left; border:1px solid #94A3B8;">Sektör</th>
<th style="padding:10px 8px; text-align:right; border:1px solid #94A3B8;">Harcama</th>
<th style="padding:10px 8px; text-align:center; border:1px solid #94A3B8;">Pay</th>
<th style="padding:10px 8px; text-align:center; border:1px solid #94A3B8;">YoY</th>
<th style="padding:10px 8px; text-align:center; border:1px solid #94A3B8;">vs{KK_MA}H</th>
<th style="padding:10px 8px; text-align:right; border:1px solid #94A3B8;">İşlem</th>
<th style="padding:10px 8px; text-align:right; border:1px solid #94A3B8;">Sepet</th>
<th style="padding:10px 8px; text-align:right; border:1px solid #94A3B8;">Sepet {KK_MA}H</th>
</tr></thead><tbody>"""
    for i, r in enumerate(rows):
        bg = "#F1F5F9" if i % 2 == 0 else "white"
        yoy_color = "#15803d" if r["yoy"] >= 0 else "#DC2626"
        vs_color = "#15803d" if r["vs_ma"] >= 0 else "#DC2626"
        html += f"""<tr style="background:{bg}; color:#0F172A;">
<td style="padding:8px; font-weight:600; border-bottom:1px solid #E2E8F0;">{r['sektor']}</td>
<td style="padding:8px; text-align:right; font-weight:600; border-bottom:1px solid #E2E8F0;">{_kk_fmt_tl(r['tutar'])}</td>
<td style="padding:8px; text-align:center; border-bottom:1px solid #E2E8F0;">%{r['pay']:.1f}</td>
<td style="padding:8px; text-align:center; color:{yoy_color}; font-weight:600; border-bottom:1px solid #E2E8F0;">{_kk_fmt_pct(r['yoy'])}</td>
<td style="padding:8px; text-align:center; color:{vs_color}; font-weight:600; border-bottom:1px solid #E2E8F0;">{_kk_fmt_pct(r['vs_ma'])}</td>
<td style="padding:8px; text-align:right; border-bottom:1px solid #E2E8F0;">{_kk_fmt_adet(r['adet'])}</td>
<td style="padding:8px; text-align:right; border-bottom:1px solid #E2E8F0;">{_kk_fmt_sepet(r['sepet'])}</td>
<td style="padding:8px; text-align:right; border-bottom:1px solid #E2E8F0;">{_kk_fmt_sepet(r['sepet_ma'])}</td>
</tr>"""
    html += "</tbody></table>"
    return html

def kk_dual_bar(df, tip="harcama"):
    """03/04 — Çift renkli yatay bar (harcama veya işlem)."""
    son = df.iloc[-1]
    veri_tarihi = son["Tarih"].strftime("%d.%m.%Y")
    data = []
    for kt in KK_GERCEK:
        if tip == "harcama":
            col, ma_col = kt, f"{kt}_MA"
            if col not in df.columns or ma_col not in df.columns: continue
            cur = float(son.get(col, 0)) / 1e6
            avg = float(son.get(ma_col, 0)) / 1e6
        else:
            ka = kt.replace("KT", "KA")
            ma_col = f"{ka}_MA"
            if ka not in df.columns or ma_col not in df.columns: continue
            cur = float(son.get(ka, 0)) / 1e6
            avg = float(son.get(ma_col, 0)) / 1e6
        if cur > 0 or avg > 0:
            data.append((KK_SEKTOR_MAP.get(kt, kt), cur, avg))
    if not data: return None
    data.sort(key=lambda x: x[1], reverse=True)

    names = [d[0] for d in data]
    cur_vals = [d[1] for d in data]
    avg_vals = [d[2] for d in data]

    baz_vals, fark_vals, baz_colors, fark_colors = [], [], [], []
    for cur, avg in zip(cur_vals, avg_vals):
        if cur >= avg:
            baz_vals.append(avg); fark_vals.append(cur - avg)
            baz_colors.append(BLUE_300); fark_colors.append(BLUE_500)
        else:
            baz_vals.append(cur); fark_vals.append(avg - cur)
            baz_colors.append(BLUE_500); fark_colors.append(BLUE_300)

    unit = "mr ₺" if tip == "harcama" else "mn adet"
    baslik = f"Sektörel {'Harcama' if tip == 'harcama' else 'İşlem Adedi'} vs {KK_MA}H Ort. ({veri_tarihi}) — {unit}"

    fig = go.Figure()
    fig.add_trace(go.Bar(y=names, x=baz_vals, orientation="h",
                         marker=dict(color=baz_colors, line=dict(width=0)), showlegend=False))
    fig.add_trace(go.Bar(y=names, x=fark_vals, orientation="h",
                         marker=dict(color=fark_colors, line=dict(width=0)), showlegend=False))
    for i, (cur, avg) in enumerate(zip(cur_vals, avg_vals)):
        fig.add_annotation(x=max(cur, avg), y=names[i],
            text=f"  {cur:.1f}  (ort:{avg:.1f})", showarrow=False, xanchor="left",
            font=dict(size=11, color=BLACK))

    fig.update_layout(barmode="stack", title=dict(text=baslik, font=dict(size=15, color=BLACK), x=0.5),
        paper_bgcolor="white", plot_bgcolor="white", font=dict(family="Arial", color=BLACK, size=13),
        margin=dict(t=50, b=30, l=160, r=130), height=650, showlegend=False,
        xaxis=dict(showgrid=True, gridcolor=GRID, zeroline=False, title=unit,
                   tickfont=dict(size=13, color=BLACK)),
        yaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=12, color=BLACK)))
    fig.update_yaxes(autorange="reversed")
    return fig

def kk_ceyreklik_harcama(df):
    """05 — Çeyreklik stacked bar (top 4 sektör + diğer)."""
    cols_needed = ["KT1"] + KK_ANA_SEKTORLER
    for c in cols_needed:
        if c not in df.columns: return None
    dfc = _2020den_bugune(df[["Tarih", "Ceyrek"] + cols_needed].copy(), subset=["KT1"])
    if dfc.empty:
        return None
    dfc["Diger"] = dfc["KT1"] - dfc[KK_ANA_SEKTORLER].sum(axis=1)
    q = dfc.groupby("Ceyrek")[KK_ANA_SEKTORLER + ["Diger"]].sum().reset_index()
    q_renk = {k: c for k, c in zip(KK_ANA_SEKTORLER + ["Diger"],
              [NAVY_900, NAVY_700, BLUE_600, BLUE_400, BLUE_300])}
    q_isim = {k: KK_SEKTOR_MAP.get(k, k) for k in KK_ANA_SEKTORLER}
    q_isim["Diger"] = "Diğer"
    fig = go.Figure()
    for col in KK_ANA_SEKTORLER + ["Diger"]:
        fig.add_trace(go.Bar(x=q["Ceyrek"], y=q[col]/1e6, name=q_isim.get(col, col),
                              marker=dict(color=q_renk.get(col, SLATE_500))))
    layout = _kk_ortak()
    layout.update(height=420)
    fig.update_layout(barmode="stack", **layout,
        title=dict(text="Çeyreklik Harcama Dağılımı (2020'den Bugüne) — mr ₺", font=dict(size=17, color=BLACK), x=0.5),
        legend=dict(orientation="h", y=-0.22, x=0.5, xanchor="center",
                    font=dict(size=13, color=BLACK), bgcolor="rgba(255,255,255,0.95)",
                    bordercolor="#D1D5DB", borderwidth=1))
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=13, color=BLACK))
    fig.update_yaxes(gridcolor=GRID, tickfont=dict(size=13, color=BLACK),
                     title_text="mr ₺", title_font=dict(size=14, color=BLACK))
    return fig

def kk_ceyreklik_islem(df):
    """05 — Çeyreklik işlem adedi bar."""
    if "KA1" not in df.columns or "Ceyrek" not in df.columns: return None
    tail = _2020den_bugune(df, subset=["KA1"])
    if tail.empty:
        return None
    q = tail.groupby("Ceyrek")["KA1"].sum().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=q["Ceyrek"], y=q["KA1"]/1e9, marker_color=BLUE_500))
    layout = _kk_ortak()
    layout.update(height=350)
    fig.update_layout(**layout,
        title=dict(text="Çeyreklik Toplam İşlem Adedi (2020'den Bugüne) — mr adet", font=dict(size=17, color=BLACK), x=0.5),
        showlegend=False)
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=13, color=BLACK))
    fig.update_yaxes(gridcolor=GRID, tickfont=dict(size=13, color=BLACK),
                     title_text="mr adet", title_font=dict(size=14, color=BLACK))
    return fig

def kk_ceyreklik_tablo_html(df):
    """05 — 2020'den bugüne çeyrek harcama + işlem tablosu."""
    if "KT1" not in df.columns or "KA1" not in df.columns: return ""
    tail = _2020den_bugune(df, subset=["KT1", "KA1"])
    if tail.empty:
        return ""
    q = tail.groupby("Ceyrek")[["KT1", "KA1"]].sum().reset_index()
    html = f"""<table style="width:70%; border-collapse:collapse; font-family:Arial; font-size:14px; margin-top:8px; border:1px solid #CBD5E1;">
<thead><tr style="background:{NAVY_800}; color:white; font-weight:bold; font-size:14px;">
<th style="padding:10px 8px; text-align:center; border:1px solid #94A3B8;">Çeyrek</th>
<th style="padding:10px 8px; text-align:right; border:1px solid #94A3B8;">Toplam Harcama</th>
<th style="padding:10px 8px; text-align:right; border:1px solid #94A3B8;">Toplam İşlem Adedi</th>
</tr></thead><tbody>"""
    for i, (_, r) in enumerate(q.iterrows()):
        bg = "#F1F5F9" if i % 2 == 0 else "white"
        html += f"""<tr style="background:{bg}; color:#0F172A;">
<td style="padding:8px; text-align:center; font-weight:bold; border-bottom:1px solid #E2E8F0;">{r['Ceyrek']}</td>
<td style="padding:8px; text-align:right; font-weight:600; border-bottom:1px solid #E2E8F0;">{_kk_fmt_tl(float(r['KT1']))}</td>
<td style="padding:8px; text-align:right; font-weight:600; border-bottom:1px solid #E2E8F0;">{_kk_fmt_adet(float(r['KA1']))}</td>
</tr>"""
    html += "</tbody></table>"
    return html


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    if LOGO_PATH.exists():
        logo_base64 = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
        st.markdown(
            f"""
            <div style="background:#FFFFFF; border-radius:16px; padding:14px 14px 10px 14px; margin-bottom:10px; box-shadow:0 10px 24px rgba(15,23,42,0.22);">
                <img src="data:image/png;base64,{logo_base64}" style="width:100%; display:block; border-radius:12px;" />
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown("""
        <div style="background:#FFFFFF; border-radius:16px; padding:16px 12px 14px 12px; margin-bottom:10px; box-shadow:0 10px 24px rgba(15,23,42,0.22); text-align:center;">
            <span style="font-size:24px; font-weight:800;
            background:linear-gradient(135deg,#A855F7,#22D3EE);
            -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            Sai Manager</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<div class="modul-baslik">MODÜL SEÇ</div>', unsafe_allow_html=True)
    modul = st.selectbox("Modül", [
        "📈 TÜFE",
        "🏭 ÜFE",
        "🌍 Yabancı Sermaye Hareketleri",
        "✈️ Hava Trafik",
        "🏠 Konut Sektörel Veriler",
        "💳 Kredi Kartı Harcamaları",
    ], label_visibility="collapsed")

    st.markdown("---")

    secili_kalemler = []

    if "TÜFE" in modul:
        st.markdown('<div class="modul-baslik">TÜFE KALEMLERİ</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Tümünü Seç", use_container_width=True, key="tufe_hepsi"):
                st.session_state["tufe_secim"] = TUFE_KALEMLER.copy()
                for kalem in TUFE_KALEMLER:
                    st.session_state[f"cb_{kalem}"] = True
        with col_b:
            if st.button("Temizle", use_container_width=True, key="tufe_temizle"):
                st.session_state["tufe_secim"] = []
                for kalem in TUFE_KALEMLER:
                    st.session_state[f"cb_{kalem}"] = False
        if "tufe_secim" not in st.session_state:
            st.session_state["tufe_secim"] = []
        for kalem in TUFE_KALEMLER:
            checked = kalem in st.session_state["tufe_secim"]
            val = st.checkbox(kalem, value=checked, key=f"cb_{kalem}")
            if val and kalem not in st.session_state["tufe_secim"]:
                st.session_state["tufe_secim"].append(kalem)
            elif not val and kalem in st.session_state["tufe_secim"]:
                st.session_state["tufe_secim"].remove(kalem)
        secili_kalemler = st.session_state["tufe_secim"]

    elif "ÜFE" in modul:
        st.markdown('<div class="modul-baslik">ÜFE KALEMLERİ</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Tümünü Seç", use_container_width=True, key="ufe_hepsi"):
                st.session_state["ufe_secim"] = UFE_KALEMLER.copy()
                for kalem in UFE_KALEMLER:
                    st.session_state[f"ucb_{kalem}"] = True
        with col_b:
            if st.button("Temizle", use_container_width=True, key="ufe_temizle"):
                st.session_state["ufe_secim"] = []
                for kalem in UFE_KALEMLER:
                    st.session_state[f"ucb_{kalem}"] = False
        if "ufe_secim" not in st.session_state:
            st.session_state["ufe_secim"] = []
        for kalem in UFE_KALEMLER:
            checked = kalem in st.session_state["ufe_secim"]
            val = st.checkbox(kalem, value=checked, key=f"ucb_{kalem}")
            if val and kalem not in st.session_state["ufe_secim"]:
                st.session_state["ufe_secim"].append(kalem)
            elif not val and kalem in st.session_state["ufe_secim"]:
                st.session_state["ufe_secim"].remove(kalem)
        secili_kalemler = st.session_state["ufe_secim"]

    elif "Yabancı Sermaye" in modul:
        st.markdown('<div class="modul-baslik">YABANCI SERMAYE KALEMLERİ</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Tümünü Seç", use_container_width=True, key="ysa_hepsi"):
                st.session_state["ysa_secim"] = YSA_MENU.copy()
                for kalem in YSA_MENU:
                    st.session_state[f"ycb_{kalem}"] = True
        with col_b:
            if st.button("Temizle", use_container_width=True, key="ysa_temizle"):
                st.session_state["ysa_secim"] = []
                for kalem in YSA_MENU:
                    st.session_state[f"ycb_{kalem}"] = False
        if "ysa_secim" not in st.session_state:
            st.session_state["ysa_secim"] = []
        for kalem in YSA_MENU:
            checked = kalem in st.session_state["ysa_secim"]
            val = st.checkbox(kalem, value=checked, key=f"ycb_{kalem}")
            if val and kalem not in st.session_state["ysa_secim"]:
                st.session_state["ysa_secim"].append(kalem)
            elif not val and kalem in st.session_state["ysa_secim"]:
                st.session_state["ysa_secim"].remove(kalem)
        secili_kalemler = st.session_state["ysa_secim"]

    elif "Hava Trafik" in modul:
        st.markdown('<div class="modul-baslik">HAVA TRAFIK</div>', unsafe_allow_html=True)
        secenekler = ["THYAO", "PGSUS", "TAVHL", "Jet Yakıtı"]
        mevcut = st.session_state.get("hava_trafik_panel", "THYAO")
        if mevcut not in secenekler:
            mevcut = "THYAO"
        secili_panel = st.radio(
            "Hava Trafik",
            secenekler,
            index=secenekler.index(mevcut),
            key="hava_trafik_panel",
            label_visibility="collapsed",
        )
        if secili_panel == "Jet Yakıtı":
            st.caption("Jet Yakıtı soldaki menüden açılır.")
        else:
            st.caption(f"{secili_panel} grafikleri soldaki menüden açılır.")

    elif "Konut" in modul:
        st.markdown('<div class="modul-baslik">KONUT KALEMLERİ</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Tümünü Seç", use_container_width=True, key="konut_hepsi"):
                st.session_state["konut_secim"] = KONUT_MENU.copy()
                for kalem in KONUT_MENU:
                    st.session_state[f"kcb_{kalem}"] = True
        with col_b:
            if st.button("Temizle", use_container_width=True, key="konut_temizle"):
                st.session_state["konut_secim"] = []
                for kalem in KONUT_MENU:
                    st.session_state[f"kcb_{kalem}"] = False
        if "konut_secim" not in st.session_state:
            st.session_state["konut_secim"] = []
        for kalem in KONUT_MENU:
            checked = kalem in st.session_state["konut_secim"]
            val = st.checkbox(kalem, value=checked, key=f"kcb_{kalem}")
            if val and kalem not in st.session_state["konut_secim"]:
                st.session_state["konut_secim"].append(kalem)
            elif not val and kalem in st.session_state["konut_secim"]:
                st.session_state["konut_secim"].remove(kalem)
        secili_kalemler = st.session_state["konut_secim"]

    elif "Kredi Kartı" in modul:
        st.markdown('<div class="modul-baslik">KREDİ KARTI BÖLÜMLERİ</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Tümünü Seç", use_container_width=True, key="kk_hepsi"):
                st.session_state["kk_secim"] = KK_MENU.copy()
                for kalem in KK_MENU:
                    st.session_state[f"kkcb_{kalem}"] = True
        with col_b:
            if st.button("Temizle", use_container_width=True, key="kk_temizle"):
                st.session_state["kk_secim"] = []
                for kalem in KK_MENU:
                    st.session_state[f"kkcb_{kalem}"] = False
        if "kk_secim" not in st.session_state:
            st.session_state["kk_secim"] = []
        for kalem in KK_MENU:
            checked = kalem in st.session_state["kk_secim"]
            val = st.checkbox(kalem, value=checked, key=f"kkcb_{kalem}")
            if val and kalem not in st.session_state["kk_secim"]:
                st.session_state["kk_secim"].append(kalem)
            elif not val and kalem in st.session_state["kk_secim"]:
                st.session_state["kk_secim"].remove(kalem)
        secili_kalemler = st.session_state["kk_secim"]

    st.markdown("---")

    if st.button("🔄 Veriyi Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"""<div style="text-align:center; color:#64748B; font-size:10px; margin-top:15px;">
        Sai Amatör Yatırım<br>Kaynak: TCMB EVDS<br>{datetime.now().strftime('%d.%m.%Y %H:%M')}
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
# ANA İÇERİK
# ═══════════════════════════════════════════════════════════
if "TÜFE" in modul:
    df_tufe = tufe_yukle(csv_cache_key("tufe.csv"))
    if df_tufe is None:
        st.warning("⚠️ TÜFE verisi bulunamadı!")
        st.code("python makro.py guncelle --only tufe", language="bash")
        st.stop()
    if not secili_kalemler:
        st.info("👈 Sol menüden görüntülemek istediğin TÜFE kalemlerini seç.")
    else:
        n = len(secili_kalemler)
        if n == 1:
            fig = tufe_grafik(df_tufe, secili_kalemler[0])
            if fig:
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
        else:
            for i in range(0, n, 2):
                cols = st.columns(2)
                for j in range(2):
                    idx = i + j
                    if idx < n:
                        fig = tufe_grafik(df_tufe, secili_kalemler[idx])
                        if fig:
                            with cols[j]:
                                st.plotly_chart(fig, use_container_width=True)

elif "ÜFE" in modul:
    df_ufe = ufe_yukle(csv_cache_key("ufe.csv"))
    if df_ufe is None:
        st.warning("⚠️ ÜFE verisi bulunamadı!")
        st.code("python makro.py guncelle --only ufe", language="bash")
        st.stop()
    if not secili_kalemler:
        st.info("👈 Sol menüden görüntülemek istediğin ÜFE kalemlerini seç.")
    else:
        n = len(secili_kalemler)
        if n == 1:
            fig = tufe_grafik(df_ufe, secili_kalemler[0])
            if fig:
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
        else:
            for i in range(0, n, 2):
                cols = st.columns(2)
                for j in range(2):
                    idx = i + j
                    if idx < n:
                        fig = tufe_grafik(df_ufe, secili_kalemler[idx])
                        if fig:
                            with cols[j]:
                                st.plotly_chart(fig, use_container_width=True)

elif "Yabancı Sermaye" in modul:
    df_ysa = ysa_yukle(csv_cache_key("ysa.csv"))
    if df_ysa is None:
        st.warning("⚠️ YSA verisi bulunamadı!")
        st.code("python makro.py guncelle --only ysa", language="bash")
        st.stop()
    if not secili_kalemler:
        st.info("👈 Sol menüden görüntülemek istediğin kalemleri seç.")
    else:
        grafik_listesi = []
        for kalem in secili_kalemler:
            if kalem == "Hisse Senedi":
                grafik_listesi.append(ysa_bilesen_grafik(df_ysa, "Hisse", "Hisse Senedi (mn $)"))
            elif kalem == "DİBS":
                grafik_listesi.append(ysa_bilesen_grafik(df_ysa, "DIBS", "DİBS (mn $)"))
            elif kalem == "Özel Sektör":
                grafik_listesi.append(ysa_bilesen_grafik(df_ysa, "Ozel_Sektor", "Özel Sektör (mn $)"))
            elif kalem == "Eurobond":
                grafik_listesi.append(ysa_bilesen_grafik(df_ysa, "Eurobond", "Eurobond (mn $)"))
            elif kalem == "Toplam Net Akım":
                grafik_listesi.append(ysa_toplam_aylik_grafik(df_ysa))
            elif kalem == "Kümülatif":
                grafik_listesi.append(ysa_kumulatif_grafik(df_ysa))
            elif kalem == "Çeyreklik Dağılım":
                grafik_listesi.append(ysa_ceyreklik_grafik(df_ysa))
        grafik_listesi = [g for g in grafik_listesi if g is not None]
        n = len(grafik_listesi)
        if n == 1:
            grafik_listesi[0].update_layout(height=600)
            st.plotly_chart(grafik_listesi[0], use_container_width=True)
        else:
            for i in range(0, n, 2):
                cols = st.columns(2)
                for j in range(2):
                    idx = i + j
                    if idx < n:
                        with cols[j]:
                            st.plotly_chart(grafik_listesi[idx], use_container_width=True)

elif "Hava Trafik" in modul:
    secili_panel = st.session_state.get("hava_trafik_panel", "THYAO")
    if secili_panel == "THYAO":
        render_thyao_tab()
    elif secili_panel == "PGSUS":
        render_pgsus_tab()
    elif secili_panel == "TAVHL":
        render_tavhl_tab()
    else:
        render_jet_yakiti_tab()

elif "Konut" in modul:
    df_konut = konut_yukle(csv_cache_key("konut.csv"))
    if df_konut is None:
        st.warning("⚠️ Konut verisi bulunamadı!")
        st.code("python makro.py guncelle --only konut", language="bash")
        st.stop()
    if not secili_kalemler:
        st.info("👈 Sol menüden görüntülemek istediğin kalemleri seç.")
    else:
        grafik_listesi = []
        for kalem in secili_kalemler:
            if kalem == "KFE Türkiye":
                grafik_listesi.append(konut_kfe_grafik(df_konut))
            elif kalem == "Konut Satış Adetleri":
                grafik_listesi.append(konut_satis_grafik(df_konut))
                grafik_listesi.append(konut_ilk_ikinci_el_grafik(df_konut))
            elif kalem == "Yeni vs Eski Konut FE":
                grafik_listesi.append(konut_yeni_eski_grafik(df_konut))
            elif kalem == "Kira Endeksi":
                grafik_listesi.append(konut_kira_grafik(df_konut))
            elif kalem == "Birim Fiyat (TL/m²)":
                grafik_listesi.append(konut_birim_fiyat_grafik(df_konut))
            elif kalem == "Birim Kira (TL/m²)":
                grafik_listesi.append(konut_birim_kira_grafik(df_konut))
            elif kalem == "Amortisman (Ay)":
                grafik_listesi.append(konut_amortisman_grafik(df_konut))
            elif kalem == "Konut Kredisi Faizi (%)":
                grafik_listesi.append(konut_kredi_faiz_grafik(df_konut))
            elif kalem == "İnşaat Maliyet Endeksi":
                grafik_listesi.append(konut_insaat_maliyet_grafik(df_konut))
            elif kalem == "İnşaat Üretim Endeksi":
                grafik_listesi.append(konut_insaat_uretim_grafik(df_konut))
            elif kalem == "İnşaat Güven Endeksi":
                grafik_listesi.append(konut_insaat_guven_grafik(df_konut))
            elif kalem == "Yapı Ruhsatı — Yapı Sayısı":
                grafik_listesi.append(konut_ruhsat_grafik(df_konut, "Ruhsat_Konut_Yapi", "Yapı Ruhsatı — Yapı Sayısı"))
            elif kalem == "Yapı Ruhsatı — Yüzölçüm":
                grafik_listesi.append(konut_ruhsat_grafik(df_konut, "Ruhsat_Konut_Yuzolcum", "Yapı Ruhsatı — Yüzölçüm (m²)"))
            elif kalem == "Yapı Ruhsatı — Daire Sayısı":
                grafik_listesi.append(konut_ruhsat_grafik(df_konut, "Ruhsat_Konut_Daire", "Yapı Ruhsatı — Daire Sayısı"))
        grafik_listesi = [g for g in grafik_listesi if g is not None]
        n = len(grafik_listesi)
        if n == 1:
            grafik_listesi[0].update_layout(height=600)
            st.plotly_chart(grafik_listesi[0], use_container_width=True)
        elif n > 1:
            for i in range(0, n, 2):
                cols = st.columns(2)
                for j in range(2):
                    idx = i + j
                    if idx < n:
                        with cols[j]:
                            st.plotly_chart(grafik_listesi[idx], use_container_width=True)

elif "Kredi Kartı" in modul:
    df_kk = kredi_karti_yukle(csv_cache_key("kredi_karti.csv"))

    if df_kk is None:
        st.warning("⚠️ Kredi kartı verisi bulunamadı!")
        st.code("python makro.py guncelle --only kredi_karti", language="bash")
        st.stop()

    if not secili_kalemler:
        st.info("👈 Sol menüden görüntülemek istediğin bölümleri seç.")
    else:
        son = df_kk.iloc[-1]
        veri_tarihi = son["Tarih"]
        veri_tarihi_str = veri_tarihi.strftime("%d.%m.%Y")

        for bolum in secili_kalemler:

            # ── 01 GENEL GÖRÜNÜM ──────────────────────
            if "Genel Görünüm" in bolum:
                st.markdown(f"### 01 | GENEL GÖRÜNÜM")
                st.caption(f"Veri Tarihi: {veri_tarihi_str}")

                # KPI kartları
                toplam_son = float(son.get("KT1", 0))
                yoy_toplam = float(son.get("KT1_yoy", np.nan))
                islem_son = float(son.get("KA1", 0))
                sepet_son = float(son.get("Sepet_KT1", 0))

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Son Hafta Toplam", _kk_fmt_tl(toplam_son))
                c2.metric("YoY Değişim", _kk_fmt_pct(yoy_toplam))
                c3.metric("İşlem Adedi", _kk_fmt_adet(islem_son))
                c4.metric("Ort. Sepet", _kk_fmt_sepet(sepet_son))

                st.plotly_chart(kk_haftalik_trend(df_kk), use_container_width=True)
                st.plotly_chart(kk_yoy_bar(df_kk), use_container_width=True)

                # Açıklama
                toplam_ma = float(son.get("KT1_MA", np.nan))
                ma_cmp = ""
                if not np.isnan(toplam_ma) and toplam_ma > 0:
                    fark = (toplam_son / toplam_ma - 1) * 100
                    ma_cmp = f" Bu değer {KK_MA} haftalık ortalamanın **{_kk_fmt_pct(fark)}** {'üzerindedir' if fark >= 0 else 'altındadır'}."

                ytd_sum = float(df_kk.loc[df_kk["Tarih"] >= datetime(veri_tarihi.year, 1, 1), "KT1"].sum()) if "KT1" in df_kk.columns else 0
                st.markdown(
                    f"**{len(df_kk)} haftalık** veri serisinde toplam kartlı harcama "
                    f"{veri_tarihi_str} haftasında **{_kk_fmt_tl(toplam_son)}**.{ma_cmp} "
                    f"YoY: **{_kk_fmt_pct(yoy_toplam)}**, işlem: **{_kk_fmt_adet(islem_son)}**, "
                    f"sepet: **{_kk_fmt_sepet(sepet_son)}**. "
                    f"YTD ({veri_tarihi.year}): **{_kk_fmt_tl(ytd_sum)}**."
                )
                st.markdown("---")

            # ── 02 SEKTÖREL DAĞILIM (TABLO) ───────────
            elif "Sektörel Dağılım" in bolum:
                st.markdown(f"### 02 | SEKTÖREL DAĞILIM")
                st.markdown(f"**Sektörel Dağılım ({veri_tarihi_str})**")
                st.markdown(kk_sektorel_tablo_html(df_kk), unsafe_allow_html=True)
                st.caption(
                    f"YoY = 52 hafta öncesine göre değişim. vs{KK_MA}H = son {KK_MA} haftalık ortalamaya göre fark. "
                    f"Sepet = harcama tutarı / işlem adedi (TL). Sepet {KK_MA}H = sepet büyüklüğünün {KK_MA} haftalık ortalaması."
                )
                st.markdown("---")

            # ── 03 HARCAMA vs 13H ORT ─────────────────
            elif "Harcama vs" in bolum:
                st.markdown(f"### 03 | SEKTÖREL HARCAMA vs {KK_MA} HAFTA ORTALAMASI")
                fig = kk_dual_bar(df_kk, "harcama")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                st.caption(
                    f"■ Koyu mavi = son haftanın {KK_MA}H ortalamasını aşan kısmı. "
                    f"■ Açık mavi = fark bölgesi."
                )
                st.markdown("---")

            # ── 04 İŞLEM ADEDİ ────────────────────────
            elif "İşlem Adedi" in bolum:
                st.markdown("### 04 | İŞLEM ADEDİ ANALİZİ")
                fig = kk_dual_bar(df_kk, "islem")
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                islem_ma = float(son.get("KA1_MA", 0))
                if islem_ma > 0:
                    islem_fark = (islem_son / islem_ma - 1) * 100
                    st.markdown(
                        f"Toplam işlem adedi son hafta: **{_kk_fmt_adet(islem_son)}**, "
                        f"{KK_MA}H ortalamasının **{_kk_fmt_pct(islem_fark)}** "
                        f"{'üzerinde' if islem_fark >= 0 else 'altında'}."
                    )
                st.markdown("---")

            # ── 05 ÇEYREKLİK DAĞILIM ─────────────────
            elif "Çeyreklik" in bolum:
                st.markdown("### 05 | ÇEYREKLİK DAĞILIM")
                fig_h = kk_ceyreklik_harcama(df_kk)
                if fig_h:
                    st.plotly_chart(fig_h, use_container_width=True)
                fig_i = kk_ceyreklik_islem(df_kk)
                if fig_i:
                    st.plotly_chart(fig_i, use_container_width=True)
                st.markdown("**2020'den Bugüne — Harcama & İşlem Adedi**")
                st.markdown(kk_ceyreklik_tablo_html(df_kk), unsafe_allow_html=True)
                st.caption(
                    f"Veriler TCMB EVDS kaynaklıdır. Veri frekansı haftalık. "
                    f"(*) İnternet, Mektup/Telefon ve Gümrük serileri toplama dahil değildir."
                )
