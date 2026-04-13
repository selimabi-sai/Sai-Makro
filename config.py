# -*- coding: utf-8 -*-
"""
SAI MAKRO — Ortak Ayarlar ve Seri Tanımları
=============================================
Tüm guncelle_*.py ve dashboard bu dosyayı import eder.
"""

import os
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════
# YOLLAR
# ═══════════════════════════════════════════════════════════
try:
    BASE_DIR = Path(__file__).resolve().parent
except Exception:
    BASE_DIR = Path.cwd()

DATA_DIR = BASE_DIR / "makro_data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# EVDS
# ═══════════════════════════════════════════════════════════
EVDS_API_KEY = "C7Lm9VKgiL"

def evds_baglan():
    from evds import evdsAPI
    return evdsAPI(EVDS_API_KEY)

def evds_cek(seri_kodlari, baslangic, bitis=None, formulas=None, frequency=None):
    """
    EVDS'den veri çek.
    formulas: None=düzey, 1=aylık % değişim, 3=yıllık % değişim
    frequency: None=varsayılan, 5=aylık, 6=çeyreklik, 3=haftalık
    """
    import pandas as pd

    if bitis is None:
        bitis = datetime.now().strftime("%d-%m-%Y")
    evds = evds_baglan()
    kwargs = {
        "startdate": baslangic,
        "enddate": bitis,
    }
    if formulas is not None:
        kwargs["formulas"] = formulas
    if frequency is not None:
        kwargs["frequency"] = frequency
    df = evds.get_data(seri_kodlari, **kwargs)
    if "Tarih" in df.columns:
        df["Tarih"] = pd.to_datetime(df["Tarih"], format="mixed", dayfirst=True, errors="coerce")
        df = df.sort_values("Tarih").reset_index(drop=True)
    if "UNIXTIME" in df.columns:
        df = df.drop(columns=["UNIXTIME"])
    return df

# ═══════════════════════════════════════════════════════════
# TÜFE SERİLERİ — 17 kalem
# ═══════════════════════════════════════════════════════════
TUFE_SERILER = {
    # --- 14 ana kalem ---
    "TP.TUKFIY2025.GENEL": "TÜFE Genel",
    "TP.TUKFIY2025.01":    "Gıda ve Alkolsüz İçecekler",
    "TP.TUKFIY2025.02":    "Alkollü İçecekler, Tütün",
    "TP.TUKFIY2025.03":    "Giyim ve Ayakkabı",
    "TP.TUKFIY2025.04":    "Konut, Su, Elektrik, Gaz",
    "TP.TUKFIY2025.05":    "Mobilya, Ev Ekipmanları",
    "TP.TUKFIY2025.06":    "Sağlık",
    "TP.TUKFIY2025.07":    "Ulaştırma",
    "TP.TUKFIY2025.08":    "Bilgi ve İletişim",
    "TP.TUKFIY2025.09":    "Eğlence, Spor, Kültür",
    "TP.TUKFIY2025.10":    "Eğitim",
    "TP.TUKFIY2025.11":    "Lokanta ve Konaklama",
    "TP.TUKFIY2025.12":    "Sigorta ve Finansal Hizmetler",
    "TP.TUKFIY2025.13":    "Kişisel Bakım, Çeşitli",
    # --- 3 çekirdek ---
    "TP.FE25.OKTG03":      "Çekirdek B",
    "TP.FE25.OKTG04":      "Çekirdek C",
    "TP.FE25.OKTG05":      "Çekirdek D",
}

TUFE_BASLANGIC = "01-01-2012"

# ═══════════════════════════════════════════════════════════
# ÜFE SERİLERİ — 15 kalem
# ═══════════════════════════════════════════════════════════
UFE_SERILER = {
    # --- 5 ana sektör ---
    "TP.TUFE1YI.T1":   "ÜFE Genel",
    "TP.TUFE1YI.T2":   "Madencilik ve Taşocakçılığı",
    "TP.TUFE1YI.T15":  "İmalat",
    "TP.TUFE1YI.T118": "Elektrik, Gaz, Buhar",
    "TP.TUFE1YI.T123": "Su Temini, Atık Yönetimi",
    # --- 10 imalat alt sektörü ---
    "TP.TUFE1YI.T16":  "Gıda Ürünleri",
    "TP.TUFE1YI.T26":  "İçecekler",
    "TP.TUFE1YI.T30":  "Tekstil",
    "TP.TUFE1YI.T35":  "Giyim Eşyası",
    "TP.TUFE1YI.T38":  "Deri",
    "TP.TUFE1YI.T44":  "Kağıt",
    "TP.TUFE1YI.T52":  "Kimyasallar",
    "TP.TUFE1YI.T73":  "Ana Metaller",
    "TP.TUFE1YI.T99":  "Makine ve Ekipmanlar",
    "TP.TUFE1YI.T112": "Mobilya",
}

UFE_BASLANGIC = "01-01-2012"

# ═══════════════════════════════════════════════════════════
# YABANCI SERMAYE AKIMI SERİLERİ
# ═══════════════════════════════════════════════════════════
YSA_SERILER = {
    "TP.MKNETHAR.M7":  "Hisse",
    "TP.MKNETHAR.M8":  "DIBS",
    "TP.MKNETHAR.M12": "Ozel_Sektor",
    "TP.MKNETHAR.M22": "Eurobond",
}

YSA_BASLANGIC = "01-09-2020"

YSA_MENU = [
    "Hisse Senedi",
    "DİBS",
    "Özel Sektör",
    "Eurobond",
    "Toplam Net Akım",
    "Kümülatif",
    "Çeyreklik Dağılım",
]

# ═══════════════════════════════════════════════════════════
# KONUT SERİLERİ
# ═══════════════════════════════════════════════════════════
# Fiyat endeksleri — formulas ile aylık/yıllık % alınacak
KONUT_FE_SERILER = {
    "TP.KFE.TR":       "KFE_Turkiye",
    "TP.YKFE.TR":      "Yeni_Konut_FE",
    "TP.YOKFEND.TR":   "Eski_Konut_FE",
    "TP.YKKE.TR":      "Kira_Endeksi",
}

# Düzey veriler — formulas kullanılmayacak
KONUT_DUZEY_SERILER = {
    "TP.BIRIMFIYAT.TR":       "Birim_Fiyat_TLm2",
    "TP.BK.TR":               "Birim_Kira_TLm2",
    "TP.AKONUTSAT1.TOPLAM":   "Satis_Toplam",
    "TP.AKONUTSAT2.TOPLAM":   "Satis_Ipotekli",
    "TP.AKONUTSAT3.TOPLAM":   "Satis_IlkEl",
    "TP.AKONUTSAT4.TOPLAM":   "Satis_IkinciEl",
}

# Konut kredisi faizi — haftalık akım bazlı
KONUT_KREDI_SERILER = {
    "TP.KTF12": "Konut_Kredi_Faiz",
}

# Yapı ruhsatları — Apartman (Toplam) + Ev (Toplam)
KONUT_RUHSAT_SERILER = {
    "TP.IN.RH2.APT.TOP.A":  "Ruhsat_Apt_Yapi",
    "TP.IN.RH2.APT.TOP.B":  "Ruhsat_Apt_Yuzolcum",
    "TP.IN.RH2.APT.TOP.D":  "Ruhsat_Apt_Daire",
    "TP.IN.RH2.EV.TOP.A":   "Ruhsat_Ev_Yapi",
    "TP.IN.RH2.EV.TOP.B":   "Ruhsat_Ev_Yuzolcum",
    "TP.IN.RH2.EV.TOP.D":   "Ruhsat_Ev_Daire",
}

KONUT_BASLANGIC = "01-01-2013"

KONUT_MENU = [
    "KFE Türkiye",
    "Konut Satış Adetleri",
    "Yeni vs Eski Konut FE",
    "Kira Endeksi",
    "Birim Fiyat (TL/m²)",
    "Birim Kira (TL/m²)",
    "Amortisman (Ay)",
    "Konut Kredisi Faizi (%)",
    "İnşaat Maliyet Endeksi",
    "İnşaat Üretim Endeksi",
    "İnşaat Güven Endeksi",
    "Yapı Ruhsatı — Yapı Sayısı",
    "Yapı Ruhsatı — Yüzölçüm",
    "Yapı Ruhsatı — Daire Sayısı",
]

# ═══════════════════════════════════════════════════════════
# KREDİ KARTI SERİLERİ
# ═══════════════════════════════════════════════════════════
KK_BASLANGIC = "01-01-2015"
KK_MA = 13          # 13 hafta hareketli ortalama
KK_YOY = 52         # YoY = 52 hafta öncesine göre

# EVDS seri suffix'leri
KK_KT_SUFFIXES = [f"KT{i}" for i in range(1, 27)] + ["KT49", "KT50", "KT51", "KT52"]
KK_KA_SUFFIXES = [f"KA{i}" for i in range(1, 27)] + ["KA49", "KA50", "KA51", "KA52"]

# Sektör isimleri
KK_SEKTOR_MAP = {
    "KT1": "TOPLAM", "KT2": "Araba Kiralama", "KT3": "Araç Satış/Servis",
    "KT4": "Benzin ve Yakıt", "KT5": "Çeşitli Gıda", "KT6": "Doğrudan Pazarlama",
    "KT7": "Eğitim/Kırtasiye", "KT8": "Elektronik/Bilgisayar", "KT9": "Giyim ve Aksesuar",
    "KT10": "Havayolları", "KT11": "Hizmet Sektörleri", "KT12": "Konaklama",
    "KT13": "Kulüp/Dernek", "KT14": "Kumarhane/İçkili", "KT15": "Kuyumcular",
    "KT16": "Market ve AVM", "KT17": "Mobilya/Dekorasyon", "KT18": "Müteahhit İşleri",
    "KT19": "Sağlık/Kozmetik", "KT20": "Seyahat/Taşımacılık", "KT21": "Sigorta",
    "KT22": "Telekomünikasyon", "KT23": "Yapı Malzemeleri", "KT24": "Yemek",
    "KT25": "Kamu/Vergi", "KT26": "Bireysel Emeklilik",
    "KT49": "Diğer", "KT50": "İnternet Alışverişi*", "KT51": "Mektup/Telefon*",
    "KT52": "Gümrük Vergisi*",
}

# Raporlarda kullanılan gerçek sektörler (toplam ve * hariçler hariç)
KK_GERCEK = [f"KT{i}" for i in range(2, 27)]

# Çeyreklik stacked bar için ana sektörler
KK_ANA_SEKTORLER = ["KT16", "KT5", "KT9", "KT24"]

# Dashboard sidebar menüsü
KK_MENU = [
    "Genel Görünüm",
    "Sektörel Dağılım (Tablo)",
    "Harcama vs 13H Ortalaması",
    "İşlem Adedi Analizi",
    "Çeyreklik Dağılım",
]
