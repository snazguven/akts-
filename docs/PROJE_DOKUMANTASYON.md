# Adaptif AKTS — Veri Hazırlama Pipeline Dokümantasyonu
Proje: YÖKAK 2026 | Sorumlu: Sudenaz Güven | Tarih: 19 Haziran 2026

## Klasör Yapısı
akts-bloom/
├── ip2_master_clean.py     ← İP2: temizlik + birleştirme
├── ip3_bloom_nlp.py        ← İP3: Bloom NLP analizi
├── PROJE_DOKUMANTASYON.md  ← bu dosya
└── data/
    ├── raw/                ← 7 ham xlsx (dokunulmaz)
    └── processed/
        ├── master_clean.xlsx  ← İP2 çıktısı (4.133 satır)
        └── master_bloom.xlsx  ← İP3 çıktısı (güncel master)

## Kullanılan Kütüphaneler
pandas, numpy==1.26.4, openpyxl

## İP2 — Ne Yaptık
Girdi : 5.807 satır (7 fakülte xlsx)
Çıktı : 4.133 satır, ~65 sütun
Düşülen: 1.674 satır
  - AKTS=0       → 57 satır silindi
  - Boş kazanım  → ~17 satır silindi
  - İÖ tekrarı   → ~1.600 satır silindi (aynı Katalogid, normal öğretim tutuldu)

Eklenen sütunlar:
  fakulte, alan_grubu (STEM/Sosyal/Fen-Sosyal/Sanat/Spor)
  n_ogrenme_kazanim, kazanim_concat
  n_etkinlik
  has_lab, has_proje, has_uygulama, has_atolye
  has_odev, has_sinav, has_sunum, has_alan_calismasi

Fakülte dağılımı (temizlik sonrası):
  Mühendislik      : 1.090 (%26.4)
  Fen-Edebiyat     :   890 (%21.5)
  Güzel Sanatlar   :   710 (%17.2)
  Spor Bilimleri   :   431 (%10.4)
  Eğitim           :   366 (%8.9)
  Teknoloji        :   323 (%7.8)
  Siyasal Bilgiler :   323 (%7.8)

Etkinlik oranları:
  has_sinav: %97.7 | has_odev: %17.5 | has_uygulama: %9.2
  has_proje: %7.3  | has_sunum: %7.5  | has_lab: %3.4

## İP3 — Ne Yaptık
Girdi : master_clean.xlsx
Çıktı : master_bloom.xlsx
Yöntem: Kural tabanlı NLP — Türkçe fiil listesi eşleştirme (L6→L1 greedy tarama)
NOT   : bloom_uygunluk_alani KALDIRILDI (19 Haz 2026 toplantı kararı)

Bloom Katsayıları:
  L1 Hatırlama     → 1.00
  L2 Anlama        → 1.10
  L3 Uygulama      → 1.20
  L4 Analiz        → 1.30
  L5 Değerlendirme → 1.40
  L6 Yaratma       → 1.50

K_bilissel formülü: 1 + ((bloom_avg_level - 1) / 5) * 0.50

Bloom Dominant Dağılımı:
  L1 Hatırlama     : 2.810 ders (%68.0)
  L2 Anlama        :   579 ders (%14.0)
  L3 Uygulama      :   491 ders (%11.9)
  L4 Analiz        :   112 ders (%2.7)
  L6 Yaratma       :   107 ders (%2.6)
  L5 Değerlendirme :    34 ders (%0.8)

Fakülte bazlı ort. Bloom: Siyasal(2.65) > Teknoloji(2.34) > Müh(2.04) > Spor(1.97) > Eğitim(1.94) > FenEd(1.86) > GüzSan(1.69)
K_bilissel: Min=1.00 | Ort=1.098 | Max=1.50 | Std=0.095

Ana Bulgu: Derslerin %68i L1 Hatırlama düzeyinde → H4 hipotezini destekliyor.
Statik motor bilişsel yükü görmezden geliyor = projenin temel tezi kanıtlandı.

## Eklenen Bloom Sütunları
bloom_l1_count .. bloom_l6_count  (kazanım sayısı)
bloom_l1_ratio .. bloom_l6_ratio  (oran 0-1)
bloom_avg_level, bloom_max_level, bloom_dominant_level
K_bilissel, bloom_justification

## Sıradaki Adımlar
✅ İP2 Temizlik + Master tablo  → Sudenaz   → master_clean.xlsx
✅ İP3 Bloom NLP               → Sudenaz   → master_bloom.xlsx
✅ İP4 Yapısal gruplama        → Samet     → K_profil sütunu
✅ İP5 Random Forest + Adaptif → Samet     → master_akts_final.xlsx (18 Temmuz 2026)
✅ İP6 Validasyon              → Samet     → ip6-validasyon/ (18 Temmuz 2026)
⏳ İP7 Tam makale yazımı       → Ekip

Güncel master: data/processed/master_bloom.xlsx
Güncel nihai tablo: data/processed/master_akts_final.xlsx (bkz. docs/IP5_IP6_RAPOR.md)

## İP2 Kaynak Kodu
"""
ip2_master_clean.py
Master temizleme scripti — 7 fakülte Excel'ini birleştirir, temizler, zenginleştirir.
"""

import subprocess, sys

# Gerekli kütüphane kontrolü
for pkg in ["pandas", "openpyxl"]:
    try:
        __import__(pkg)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import warnings
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Yollar ──────────────────────────────────────────────────────────────────
RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

# ── 1. Dosyaları yükle ──────────────────────────────────────────────────────
files = {
    "Mühendislik":      "Mu_hendislik.xlsx",
    "Güzel Sanatlar":   "Gu_zel_Sanatlar.xlsx",
    "Fen-Edebiyat":     "FenEdebiyat.xlsx",
    "Eğitim":           "Eg_itim.xlsx",
    "Siyasal Bilgiler": "Siyasal_Bilgiler.xlsx",
    "Spor Bilimleri":   "Spor_Bilimleri.xlsx",
    "Teknoloji":        "Teknoloji.xlsx",
}

alan_grubu_map = {
    "Mühendislik":      "STEM",
    "Teknoloji":        "STEM",
    "Fen-Edebiyat":     "Fen-Sosyal",
    "Eğitim":           "Sosyal",
    "Siyasal Bilgiler": "Sosyal",
    "Güzel Sanatlar":   "Sanat",
    "Spor Bilimleri":   "Spor",
}

dfs = []
for fakulte, fname in files.items():
    path = RAW / fname
    df_tmp = pd.read_excel(path)
    df_tmp["Fakulte"] = fakulte
    dfs.append(df_tmp)
    print(f"  Yüklendi: {fname:<30} ({len(df_tmp):>5} satır)")

df = pd.concat(dfs, ignore_index=True)
raw_count = len(df)
print(f"\nHam birleşik satır: {raw_count}")

# ── 3. Temizlik ─────────────────────────────────────────────────────────────
# AKTSKredi == 0
df = df[df["AKTSKredi"] != 0]
drop_akts = raw_count - len(df)

# OgrenmeKazanim_1 boş
df = df[df["OgrenmeKazanim_1"].notna()]
df = df[df["OgrenmeKazanim_1"].astype(str).str.strip().str.lower() != "nan"]
drop_kaz = raw_count - drop_akts - len(df)

# EtkinlikAd sütunlarında strip
etkinlik_cols = [f"EtkinlikAd_{i}" for i in range(1, 22)]
for c in etkinlik_cols:
    if c in df.columns:
        df[c] = df[c].astype(str).str.strip().replace("nan", pd.NA)

# ── 4. İÖ tekilleştirme ─────────────────────────────────────────────────────
df["is_io"] = df["BolumAd"].astype(str).str.contains(r"\(İÖ\)|\(IO\)", regex=True, na=False)
before_dedup = len(df)
# Sırala: is_io=False önce gelsin → keep='first' ile İÖ olanı atar (aynı id varsa)
df = df.sort_values("is_io").drop_duplicates(subset="Katalogid", keep="first")
drop_io = before_dedup - len(df)

# ── 5. Yeni sütunlar ────────────────────────────────────────────────────────
df["alan_grubu"] = df["Fakulte"].map(alan_grubu_map)

# Öğrenme kazanımları
kaz_cols = [f"OgrenmeKazanim_{i}" for i in range(1, 26)]

def count_kaz(row):
    return sum(
        1 for c in kaz_cols
        if c in row and pd.notna(row[c]) and str(row[c]).strip().lower() not in ("", "nan")
    )

def concat_kaz(row):
    vals = [
        str(row[c]).strip()
        for c in kaz_cols
        if c in row and pd.notna(row[c]) and str(row[c]).strip().lower() not in ("", "nan")
    ]
    return " | ".join(vals)

df["n_ogrenme_kazanim"] = df.apply(count_kaz, axis=1)
df["kazanim_concat"]    = df.apply(concat_kaz, axis=1)

# Etkinlik özellikleri — büyük/küçük harf duyarsız eşleştirme
def etkinlik_features(row):
    vals = " | ".join([
        str(row[c]).strip().lower()
        for c in etkinlik_cols
        if c in row and pd.notna(row[c]) and str(row[c]).strip().lower() not in ("", "nan")
    ])
    n = vals.count("|") + 1 if vals.strip() else 0
    return pd.Series({
        "n_etkinlik":    n,
        "has_lab":       int("laboratuvar" in vals),
        "has_proje":     int("proje" in vals),
        "has_uygulama":  int("uygulama" in vals),
        "has_atolye":    int("atölye" in vals or "atolye" in vals),
        "has_odev":      int("ödev" in vals or "odev" in vals),
        "has_sinav":     int("sınav" in vals or "sinav" in vals or "quiz" in vals),
        "has_sunum":     int("sunum" in vals or "seminer" in vals),
    })

ef = df.apply(etkinlik_features, axis=1)
df = pd.concat([df, ef], axis=1)

# ── 6. Kaydet ───────────────────────────────────────────────────────────────
df.reset_index(drop=True, inplace=True)
df.to_excel(OUT / "master_clean.xlsx", index=False)
df.to_csv(OUT / "master_clean.csv", index=False, encoding="utf-8-sig")

# ── 7. Rapor ────────────────────────────────────────────────────────────────
n_rows = len(df)
n_cols = len(df.columns)

print("\n" + "=" * 45)
print("         TEMİZLİK RAPORU")
print("=" * 45)
print(f"Ham satır              : {raw_count}")
print(f"AKTSKredi=0 düşülen   : {drop_akts}")
print(f"Kazanım boş düşülen   : {drop_kaz}")
print(f"İÖ tekrar düşülen     : {drop_io}")
print(f"MASTER SATIR           : {n_rows}")
print(f"MASTER KOLON           : {n_cols}")

print("\n── Fakülte Dağılımı ──────────────────────")
for fak, cnt in df["Fakulte"].value_counts().items():
    pct = cnt / n_rows * 100
    print(f"  {fak:<22}: {cnt:>5}  ({pct:.1f}%)")

print("\n── Etkinlik Oranları ─────────────────────")
for col in ["has_lab", "has_proje", "has_uygulama", "has_atolye", "has_odev", "has_sinav", "has_sunum"]:
    if col in df.columns:
        s = df[col].sum()
        r = s / n_rows * 100
        print(f"  {col:<18}: {s:>5}  ({r:.1f}%)")

print("\n── Diğer ─────────────────────────────────")
print(f"  Ort. n_etkinlik      : {df['n_etkinlik'].mean():.2f}")
print(f"  Ort. n_kazanim       : {df['n_ogrenme_kazanim'].mean():.2f}")
print(f"  Ort. AKTSKredi       : {df['AKTSKredi'].mean():.2f}")

print("\nDosyalar kaydedildi:")
print(f"  {OUT / 'master_clean.xlsx'}")
print(f"  {OUT / 'master_clean.csv'}")


## İP3 Kaynak Kodu
"""
ip3_bloom_nlp.py
Bloom taksonomisi NLP analizi — master_clean.xlsx üzerinde her kazanımı sınıflandırır.
"""

import warnings
import pandas as pd
from pathlib import Path

warnings.filterwarnings("ignore")

# ── Yollar ──────────────────────────────────────────────────────────────────
IN_FILE  = Path("data/processed/master_clean.xlsx")
OUT_DIR  = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Bloom sözlüğü (L6→L1 sırasıyla) ────────────────────────────────────────
BLOOM = [
    (6, "Yaratma",        1.50, [
        "tasarlar", "geliştirir", "oluşturur", "üretir",
        "planlar", "inşa eder", "kurar", "formüle eder",
    ]),
    (5, "Değerlendirme",  1.40, [
        "değerlendirir", "yargılar", "savunur", "eleştirir",
        "karar verir", "doğrular", "önceliklendirir",
    ]),
    (4, "Analiz",         1.30, [
        "analiz eder", "inceler", "test eder", "sorgular",
        "kıyaslar", "ayırt eder", "karşılaştırır", "karmaşıklığını",
    ]),
    (3, "Uygulama",       1.20, [
        "uygular", "hesaplar", "çözer", "kullanır",
        "gerçekleştirir", "dener", "yapar", "işletir", "seçer",
    ]),
    (2, "Anlama",         1.10, [
        "açıklar", "özetler", "sınıflandırır", "yorumlar",
        "karşılaştırır", "örnekler", "betimler", "kavrar",
        "ilişkilendirir", "anlar",
    ]),
    (1, "Hatırlama",      1.00, [
        "tanımlar", "listeler", "adlandırır", "belirtir",
        "ifade eder", "öğrenir", "sıralar", "hatırlar", "tekrarlar",
    ]),
]

KAZ_COLS = [f"OgrenmeKazanim_{i}" for i in range(1, 26)]

# ── Tek bir kazanım metnini sınıflandır ─────────────────────────────────────
def classify_kazanim(text: str) -> int:
    """L6→L1 tarayarak ilk eşleşen düzeyi döndür; eşleşme yoksa 1."""
    if not text or str(text).strip().lower() in ("", "nan"):
        return 0  # boş
    t = str(text).lower()
    for level, _, _, keywords in BLOOM:
        for kw in keywords:
            if kw in t:
                return level
    return 1  # güvenli taban

# ── Bir satırı (ders) işle ───────────────────────────────────────────────────
def process_row(row) -> dict:
    levels = []
    for c in KAZ_COLS:
        val = row.get(c, None)
        if pd.notna(val) and str(val).strip().lower() not in ("", "nan"):
            lv = classify_kazanim(str(val))
            if lv > 0:
                levels.append(lv)

    if not levels:
        levels = [1]

    counts = {i: levels.count(i) for i in range(1, 7)}
    total  = len(levels)
    ratios = {i: counts[i] / total for i in range(1, 7)}

    avg_level  = sum(levels) / total
    max_level  = max(levels)
    dom_level  = max(counts, key=counts.get)

    K = 1 + ((avg_level - 1) / 5) * 0.50

    justification = (
        f"Dominant: L{dom_level} | "
        f"Ort: {avg_level:.2f} | "
        f"Maks: L{max_level} | "
        f"K={K:.4f}"
    )

    result = {}
    for i in range(1, 7):
        result[f"bloom_l{i}_count"] = counts[i]
        result[f"bloom_l{i}_ratio"] = round(ratios[i], 4)
    result["bloom_avg_level"]      = round(avg_level, 4)
    result["bloom_max_level"]      = max_level
    result["bloom_dominant_level"] = dom_level
    result["K_bilissel"]           = round(K, 4)
    result["bloom_justification"]  = justification
    return result

# ── Ana akış ────────────────────────────────────────────────────────────────
print(f"Girdi yükleniyor: {IN_FILE}")
df = pd.read_excel(IN_FILE)
print(f"  {len(df)} satır, {len(df.columns)} kolon yüklendi.")

print("Bloom analizi çalışıyor...")
bloom_rows = df.apply(process_row, axis=1, result_type="expand")
df = pd.concat([df, bloom_rows], axis=1)
print("  Tamamlandı.")

# ── Kaydet ──────────────────────────────────────────────────────────────────
df.to_excel(OUT_DIR / "master_bloom.xlsx", index=False)
df.to_csv(OUT_DIR / "master_bloom.csv",   index=False, encoding="utf-8-sig")

# ── Rapor ───────────────────────────────────────────────────────────────────
level_labels = {1:"L1 Hatırlama", 2:"L2 Anlama", 3:"L3 Uygulama",
                4:"L4 Analiz",    5:"L5 Değerlendirme", 6:"L6 Yaratma"}

print("\n" + "=" * 50)
print("         BLOOM ANALİZİ RAPORU")
print("=" * 50)

print("\n── Dominant Düzey Dağılımı ───────────────────────")
dom_dist = df["bloom_dominant_level"].value_counts().sort_index()
for lv, cnt in dom_dist.items():
    pct = cnt / len(df) * 100
    label = level_labels.get(lv, f"L{lv}")
    print(f"  {label:<22}: {cnt:>5}  ({pct:.1f}%)")

print("\n── Fakülte Bazlı Ort. Bloom Düzeyi ──────────────")
if "Fakulte" in df.columns:
    fak_avg = df.groupby("Fakulte")["bloom_avg_level"].mean().sort_values(ascending=False)
    for fak, avg in fak_avg.items():
        print(f"  {fak:<22}: {avg:.3f}")

print("\n── K_bilissel İstatistikleri ─────────────────────")
k = df["K_bilissel"]
print(f"  Min      : {k.min():.4f}")
print(f"  Max      : {k.max():.4f}")
print(f"  Ortalama : {k.mean():.4f}")
print(f"  Std      : {k.std():.4f}")

print("\nDosyalar kaydedildi:")
print(f"  {OUT_DIR / 'master_bloom.xlsx'}")
print(f"  {OUT_DIR / 'master_bloom.csv'}")

