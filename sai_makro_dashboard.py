# -*- coding: utf-8 -*-
"""
SAI MAKRO DASHBOARD
====================
streamlit run sai_makro_dashboard.py --server.port 8503
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

st.set_page_config(
    page_title="Sai Makro",
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
</style>
""", unsafe_allow_html=True)

# ── VERİ YÜKLEME ─────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd()
DATA_DIR = SCRIPT_DIR / "makro_data"


def csv_cache_key(filename):
    csv = DATA_DIR / filename
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


# ── TÜFE/ÜFE GRAFİK ─────────────────────────────────────
def tufe_grafik(df, kalem_adi):
    aylik_kol = f"{kalem_adi}_aylik"
    yillik_kol = f"{kalem_adi}_yillik"

    if aylik_kol not in df.columns:
        return None

    tail = df.dropna(subset=[aylik_kol]).tail(25).copy()
    if tail.empty:
        return None

    ay_kisa = {
        1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz",
        7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"
    }
    x_labels = [f"{ay_kisa[t.month]} {str(t.year)[2:]}" for t in tail["Tarih"]]

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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=13, color=NAVY_900), showgrid=False)

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
    tail = df.dropna(subset=[bilesen_kol]).tail(13).copy()
    if tail.empty:
        return None
    ay_kisa = {1:"Oca",2:"Şub",3:"Mar",4:"Nis",5:"May",6:"Haz",
               7:"Tem",8:"Ağu",9:"Eyl",10:"Eki",11:"Kas",12:"Ara"}
    x_labels = [f"{t.day} {ay_kisa[t.month]}" for t in tail["Tarih"]]
    vals = tail[bilesen_kol].values
    bar_colors = [BLUE_500 if v >= 0 else RED_500 for v in vals]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=x_labels, y=vals,
        marker=dict(color=bar_colors, line=dict(color="white", width=0.5)),
        text=[f"{v:+,.0f}" for v in vals],
        textposition="outside",
        textfont=dict(size=14, color=BLACK),
        hovertemplate="%{x}<br>%{y:+,.0f} mn $<extra></extra>",
    ))
    fig.update_layout(
        **_ysa_ortak_layout(),
        title=dict(text=baslik, font=dict(size=17, color=BLACK), x=0.5),
        showlegend=False, bargap=0.3,
        yaxis=dict(gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK, zerolinewidth=0.8,
                   title_text="mn $", tickfont=dict(size=14, color=BLACK),
                   title_font=dict(size=14, color=BLACK)),
    )
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=13, color=BLACK), showgrid=False)
    return fig

def ysa_toplam_aylik_grafik(df):
    if "Toplam" not in df.columns:
        return None
    dfc = df[["Tarih", "Toplam"]].copy()
    dfc["Ay"] = dfc["Tarih"].dt.to_period("M")
    aylik = dfc.groupby("Ay")["Toplam"].sum().reset_index()
    aylik["Ay_str"] = aylik["Ay"].astype(str)
    aylik["Ort_3Ay"] = aylik["Toplam"].rolling(3).mean()
    tail = aylik.tail(25).copy()
    if tail.empty:
        return None
    ay_kisa = {1:"Oca",2:"Şub",3:"Mar",4:"Nis",5:"May",6:"Haz",
               7:"Tem",8:"Ağu",9:"Eyl",10:"Eki",11:"Kas",12:"Ara"}
    x_labels = [f"{ay_kisa[p.month]} {str(p.year)[2:]}" for p in tail["Ay"]]
    vals = tail["Toplam"].values
    bar_colors = [BLUE_500 if v >= 0 else RED_500 for v in vals]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=x_labels, y=vals, marker=dict(color=bar_colors, line=dict(color="white", width=0.4)),
        text=[f"{v:+,.0f}" for v in vals], textposition="outside", textfont=dict(size=13, color=BLACK),
        name="Aylık Toplam (mn $)", hovertemplate="%{x}<br>Aylık: %{y:+,.0f} mn $<extra></extra>"), secondary_y=False)
    if tail["Ort_3Ay"].notna().any():
        fig.add_trace(go.Scatter(x=x_labels, y=tail["Ort_3Ay"].values, mode="lines",
            line=dict(color=BLACK, width=2.5), name="3 Ay Ort.",
            hovertemplate="%{x}<br>3 Ay Ort: %{y:,.0f} mn $<extra></extra>"), secondary_y=False)
    fig.update_layout(**_ysa_ortak_layout(),
        title=dict(text="Toplam Net Akım — Aylık (mn $)", font=dict(size=17, color=BLACK), x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=13, color="#000000"), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1), bargap=0.3)
    fig.update_yaxes(title_text="mn $", secondary_y=False, gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK, zerolinewidth=0.8,
                     tickfont=dict(color=BLACK, size=13), title_font=dict(color=BLACK, size=14))
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def ysa_kumulatif_grafik(df):
    if "Kumulatif" not in df.columns:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Tarih"], y=df["Kumulatif"], mode="lines",
        line=dict(color=BLUE_600, width=3.5), fill="tozeroy", fillcolor="rgba(37,99,235,0.25)",
        hovertemplate="%{x|%d.%m.%Y}<br>Kümülatif: %{y:+,.0f} mn $<extra></extra>"))
    fig.update_layout(**_ysa_ortak_layout(),
        title=dict(text="Kümülatif Net Akım (mn $)", font=dict(size=17, color=BLACK), x=0.5),
        showlegend=False, yaxis=dict(gridcolor="#D1D5DB", zeroline=True, zerolinecolor=BLACK, zerolinewidth=0.8,
            title_text="mn $", tickfont=dict(size=14, color=BLACK), title_font=dict(size=14, color=BLACK)),
        xaxis=dict(showgrid=False, tickfont=dict(size=13, color=BLACK)))
    return fig

def ysa_ceyreklik_grafik(df):
    if "Ceyrek" not in df.columns:
        return None
    qg = df.groupby("Ceyrek")[["Hisse","DIBS","Ozel_Sektor","Eurobond"]].sum().reset_index()
    qg["Toplam"] = qg[["Hisse","DIBS","Ozel_Sektor","Eurobond"]].sum(axis=1)
    fig = go.Figure()
    for kol, renk in YSA_RENK.items():
        isim = YSA_ISIM[kol]
        fig.add_trace(go.Bar(x=qg["Ceyrek"], y=qg[kol], name=isim,
            marker=dict(color=renk, line=dict(color="white", width=0.8)),
            text=[f"{v:+,.0f}" for v in qg[kol]], textposition="inside", textfont=dict(size=12, color="white"),
            hovertemplate="%{x}<br>" + isim + ": %{y:+,.0f} mn $<extra></extra>"))
    fig.update_layout(**_ysa_ortak_layout(), barmode="relative",
        title=dict(text="Çeyreklik Dağılım (mn $)", font=dict(size=17, color=BLACK), x=0.5),
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

def _ay_etiket(tarihler):
    ay_k = {1:"Oca",2:"Şub",3:"Mar",4:"Nis",5:"May",6:"Haz",
            7:"Tem",8:"Ağu",9:"Eyl",10:"Eki",11:"Kas",12:"Ara"}
    return [f"{ay_k[t.month]} {str(t.year)[2:]}" for t in tarihler]

def konut_kfe_grafik(df):
    a_kol, y_kol = "KFE_Turkiye_aylik", "KFE_Turkiye_yillik"
    if a_kol not in df.columns: return None
    tail = df.dropna(subset=[a_kol]).tail(25).copy()
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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def konut_satis_grafik(df):
    if "Satis_Toplam" not in df.columns: return None
    tail = df.dropna(subset=["Satis_Toplam"]).tail(25).copy()
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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def konut_ilk_ikinci_el_grafik(df):
    if "Satis_IlkEl" not in df.columns or "Satis_IkinciEl" not in df.columns: return None
    tail = df.dropna(subset=["Satis_IlkEl"]).tail(25).copy()
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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def konut_yeni_eski_grafik(df):
    kols = {"Yeni_Konut_FE_duzey": "Yeni Konut", "Eski_Konut_FE_duzey": "Eski Konut"}
    mevcut = {k: v for k, v in kols.items() if k in df.columns}
    if not mevcut: return None
    ilk_kol = list(mevcut.keys())[0]
    tail = df.dropna(subset=[ilk_kol]).tail(24).copy()
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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def konut_kira_grafik(df):
    kol = "Kira_Endeksi_duzey"
    if kol not in df.columns: return None
    tail = df.dropna(subset=[kol]).tail(24).copy()
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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def konut_birim_fiyat_grafik(df):
    kol = "Birim_Fiyat_TLm2"
    if kol not in df.columns: return None
    tail = df.dropna(subset=[kol]).tail(24).copy()
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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def konut_birim_kira_grafik(df):
    kol = "Birim_Kira_TLm2"
    if kol not in df.columns: return None
    tail = df.dropna(subset=[kol]).tail(24).copy()
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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def konut_amortisman_grafik(df):
    kol = "Amortisman_Ay"
    if kol not in df.columns: return None
    tail = df.dropna(subset=[kol]).tail(24).copy()
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
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=12, color=BLACK), showgrid=False)
    return fig

def konut_kredi_faiz_grafik(df):
    kol = "Konut_Kredi_Faiz"
    if kol not in df.columns: return None
    tail = df.dropna(subset=[kol]).tail(104).copy()
    if tail.empty: return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=tail["Tarih"], y=tail[kol], mode="lines", line=dict(color=RED_500, width=2.5),
                              hovertemplate="%{x|%d.%m.%Y}<br>%{y:.2f}%<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text="Konut Kredisi Faizi (%)", font=dict(size=17, color=BLACK), x=0.5),
                      showlegend=False, yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK), title_text="%"),
                      xaxis=dict(showgrid=False, tickfont=dict(size=13, color=BLACK)))
    return fig

def konut_ruhsat_grafik(df, kol, baslik):
    if kol not in df.columns: return None
    tail = df.dropna(subset=[kol]).copy()
    tail = tail[tail[kol] > 0].tail(13)
    if tail.empty: return None
    x = _ay_etiket(tail["Tarih"])
    vals = tail[kol].values
    fig = go.Figure()
    fig.add_trace(go.Bar(x=x, y=vals, marker_color=BLUE_500, text=[f"{v:,.0f}" for v in vals],
                         textposition="outside", textfont=dict(size=13, color=BLACK),
                         hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"))
    fig.update_layout(**_konut_ortak(), title=dict(text=baslik, font=dict(size=17, color=BLACK), x=0.5),
                      showlegend=False, bargap=0.3,
                      yaxis=dict(gridcolor="#D1D5DB", tickfont=dict(size=14, color=BLACK)),
                      xaxis=dict(showgrid=False, tickfont=dict(size=12, color=BLACK)))
    fig.update_xaxes(tickangle=-45)
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
    last_n = min(104, len(df))
    tail = df.tail(last_n)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tail["Tarih"], y=tail["KT1"]/1e6, marker=dict(color=BLUE_500), name="Haftalık"))
    if "KT1_MA" in tail.columns:
        fig.add_trace(go.Scatter(x=tail["Tarih"], y=tail["KT1_MA"]/1e6, mode="lines",
                                  line=dict(color=NAVY_800, width=2.5), name=f"{KK_MA}H Ort."))
    fig.update_layout(**_kk_ortak(),
        title=dict(text=f"Toplam Kartlı Harcama (Son {last_n} Haftalık) — mr ₺", font=dict(size=17, color=BLACK), x=0.5),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
                    font=dict(size=13, color=BLACK), bgcolor="rgba(255,255,255,0.95)", bordercolor="#D1D5DB", borderwidth=1),
        yaxis=dict(gridcolor=GRID, zeroline=False, title_text="mr ₺",
                   tickfont=dict(size=13, color=BLACK), title_font=dict(size=14, color=BLACK)),
        xaxis=dict(showgrid=False, tickfont=dict(size=12, color=BLACK)))
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
    dfc = df[["Tarih", "Ceyrek"] + cols_needed].copy()
    dfc["Diger"] = dfc["KT1"] - dfc[KK_ANA_SEKTORLER].sum(axis=1)
    q = dfc.groupby("Ceyrek")[KK_ANA_SEKTORLER + ["Diger"]].sum().reset_index().tail(12)
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
        title=dict(text="Çeyreklik Harcama Dağılımı (Son 12 Çeyrek) — mr ₺", font=dict(size=17, color=BLACK), x=0.5),
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
    q = df.groupby("Ceyrek")["KA1"].sum().reset_index().tail(12)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=q["Ceyrek"], y=q["KA1"]/1e9, marker_color=BLUE_500))
    layout = _kk_ortak()
    layout.update(height=350)
    fig.update_layout(**layout,
        title=dict(text="Çeyreklik Toplam İşlem Adedi (Son 12 Çeyrek) — mr adet", font=dict(size=17, color=BLACK), x=0.5),
        showlegend=False)
    fig.update_xaxes(tickangle=-45, tickfont=dict(size=13, color=BLACK))
    fig.update_yaxes(gridcolor=GRID, tickfont=dict(size=13, color=BLACK),
                     title_text="mr adet", title_font=dict(size=14, color=BLACK))
    return fig

def kk_ceyreklik_tablo_html(df):
    """05 — Son 8 çeyrek harcama + işlem tablosu."""
    if "KT1" not in df.columns or "KA1" not in df.columns: return ""
    q = df.groupby("Ceyrek")[["KT1", "KA1"]].sum().reset_index().tail(8)
    html = f"""<table style="width:60%; border-collapse:collapse; font-family:Arial; font-size:14px; margin-top:8px; border:1px solid #CBD5E1;">
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
    st.markdown("""
    <div style="text-align:center; padding:10px 0 15px 0;">
        <span style="font-size:24px; font-weight:800;
        background:linear-gradient(135deg,#A855F7,#22D3EE);
        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
        Sai Makro</span>
        <br><span style="color:#94A3B8; font-size:11px;">Makro Ekonomik Dashboard</span>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<div class="modul-baslik">MODÜL SEÇ</div>', unsafe_allow_html=True)
    modul = st.selectbox("Modül", [
        "📈 TÜFE",
        "🏭 ÜFE",
        "🌍 Yabancı Sermaye Hareketleri",
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
        st.code("python guncelle_tufe.py", language="bash")
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
        st.code("python guncelle_ufe.py", language="bash")
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
        st.code("python guncelle_ysa.py", language="bash")
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

elif "Konut" in modul:
    df_konut = konut_yukle(csv_cache_key("konut.csv"))
    if df_konut is None:
        st.warning("⚠️ Konut verisi bulunamadı!")
        st.code("python guncelle_konut.py", language="bash")
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
        st.code("python guncelle_kredi_karti.py", language="bash")
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
                st.markdown("**Son 8 Çeyrek — Harcama & İşlem Adedi**")
                st.markdown(kk_ceyreklik_tablo_html(df_kk), unsafe_allow_html=True)
                st.caption(
                    f"Veriler TCMB EVDS kaynaklıdır. Veri frekansı haftalık. "
                    f"(*) İnternet, Mektup/Telefon ve Gümrük serileri toplama dahil değildir."
                )
